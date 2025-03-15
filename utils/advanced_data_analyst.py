import os
import pandas as pd
import numpy as np
import pickle
import base64
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import sqlalchemy
from sqlalchemy import create_engine, text
import psycopg2
from psycopg2 import sql

# LangChain imports
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_experimental.tools import PythonAstREPLTool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import CSVLoader
from langchain.schema import Document

# Pinecone API
from pinecone import Pinecone, ServerlessSpec

# Basic settings
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

# AWS RDS Configuration
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')
DB_CONNECTION_STRING = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

class AdvancedDataAnalyst:
    
    def __init__(self):
        self.clients_cache = {}
        self.embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        
        # Initialize database connection using SQLAlchemy instead of psycopg2 directly
        try:
            self.db_engine = create_engine(
                f"postgresql://postgres:HokoAI2024@db-hokoainalytics.cviwa0kqeims.us-east-1.rds.amazonaws.com:5432/postgres"
            )
        except Exception as e:
            print(f"Erro ao conectar ao RDS: {e}")
            raise e
            
        # Mapeamentos de colunas de plataforma
        self.platform_columns = {
            'google_analytics': [
                'traffic_direct', 'search_volume', 'impressions', 
                'traffic_organic_search', 'traffic_organic_social', 'data'
            ],
            'facebook': [
                'page_impressions', 'page_impressions_unique', 
                'page_follows', 'data'
            ],
            'instagram': [
                'reach', 'views', 'followers', 'data'
            ]
        }
        
        # Prompt de sistema padrão para a função de analista
        self.system_prompt = """
        Você é um analista de dados avançado especializado em análise de métricas de mídias sociais.
        
        Suas capacidades incluem:
        1. Análise descritiva: Resumir dados históricos, identificar padrões e calcular métricas-chave.
        2. Análise diagnóstica: Determinar por que certas tendências ocorreram, encontrando correlações e relações causais.
        3. Análise preditiva: Usar dados históricos para prever métricas e tendências futuras.
        4. Análise prescritiva: Recomendar ações específicas para melhorar o desempenho com base em insights de dados.
        
        Sempre siga estas diretrizes:
        - Comece entendendo a estrutura dos dados e as métricas-chave
        - Forneça contexto para qualquer cálculo
        - Inclua tanto insights de alto nível quanto observações detalhadas
        - Ao fazer previsões, explique seu raciocínio e nível de confiança
        - Priorize recomendações acionáveis que sejam específicas e realistas
        - Compare sempre o desempenho atual com referências históricas
        - Destaque padrões incomuns ou anomalias que exijam atenção
        
        Você tem acesso a Python e pandas para realizar sua análise.
        NÃO crie visualizações ou gráficos. Concentre-se exclusivamente em análises numéricas e textuais.
        
        IMPORTANTE: Todas as suas respostas DEVEM ser em português do Brasil.
        """
        
    def _get_client_id_hash(self, client_id: str) -> str:
        import hashlib
        return hashlib.md5(str(client_id).encode()).hexdigest()

    def _get_client_data_from_db(self, client_id: str, platform: str, 
                               start_date: Optional[str] = None, 
                               end_date: Optional[str] = None) -> pd.DataFrame:
        # Get columns for the platform
        if platform not in self.platform_columns:
            raise ValueError(f"Platform '{platform}' not supported. Available platforms: {list(self.platform_columns.keys())}")
        
        columns = self.platform_columns[platform]
        columns_str = ", ".join(columns)
        
        # Crie a consulta SQL com parâmetros apropriados
        query = f"""
        SELECT {columns_str}
        FROM {platform}
        WHERE id_customer = :client_id
        """
        
        # Adicione filtros de data, se fornecidos
        params = {"client_id": client_id}
        if start_date:
            query += " AND data >= :start_date"
            params["start_date"] = start_date
        if end_date:
            query += " AND data <= :end_date"
            params["end_date"] = end_date
            
        # Execute the query and return as DataFrame
        try:
            with self.db_engine.connect() as connection:
                df = pd.read_sql(text(query), connection, params=params)
                
            if df.empty:
                raise ValueError(f"No data found for client {client_id} on platform {platform} for the specified date range")
                
            return df
        except Exception as e:
            raise Exception(f"Database error when fetching data for client {client_id}: {str(e)}")
    
    def _get_pinecone_index_name(self, client_id: str) -> str:
        return f"client-{self._get_client_id_hash(client_id)[:10]}"
    
    def _create_or_get_pinecone_index(self, client_id: str) -> str:
        index_name = self._get_pinecone_index_name(client_id)
        
        # Check if index exists
        if index_name not in [index.name for index in pc.list_indexes()]:
            # Create new index
            pc.create_index(
                name=index_name,
                dimension=1536,  # Dimension for OpenAI embeddings
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        
        return index_name

    def _create_or_load_vector_db(self, client_id: str, force_reload: bool = False) -> PineconeVectorStore:
        index_name = self._create_or_get_pinecone_index(client_id)
        
        # If force_reload is True, clear existing index
        if force_reload:
            index = pc.Index(index_name)
            index.delete(delete_all=True)
        
        # Check if index is empty (needs to be filled)
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        
        # Converta o client_id para string para usar como namespace
        client_id_str = str(client_id)
        
        # Just load the index since data already exists in vector database
        return PineconeVectorStore(
            index_name=index_name,
            embedding=self.embeddings,
            namespace=client_id_str
        )

    def _generate_data_summary(self, df: pd.DataFrame, client_id: str, platform: str) -> List[Document]:
        summary_texts = []
        
        # Basic dataframe info
        info_str = f"Dataset para cliente {client_id} na plataforma {platform} contém {len(df)} linhas e {len(df.columns)} colunas.\n"
        info_str += f"Colunas: {', '.join(df.columns)}\n"
        
        # Data types
        dtypes_str = "Tipos de dados das colunas:\n"
        for col, dtype in df.dtypes.items():
            dtypes_str += f"- {col}: {dtype}\n"
        
        # Basic statistics for numeric columns
        stats_str = "Estatísticas básicas para colunas numéricas:\n"
        numeric_cols = df.select_dtypes(include=['number']).columns
        if not numeric_cols.empty:
            stats = df[numeric_cols].describe().to_string()
            stats_str += stats + "\n"
        
        # Missing values
        missing_str = "Valores ausentes:\n"
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                missing_str += f"- {col}: {missing_count} valores ausentes ({missing_count/len(df)*100:.2f}%)\n"
        
        # Date range if there are date columns
        date_str = "Informações de datas:\n"
        date_cols = ['data']  # Based on your schema
        for col in date_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    min_date = df[col].min()
                    max_date = df[col].max()
                    date_str += f"- {col}: de {min_date} até {max_date}\n"
                except:
                    date_str += f"- {col}: não foi possível converter para datetime\n"
        
        # Create documents
        summary_texts.append(Document(page_content=info_str, metadata={"type": "dataset_info", "client_id": client_id, "platform": platform}))
        summary_texts.append(Document(page_content=dtypes_str, metadata={"type": "data_types", "client_id": client_id, "platform": platform}))
        summary_texts.append(Document(page_content=stats_str, metadata={"type": "statistics", "client_id": client_id, "platform": platform}))
        summary_texts.append(Document(page_content=missing_str, metadata={"type": "missing_values", "client_id": client_id, "platform": platform}))
        summary_texts.append(Document(page_content=date_str, metadata={"type": "date_info", "client_id": client_id, "platform": platform}))
        
        return summary_texts

    def _store_analysis_in_vectordb(self, client_id: str, query: str, result: str, platform: str) -> None:
        from datetime import datetime
        
        # Prepare document
        timestamp = datetime.now().isoformat()
        document = Document(
            page_content=f"Consulta: {query}\n\nResultado da Análise: {result}",
            metadata={
                "type": "analysis",
                "client_id": str(client_id),
                "platform": platform,
                "timestamp": timestamp,
                "query": query
            }
        )
        
        # Get the vector DB
        vectordb = self._create_or_load_vector_db(client_id)
        
        # Add the document to Pinecone
        vectordb.add_documents([document])
    
    def _enhanced_agent_invoke(self, agent, retriever, client_id, platform, input_query, custom_options=None):
        # Primeiro, obtenha o contexto relevante do banco de dados vetorial
        context_docs = retriever.get_relevant_documents(input_query)
        context_text = "\n\n".join([doc.page_content for doc in context_docs])
        
        # Enhance the query with relevant context
        enhanced_query = f"""
        Informações de contexto de análises anteriores e resumos de dados:
        {context_text}
        
        Plataforma analisada: {platform}
        
        Com base no contexto acima e no conjunto de dados, responda à seguinte solicitação:
        {input_query}
        
        IMPORTANTE:
        1. Responda SEMPRE em português do Brasil, não em inglês.
        """

        # Add custom options if provided
        if custom_options and "format" in custom_options:
            enhanced_query += f"\nFormate sua resposta como {custom_options['format']}."

        # Run the agent with the enhanced query
        try:
            result = agent.invoke({"input": enhanced_query})

            # Store the query and result in the vector database for future reference
            self._store_analysis_in_vectordb(client_id, input_query, result.get("output", ""), platform)

            return result
        except Exception as e:
            return {"output": f"Ocorreu um erro durante a análise: {str(e)}"}

    def _get_client_agent_from_db(self, client_id: str, platform: str) -> Optional[Any]:
        try:
            # Nota: No esquema, não há coluna agent_data, então precisaremos adicioná-la
            query = """
            SELECT agent_data 
            FROM customer 
            WHERE id_customer = :client_id
            """
            
            with self.db_engine.connect() as connection:
                result = connection.execute(text(query), {"client_id": client_id}).fetchone()
                
            if result and result[0]:
                # Deserialize the stored agent
                agent_data = base64.b64decode(result[0])
                loaded_data = pickle.loads(agent_data)
                
                # Check if it has platform-specific data
                if platform in loaded_data:
                    return loaded_data[platform]
                    
            return None
        except Exception as e:
            print(f"Error retrieving agent from database: {str(e)}")
            return None
            
    def _store_client_agent_in_db(self, client_id: str, platform: str, agent_data: Dict) -> bool:
        try:
            # Check if we have existing data
            existing_data = {}
            
            query = """
            SELECT agent_data 
            FROM customer 
            WHERE id_customer = :client_id
            """
            
            with self.db_engine.connect() as connection:
                result = connection.execute(text(query), {"client_id": client_id}).fetchone()
                
            if result and result[0]:
                # Deserialize the stored agent
                existing_data = pickle.loads(base64.b64decode(result[0]))

            # Create a copy without the agent_obj that can't be pickled
            serializable_agent_data = {
                # Não inclua agent_obj
                "df": agent_data["df"],
                "timestamp": agent_data["timestamp"],
                "metadata": agent_data["metadata"]
                # Não inclua retriever também
            }
            
            # Update with the new platform data
            existing_data[platform] = serializable_agent_data
            
            # Serialize the updated data
            serialized_agent = base64.b64encode(pickle.dumps(existing_data))
            
            # Primeiro, verificamos se a coluna agent_data existe
            with self.db_engine.connect() as connection:
                # Iniciar transação
                with connection.begin():
                    # Verificar se a coluna agent_data existe e, se não existir, criá-la
                    alter_table_query = """
                    ALTER TABLE customer ADD COLUMN IF NOT EXISTS agent_data BYTEA;
                    """
                    connection.execute(text(alter_table_query))
                    
                    # Verificar se o cliente existe
                    check_query = "SELECT 1 FROM customer WHERE id_customer = :client_id"
                    exists = connection.execute(text(check_query), {"client_id": client_id}).fetchone() is not None
                    
                    if exists:
                        # Atualizar registro existente
                        update_query = """
                        UPDATE customer 
                        SET agent_data = :agent_data, 
                            updated_at = CURRENT_TIMESTAMP 
                        WHERE id_customer = :client_id
                        """
                        connection.execute(text(update_query), {
                            "client_id": client_id,
                            "agent_data": serialized_agent
                        })
                    else:
                        # Inserir novo registro
                        insert_query = """
                        INSERT INTO customer (id_customer, agent_data, created_at, updated_at) 
                        VALUES (:client_id, :agent_data, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """
                        try:
                            connection.execute(text(insert_query), {
                                "client_id": client_id,
                                "agent_data": serialized_agent
                            })
                        except Exception as e:
                            # Se falhar, pode ser porque há colunas obrigatórias faltando
                            print(f"Erro ao inserir no banco: {e}")
                            # Tente com todos os campos necessários
                            full_insert_query = """
                            INSERT INTO customer (id_customer, agent_data, created_at, updated_at, email, name, id_user) 
                            VALUES (:client_id, :agent_data, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 
                                    'temp@example.com', 'Temporary Name', 1)
                            """
                            connection.execute(text(full_insert_query), {
                                "client_id": client_id,
                                "agent_data": serialized_agent
                            })
                        
            return True
        except Exception as e:
            print(f"Error storing agent in database: {str(e)}")
            return False

    def get_client_agent(self, client_id: str, platform: str, 
                       start_date: Optional[str] = None, 
                       end_date: Optional[str] = None, 
                       force_new: bool = False) -> Any:
        from datetime import datetime

        # Verifique se devemos criar um novo agente
        if not force_new:
            # Primeira verificação no cache de memória
            cache_key = f"{client_id}_{platform}"
            if cache_key in self.clients_cache:
                cache_data = self.clients_cache[cache_key]
                return self._create_invoke_function(
                    cache_data["agent_obj"], 
                    cache_data["retriever"], 
                    client_id,
                    platform
                )

            # Em seguida, verifique no banco de dados
            stored_agent = self._get_client_agent_from_db(client_id, platform)
            if stored_agent:
                # Store in memory cache
                self.clients_cache[cache_key] = stored_agent
                return self._create_invoke_function(
                    stored_agent["agent_obj"], 
                    stored_agent["retriever"], 
                    client_id,
                    platform
                )

        # Se precisarmos criar um novo agente
        # Obtenha dados do cliente do banco de dados com filtragem de data
        df = self._get_client_data_from_db(client_id, platform, start_date, end_date)

        # Set up vector database
        vectordb = self._create_or_load_vector_db(client_id)
        retriever = vectordb.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 10}
        )

        # Create LLM instance with system prompt
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            api_key=OPENAI_API_KEY
        )

        # Update system prompt with platform information
        platform_system_prompt = self.system_prompt + f"\n\nVocê está analisando dados da plataforma: {platform}."

        # Add platform-specific context
        if platform == 'google_analytics':
            platform_system_prompt += """
            \nMétricas importantes do Google Analytics:
            - traffic_direct: Tráfego direto para o site
            - search_volume: Volume de pesquisas relacionadas
            - impressions: Impressões em resultados de pesquisa
            - traffic_organic_search: Tráfego vindo de busca orgânica
            - traffic_organic_social: Tráfego vindo de redes sociais
            """
        elif platform == 'facebook':
            platform_system_prompt += """
            \nMétricas importantes do Facebook:
            - page_impressions: Total de impressões da página
            - page_impressions_unique: Impressões únicas da página
            - page_follows: Novos seguidores da página
            """
        elif platform == 'instagram':
            platform_system_prompt += """
            \nMétricas importantes do Instagram:
            - reach: Alcance total de conteúdo
            - views: Visualizações de conteúdo
            - followers: Número de seguidores
            """

        # Create pandas dataframe agent
        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=df,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            extra_tools=[PythonAstREPLTool()],
            prefix=platform_system_prompt,
            include_df_in_prompt=True,
            max_iterations=8,
            max_execution_time=60,
            allow_dangerous_code=True
        )

        # Create agent data to store
        agent_data = {
            "agent_obj": agent,
            "retriever": retriever,
            "df": df,
            "timestamp": datetime.now().timestamp(),
            "metadata": {
                "client_id": client_id,
                "platform": platform,
                "row_count": len(df),
                "column_count": len(df.columns)
            }
        }

        # Store in memory cache
        cache_key = f"{client_id}_{platform}"
        self.clients_cache[cache_key] = agent_data

        # Store in database
        self._store_client_agent_in_db(client_id, platform, agent_data)

        # Return invoke function directly
        return self._create_invoke_function(agent, retriever, client_id, platform)

    def _create_invoke_function(self, agent, retriever, client_id, platform):
        def invoke_func(input_query, custom_options=None):
            return self._enhanced_agent_invoke(agent, retriever, client_id, platform, input_query, custom_options)
        return invoke_func

    def run_analysis(self, client_id: str, platform: str, analysis_type: str, 
                   custom_query: Optional[str] = None,
                   start_date: Optional[str] = None, end_date: Optional[str] = None,
                   output_format: str = "detalhado") -> Dict:
        from datetime import datetime

        # Preparar cláusula de filtro de data
        date_filter = ""
        if start_date and end_date:
            date_filter = f" para o período de {start_date} até {end_date}"
        elif start_date:
            date_filter = f" a partir de {start_date}"
        elif end_date:
            date_filter = f" até {end_date}"

        # Preparar consulta com base no tipo de análise
        if custom_query:
            query = custom_query
        else:
            analysis_prompts = {
                "descriptive": f"Forneça uma análise descritiva abrangente dos dados da plataforma {platform}{date_filter}. " +
                              "Inclua métricas-chave, tendências e padrões que você observa. " +
                              "Concentre-se no engajamento do usuário, taxas de conversão e métricas de crescimento.",
                
                "diagnostic": f"Realize uma análise diagnóstica dos dados da plataforma {platform}{date_filter}. " +
                            "Identifique possíveis causas para mudanças de desempenho, correlações entre métricas " +
                            "e fatores que podem estar influenciando o comportamento do usuário.",
                
                "predictive": f"Com base nos dados da plataforma {platform}{date_filter}, forneça uma análise preditiva sobre tendências futuras. " +
                             "Use padrões históricos para prever métricas para os próximos 30 dias. " +
                             "Identifique oportunidades potenciais e riscos.",
                
                "prescriptive": f"Com base nos dados da plataforma {platform}{date_filter}, forneça recomendações prescritivas. " +
                               "Sugira ações específicas para melhorar o desempenho, otimizar estratégias " +
                               "e abordar quaisquer problemas identificados na análise."
            }

            query = analysis_prompts.get(
                analysis_type.lower(), 
                f"Analise os dados da plataforma {platform}{date_filter} e forneça insights e recomendações."
            )

        # Obtenha a função de invocação do agente
        invoke_func = self.get_client_agent(client_id, platform, start_date, end_date)

        # Configure custom options
        options = {
            "format": output_format
        }

        # Run the analysis
        try:
            start_time = datetime.now()
            result = invoke_func(query, options)
            end_time = datetime.now()

            # Package the results
            return {
                "client_id": client_id,
                "platform": platform,
                "analysis_type": analysis_type,
                "query": query,
                "result": result.get("output", "Nenhum resultado gerado"),
                "execution_time": (end_time - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {
                "client_id": client_id,
                "platform": platform,
                "analysis_type": analysis_type,
                "query": query,
                "result": f"Falha na análise: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }