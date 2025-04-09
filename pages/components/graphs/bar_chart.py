import streamlit as st
import pandas as pd
import plotly.express as px
import pytz

from datetime import timedelta
from api.facebook_api import get_facebook_insights
from api.instagram_api import get_instagram_follows

def bar_chart_followers(start_date, end_date, timezone='America/Sao_Paulo'):
    tz = pytz.timezone(timezone)
    
    facebook_followers = get_facebook_insights((start_date - timedelta(days=1)), end_date, "page_follows")
    instagram_followers = get_instagram_follows()
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