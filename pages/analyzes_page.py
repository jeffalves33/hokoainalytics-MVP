import streamlit as st
from pages.components.filters import filters
from dotenv import load_dotenv
from datetime import datetime

# Importa a classe AdvancedDataAnalyst
from utils.advanced_data_analyst import AdvancedDataAnalyst

# Carrega as variáveis do arquivo .env
load_dotenv()

# Inicializa o analista como variável global para reutilização
@st.cache_resource
def get_analyst():
    return AdvancedDataAnalyst()

def analyzes_page():
    if not st.session_state.selected_client_data:
        st.warning("Por favor, selecione um cliente para visualizar o dashboard.")
        return
        
    if 'keys' not in st.session_state.selected_client_data:
        st.error("Chaves de API não encontradas para este cliente.")
        return

    st.title("Análises")

    selected_filters = filters("analyzes_page")

    client_id = 1
    platform = selected_filters.get('platform')
    start_date = selected_filters.get("data_inicio", None)
    end_date = selected_filters.get("data_fim", None)

    if isinstance(start_date, datetime):
        start_date = start_date.strftime("%Y-%m-%d")
    if isinstance(end_date, datetime):
        end_date = end_date.strftime("%Y-%m-%d")

    if not platform:
        st.warning("Por favor, selecione uma plataforma para continuar.")
        return

    col1, col2, col3 = st.columns(3)
    
    # Armazena o tipo de análise selecionada em uma variável de sessão
    if "tipo_analise" not in st.session_state:
        st.session_state.tipo_analise = None

    with col1:
        if st.button("Descritiva"):
            st.session_state.tipo_analise = "descriptive"
    with col2:
        if st.button("Preditiva"):
            st.session_state.tipo_analise = "predictive"
    with col3:
        if st.button("Prescritiva"):
            st.session_state.tipo_analise = "prescriptive"

    # Formato de saída
    formato_opcoes = ["detalhado", "resumido", "tópicos"]
    formato = st.selectbox("Formato do relatório", formato_opcoes, index=0)

    # Opção para consulta personalizada
    usar_consulta_personalizada = st.checkbox("Usar consulta personalizada")
    consulta_personalizada = None

    if usar_consulta_personalizada:
        consulta_personalizada = st.text_area(
            "Digite sua consulta personalizada",
            "Analyze os dados e forneça insights sobre o desempenho."
        )

    # Botão Gerar à direita
    _, _, col_gerar = st.columns([1, 1, 1])

    with col_gerar:
        gerar_analise = st.button("Gerar Análise", type="primary")

    # Executar análise somente quando o botão Gerar for clicado
    if gerar_analise:
        # Verifica se um tipo de análise foi selecionado
        if not st.session_state.tipo_analise:
            st.error("Por favor, selecione um tipo de análise (Descritiva, Preditiva ou Prescritiva).")
        else:
            try:
                with st.spinner(f"Realizando análise {st.session_state.tipo_analise}..."):
                    # Inicializa o analista
                    analyst = get_analyst()
                    
                    # Executa a análise
                    response = analyst.run_analysis(
                        client_id=client_id,
                        platform=platform,
                        analysis_type=st.session_state.tipo_analise,
                        custom_query=consulta_personalizada,
                        start_date=start_date,
                        end_date=end_date,
                        output_format=formato
                    )
                    
                    # Exibe o resultado
                    if response["status"] == "success":
                        st.subheader(f"Análise {st.session_state.tipo_analise.capitalize()}")
                        
                        # Adiciona metadados da análise
                        with st.expander("Detalhes da análise", expanded=False):
                            st.write(f"**Cliente:** {client_id}")
                            st.write(f"**Plataforma:** {platform}")
                            st.write(f"**Período:** {start_date or 'Início'} até {end_date or 'Hoje'}")
                            st.write(f"**Tempo de execução:** {response.get('execution_time', 'N/A')} segundos")
                            
                        # Exibe o resultado principal
                        st.markdown(response["result"])
                    else:
                        st.error(f"Erro na análise: {response['result']}")
            except Exception as e:
                st.error(f"Ocorreu um erro ao executar a análise: {str(e)}")
    else:
        if st.session_state.tipo_analise:
            st.info("Clique no botão 'Gerar' para executar a análise.")
        else:
            st.info("Selecione um tipo de análise e clique no botão 'Gerar' para executar.")

if __name__ == "__main__":
    analyzes_page()