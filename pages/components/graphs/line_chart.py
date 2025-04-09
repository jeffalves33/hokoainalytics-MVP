#pages/components/graphs/line_chart.py
import streamlit as st
import pandas as pd
import plotly.express as px
import pytz

from api.googleAnalytics_api import get_googleAnalytics_impressions
from api.instagram_api import get_instagram_reach, get_instagram_impressions
from api.facebook_api import get_facebook_insights
from datetime import timedelta

def line_chart_Reach(start_date, end_date, timezone='America/Sao_Paulo'):
    tz = pytz.timezone(timezone)
    dates = pd.date_range(start=(start_date + timedelta(days=1)), end=(end_date + timedelta(days=1)))
    dates = dates.tz_localize('UTC').tz_convert(tz)

    facebook_reach = get_facebook_insights((start_date - timedelta(days=1)), end_date, "page_impressions_unique")
    instagram_reach = get_instagram_reach((start_date - timedelta(days=1)), end_date)

    reach_data = pd.DataFrame({
        'Data': dates,
        'Facebook': facebook_reach,
        'Instagram': instagram_reach
    })

    fig = px.line(reach_data, x='Data', y=['Facebook', 'Instagram'], 
                  labels={'value': 'Alcance', 'variable': 'Plataformas'},
                  title="Alcance")

    fig.update_layout(hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

def line_chart_Impressions(start_date, end_date, timezone='America/Sao_Paulo'):
    tz = pytz.timezone(timezone)
    dates = pd.date_range(start=(start_date + timedelta(days=1)), end=(end_date + timedelta(days=1)))
    dates = dates.tz_localize('UTC').tz_convert(tz)

    facebook_impressions = get_facebook_insights((start_date - timedelta(days=1)), end_date, "page_impressions")
    instagram_impressions = get_instagram_impressions((start_date - timedelta(days=1)), end_date)
    googleAnalytics_impressions = get_googleAnalytics_impressions(start_date, end_date)

    reach_data = pd.DataFrame({
        'Data': dates,
        'Facebook': facebook_impressions,
        'Instagram': instagram_impressions,
        'Google Analytics': googleAnalytics_impressions
    })

    fig = px.line(reach_data, x='Data', y=['Facebook', 'Instagram', 'Google Analytics'], 
                  labels={'value': 'Impressões', 'variable': 'Plataformas'},
                  title="Impressões")

    fig.update_layout(hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)
