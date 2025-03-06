import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pytz
from dotenv import load_dotenv
import os

from datetime import datetime, timedelta, date
from api.facebook_api import get_facebook_insights
from api.instagram_api import get_instagram_follows

load_dotenv() 

FACEBOOK_BASE_URL = os.getenv("FACEBOOK_BASE_URL")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
INSTAGRAM_BASE_URL = os.getenv("INSTAGRAM_BASE_URL")
INSTAGRAM_PAGE_ID = os.getenv("INSTAGRAM_PAGE_ID")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

def bar_chart_followers(start_date, end_date, timezone='America/Sao_Paulo'):
    tz = pytz.timezone(timezone)
    
    facebook_followers = get_facebook_insights(FACEBOOK_BASE_URL, FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN, (start_date - timedelta(days=1)), end_date, "page_follows")
    instagram_followers = get_instagram_follows(INSTAGRAM_BASE_URL, INSTAGRAM_PAGE_ID, INSTAGRAM_ACCESS_TOKEN)
    facebook_valor = facebook_followers[-1] if len(facebook_followers) > 0 else 0

    dados = pd.DataFrame({
        'Plataforma': ['Facebook', 'Instagram'],
        'Seguidores': [facebook_valor, instagram_followers]
    })

    fig = px.bar(
        dados,
        x='Plataforma',
        y='Seguidores',
        color='Plataforma',  # opcional, para colorir cada barra diferente
        title='Seguidores'
    )

    st.plotly_chart(fig, use_container_width=True)