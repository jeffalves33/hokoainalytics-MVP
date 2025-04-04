# pages/dashboard_page.py
import streamlit as st
import numpy as np
import pandas as pd

from pages.components.filters import filters
from pages.components.graphs.line_chart import line_chart_Reach
from pages.components.graphs.line_chart import line_chart_Impressions
from pages.components.graphs.bar_chart import bar_chart_followers
from pages.components.graphs.table_chart import table_chart_websiteTraffic, table_chart_searchVolume

def dashboard_page():
    selected_filters = filters("dashboard_page")
    start_date = selected_filters.get('data_inicial')
    end_date = selected_filters.get('data_final')

    if start_date == end_date:
        st.warning(
            "As datas inicial e final são iguais. Por favor, forneça um intervalo válido de datas para gerar as análises.",
            icon="⚠️"
        )
        return

    date_difference = (end_date - start_date).days + 1
    if date_difference > 30:
        st.error(
            "O intervalo entre as datas é maior que 30 dias. Por favor, selecione um período de até 30 dias.",
            icon="❌"
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

#1 - pelo front, terminar os gráficos.
#2 - com os gráficos prontos, consumir automaticamente DAS PLATAFORMAS a medida que selecionar o intervalo.
#page_impressions_unique: impressões totais
#   page_posts_impressions_unique: alcance total
