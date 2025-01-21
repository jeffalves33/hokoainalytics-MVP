# auth_manager.py
import streamlit as st
import streamlit_authenticator as stauth
from pathlib import Path
import yaml
from yaml.loader import SafeLoader


class AuthManager:
    def __init__(self, config_path=None):
        # Define o caminho absoluto para o arquivo config.yaml
        if config_path is None:
            config_path = Path(__file__).parent / 'config.yaml'
        else:
            config_path = Path(config_path)
        
        # Carrega o arquivo de configuração com as credenciais
        with open(config_path) as file:
            self.config = yaml.load(file, Loader=SafeLoader)

        # Inicializa o autenticador com as credenciais e parâmetros de cookie
        self.authenticator = stauth.Authenticate(
            self.config['credentials'],
            self.config['cookie']['name'],
            self.config['cookie']['key'],
            self.config['cookie']['expiry_days'],
            0,  # Reautenticação (0 significa desativado)
            True  # Ativa o lembrete de senha
        )

    def login(self):
        """Gerencia o processo de login e autenticação da sessão."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False

        if not st.session_state.authenticated:
            authentication_status = self.authenticator.login()
            if st.session_state.get("username"):
                st.session_state.authenticated = True

    def logout(self):
        """Função para fazer logout, limpando o estado de autenticação."""
        self.authenticator.logout(button_name='Sair', location="sidebar")
        st.session_state.authenticated = False

    def get_user_clients(self, username):
        """Retorna os clientes com base no nome de usuário."""
        clients = {
            'ho.ko': ["ho.ko"],
            'cliente1': ["Cliente1", "Cliente2", "Cliente3"]
        }
        return clients.get(username, [])