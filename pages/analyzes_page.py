# pages/analyzes_page.py
import streamlit as st
import time
from openai import OpenAI
from datetime import datetime
from pages.components.filters import filters
from datetime import datetime
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env
load_dotenv()

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
client = OpenAI(api_key=os.getenv("API_KEY"))

def agentAI(textEmpty, THREAD_ID, selected_filters):
    start_date = selected_filters.get('data_inicial')
    end_date = selected_filters.get('data_final')
    platform_data = selected_filters.get('platform')
    system_prompt = f'Hoje é dia {datetime.today().strftime('%Y-%m-%d')}. Você é um chatbot de análise de dados e não quero conversação, quero apenas a análise. Respostas sempre em portugês - Brasil. Baseado no intervalo de {start_date} até {end_date}, gere uma análise {textEmpty} baseado em meus dados da plataforma {platform_data}. Seja fora da curva e não me diga apenas o básico. Use o máximo de conhecimento que tem sobre análise de dados.'
    
    message = client.beta.threads.messages.create(
        thread_id=THREAD_ID,
        role="user",
        content=system_prompt
    )
    run = client.beta.threads.runs.create(thread_id=THREAD_ID, assistant_id=ASSISTANT_ID)
    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=THREAD_ID, run_id=run.id)
        time.sleep(1)
    
    message_response = client.beta.threads.messages.list(thread_id=THREAD_ID)
    messages = message_response.data

    laster_message = messages[0]
    return laster_message.content[0].text.value.strip()

def analyzes_page():
    selected_filters = filters("analyzes_page")
    col1, col2, col3 = st.columns(3)
    botao_clicado = None
    THREAD_ID = None

    with col1:
        if st.button("Descritiva"):
            botao_clicado = "descritiva"
            THREAD_ID = os.getenv("THREAD_ID")
    with col2:
        if st.button("Preditiva"):
            botao_clicado = "preditiva"
            THREAD_ID = os.getenv("THREAD_ID")
    with col3:
        if st.button("Prescritiva"):
            botao_clicado = "prescritiva"
            THREAD_ID = os.getenv("THREAD_ID")

    if botao_clicado:
        response = agentAI(botao_clicado, THREAD_ID, selected_filters)
        st.write(response)
    else:
        st.write("\nClique em um dos botões para ver um relatório de análise.")
