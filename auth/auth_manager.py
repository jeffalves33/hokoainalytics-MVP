# auth_manager.py
import streamlit as st
import streamlit_authenticator as stauth
from pathlib import Path
import yaml
from yaml.loader import SafeLoader
import psycopg2
from dotenv import load_dotenv
import os

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

        load_dotenv()
        self.db_config = {
            'dbname': 'postgres',
            'user': os.getenv('DB_USERNAME'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }

    def get_db_connection(self):
        """Estabelece conexão com o banco de dados."""
        return psycopg2.connect(**self.db_config)

    def get_client_keys(self, client_id):
        """Busca todas as chaves de API do cliente."""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Busca as chaves do cliente na tabela customer_keys
            cur.execute("""
                SELECT * FROM customer_keys 
                WHERE id_customer = %s
            """, (client_id,))
            client_keys = cur.fetchone()

            # Busca os tokens do Facebook/Instagram
            cur.execute("""
                SELECT facebook_access_token, instagram_access_token 
                FROM user_keys 
                WHERE id_user = %s
            """, (client_id,))
            user_tokens = cur.fetchone()
            
            if client_keys and user_tokens:
                # Organiza as chaves em um dicionário
                keys_dict = {
                    'facebook_page_id': client_keys[2],
                    'google_property_id': client_keys[3],
                    'google_credentials': {
                        'type': client_keys[4],
                        'project_id': client_keys[5],
                        'private_key_id': client_keys[6],
                        'private_key': client_keys[7],
                        'client_email': client_keys[8],
                        'client_id': client_keys[9],
                        'auth_uri': client_keys[10],
                        'token_uri': client_keys[11],
                        'auth_provider_x509_cert_url': client_keys[12],
                        'client_x509_cert_url': client_keys[13]
                    },
                    'instagram_page_id': client_keys[14],
                    'facebook_access_token': user_tokens[0],
                    'instagram_access_token': user_tokens[1]
                }
                return keys_dict
            return None
            
        except Exception as e:
            st.error(f"Erro ao buscar chaves do cliente: {str(e)}")
            return None
        finally:
            cur.close()
            conn.close()

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
        clients_data = {
            'ho.ko': {
                "ho.ko": {
                    "id": 1,
                    "nome": "ho.ko",
                    "email": "ho.ko@example.com",
                    "telefone": "123456789"
                },
                "Marcelo Psicologo": {
                    "id": 2,
                    "nome": "Marcelo Psicologo",
                    "email": "marcelo@example.com",
                    "telefone": "987654321"
                }
            },
            'cliente1': {
                "Cliente1": {
                    "id": 3,
                    "nome": "Cliente1",
                    "email": "cliente1@example.com"
                },
                # ... outros clientes ...
            }
        }
        return clients_data.get(username, {})

    def get_client_data(self, username, client_name):
        """Retorna os dados completos de um cliente específico com suas chaves."""
        clients = self.get_user_clients(username)
        client_data = clients.get(client_name, None)
        
        if client_data:
            # Busca as chaves do cliente
            client_keys = self.get_client_keys(client_data['id'])
            if client_keys:
                client_data['keys'] = client_keys
                
        return client_data