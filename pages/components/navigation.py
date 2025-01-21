#  pages/components/navigation.py
import streamlit as st

from pages.dashboard_page import dashboard_page
from pages.analyzes_page import analyzes_page
from pages.chat_page import chat_page

def navigation():
    # Widgets shared by all the pages
    # st.sidebar.selectbox("Foo", ["A", "B", "C"], key="foo")
    # st.sidebar.checkbox("Bar", key="bar")
    
    # paginação do menu lateral 
    pg = st.navigation([st.Page(dashboard_page, title="Dashboard"), st.Page(analyzes_page, title="Análises"), st.Page(chat_page, title="Chat")], )
    pg.run()