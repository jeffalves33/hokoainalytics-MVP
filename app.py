# app.py
import streamlit as st

from auth.auth_manager import AuthManager
from pages.components.navigation import navigation

st.set_page_config(initial_sidebar_state="collapsed")

auth_manager = AuthManager()

def show_sidebar():
    clients = auth_manager.get_user_clients(st.session_state.username)
    st.sidebar.selectbox("Cliente", clients)
    auth_manager.logout()

def main():
    auth_manager.login()

    if st.session_state.authenticated:
        
        show_sidebar()
        navigation()

if __name__ == "__main__":
    main()

