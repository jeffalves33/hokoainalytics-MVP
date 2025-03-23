# pages/chat_page.py
import streamlit as st
import json
from openai import OpenAI
from datetime import datetime
from langchain.schema import Document
from dotenv import load_dotenv
import os
import time

from utils.db.vector_db import VectorDBManager

load_dotenv()

def chat_page():
    st.title("Chat Analítico")
    
    # Constantes para o cliente específico de teste
    CLIENT_ID = 1
    PINECONE_INDEX = "client-c4ca4238a0"
    AGENT_ID = "asst_gHL8fRWospTobQyAaO8zFLs"
    
    # Inicializa o gerenciador de banco de dados vetorial
    vector_db_manager = VectorDBManager(
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Initialize session state for messages
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Digite sua mensagem aqui..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Pensando...")
            
            # Get response using simplified approach
            response = generate_response(
                vector_db_manager,
                CLIENT_ID,
                PINECONE_INDEX,
                AGENT_ID,
                prompt,
                st.session_state.messages
            )
            
            # Display the response
            message_placeholder.markdown(response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def generate_response(vector_db_manager, client_id, pinecone_index, agent_id, user_query, message_history):
    """Generate a response using RAG system for the specific client"""
    try:
        # Carregar diretamente o índice vetorial para o cliente específico
        # Não usamos o método create_or_load_vector_db com index_name personalizado
        # pois ele gera o nome do índice internamente
        vectordb = vector_db_manager.create_or_load_vector_db(client_id)
        
        retriever = vectordb.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 10}
        )

        # Get relevant documents for the user query
        context_docs = retriever.invoke(user_query)
        context_text = "\n\n".join([doc.page_content for doc in context_docs])

        # Obter informações do cliente
        client_name = "Ho.ko"  # Hardcoded para o cliente específico
        
        # Format messages for OpenAI
        openai_messages = []

        # System message com instruções específicas para o teste
        system_message = f"""Você é um assistente especializado em análise de dados de marketing digital para o cliente {client_name}.
        ID do cliente: {client_id}
        Comunicação: Direta e objetiva
        
        Responda às perguntas do usuário com base no contexto fornecido e nos dados disponíveis.
        Mantenha um tom profissional.

        Contexto adicional relevante da base de dados:
        {context_text}

        Se você não tiver informações suficientes para responder à pergunta, diga isso claramente.
        Seja conciso, claro e objetivo em suas respostas."""
        
        openai_messages.append({"role": "system", "content": system_message})
        
        # Add chat history (only the last 8 messages to prevent context overflow)
        for msg in message_history[-8:]:
            openai_messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Create OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Generate response
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=openai_messages,
            temperature=0.2
        )

        response_content = response.choices[0].message.content
        return response_content
        
    except Exception as e:
        return f"Desculpe, encontrei um erro ao processar sua solicitação: {str(e)}"