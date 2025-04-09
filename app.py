# app.py
import streamlit as st

from auth.auth_manager import AuthManager
from pages.components.navigation import navigation

st.set_page_config(initial_sidebar_state="collapsed")

auth_manager = AuthManager()

def show_sidebar():
    clients_data = auth_manager.get_user_clients(st.session_state.username)
    client_names = list(clients_data.keys())
    
    # Inicializa os estados se não existirem
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None
        st.session_state.selected_client_data = None
    
    # Armazena o cliente selecionado no session_state
    selected_client = st.sidebar.selectbox(
        "Cliente",
        client_names,
        key='client_selector'
    )
    
    # Atualiza o cliente selecionado e seus dados quando houver mudança
    if selected_client != st.session_state.selected_client:
        st.session_state.selected_client = selected_client
        # Busca dados completos do cliente, incluindo as chaves
        client_data = auth_manager.get_client_data(st.session_state.username, selected_client)
        st.session_state.selected_client_data = client_data
        # Recarrega a página para atualizar os dados
        st.rerun()
    
    auth_manager.logout()

def main():
    auth_manager.login()

    if st.session_state.authenticated:  
        show_sidebar()
        navigation()

if __name__ == "__main__":
    main()

