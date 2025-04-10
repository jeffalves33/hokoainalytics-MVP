# pages/dashboard_page.py
import streamlit as st

from pages.components.filters import filters
from pages.components.graphs.line_chart import line_chart_Reach
from pages.components.graphs.line_chart import line_chart_Impressions
from pages.components.graphs.bar_chart import bar_chart_followers
from pages.components.graphs.table_chart import table_chart_websiteTraffic, table_chart_searchVolume

def dashboard_page():
    if not st.session_state.selected_client_data:
        st.warning("Por favor, selecione um cliente para visualizar o dashboard.")
        return
        
    if 'keys' not in st.session_state.selected_client_data:
        st.error("Chaves de API não encontradas para este cliente.")
        return

    selected_filters = filters("dashboard_page")
    start_date = selected_filters.get('data_inicial')
    end_date = selected_filters.get('data_final')

    if start_date == end_date:
        st.warning(
            "As datas inicial e final são iguais. Por favor, forneça um intervalo válido de datas para gerar as análises.",
            icon="⚠️"
        )
        return

    # Alcance
    line_chart_Reach(start_date, end_date)
    # Impressão
    line_chart_Impressions(start_date, end_date)
    # Seguidores
    bar_chart_followers(start_date, end_date)
    # Tráfego de site
    table_chart_websiteTraffic(start_date, end_date)
    # Volume de pesquisa
    table_chart_searchVolume(start_date, end_date)
