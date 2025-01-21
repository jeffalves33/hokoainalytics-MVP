# pages/chat_page.py
import streamlit as st
from openai import OpenAI
from streamlit_chat import message
import time
from dotenv import load_dotenv
import os

load_dotenv()

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
client = OpenAI(api_key=os.getenv("API_KEY"))
THREAD_ID = os.getenv("THREAD_ID")

def responder_pergunta(pergunta):
    client.beta.threads.messages.create(
        thread_id=THREAD_ID,
        role="user",
        content=pergunta
    )
    run = client.beta.threads.runs.create(thread_id=THREAD_ID, assistant_id=ASSISTANT_ID)
    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=THREAD_ID, run_id=run.id)
        time.sleep(1)

    message_response = client.beta.threads.messages.list(thread_id=THREAD_ID)
    messages = message_response.data
    latest_message = messages[0].content[0].text.value.strip()
    return latest_message

def on_input_change():
    user_input = st.session_state.user_input
    if user_input:
        st.session_state.past.append(user_input)
        resposta = responder_pergunta(user_input)
        st.session_state.generated.append(resposta)
    else:
        st.warning("Por favor, insira uma pergunta.")

def on_btn_click():
    del st.session_state.past[:]
    del st.session_state.generated[:]

def chat_page():
    st.session_state.setdefault('past', [])
    st.session_state.setdefault('generated', [])
    st.title("Assistente")

    chat_placeholder = st.empty()

    with chat_placeholder.container():
        for i in range(len(st.session_state['generated'])):
            message(st.session_state['past'][i], is_user=True, key=f"{i}_user")
            message(st.session_state['generated'][i], key=f"{i}")

        st.button("Limpar mensagens", on_click=on_btn_click)

    st.text_input("Digite sua pergunta:", on_change=on_input_change, key="user_input")
