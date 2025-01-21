import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pytz
from dotenv import load_dotenv
import os

from datetime import datetime, timedelta, date
from api.facebook_api import get_facebook_insights

load_dotenv() 

BASE_URL = os.getenv("FACEBOOK_BASE_URL")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")

def bar_chart_followers(start_date, end_date, timezone='America/Sao_Paulo'):
    tz = pytz.timezone(timezone)
    dates = pd.date_range(start=(start_date + timedelta(days=1)), end=(end_date + timedelta(days=1)))
    dates = dates.tz_localize('UTC').tz_convert(tz)
    
    facebook_followers = get_facebook_insights(BASE_URL, PAGE_ID, ACCESS_TOKEN, (start_date - timedelta(days=1)), end_date, "page_follows")
    followers_data = pd.DataFrame({
        'Data': dates,
        'Facebook': facebook_followers,
        'Instagram': 0,
    })

    followers_data_melted = followers_data.melt(id_vars='Data', 
                                                value_vars=['Facebook', 'Instagram'], 
                                                var_name='Plataforma', 
                                                value_name='Seguidores')

    fig = px.bar(followers_data_melted, x='Data', y='Seguidores', color='Plataforma',
                 title='Seguidores')

    st.plotly_chart(fig, use_container_width=True)