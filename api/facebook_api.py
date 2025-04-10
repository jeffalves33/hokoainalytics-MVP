import requests
import streamlit as st
from datetime import timedelta, datetime

BASE_URL= "https://graph.facebook.com/v20.0"

def get_facebook_insights(since, until, metric, period="day"):
    if not st.session_state.selected_client_data or 'keys' not in st.session_state.selected_client_data:
        raise ValueError("Chaves do cliente não encontradas")
    
    keys = st.session_state.selected_client_data['keys']
    page_id = keys['facebook_page_id']
    access_token = keys['facebook_access_token']

    # Função para dividir o intervalo de datas em blocos de 30 dias
    def split_date_range(start_date, end_date, delta_days=30):
        current_date = start_date
        while current_date < end_date:
            next_date = min(current_date + timedelta(days=delta_days), end_date)
            yield current_date, next_date
            current_date = next_date

    all_values = []

    # Iterar sobre cada bloco de 30 dias
    for start, end in split_date_range(since, until):
        url = f"{BASE_URL}/{page_id}/insights"
        params = {
            "metric": metric,
            "access_token": access_token,
            "period": period,
            "since": start.strftime("%Y-%m-%d"),
            "until": end.strftime("%Y-%m-%d")
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            values = [item["value"] for item in data["data"][0]["values"]]
            all_values.extend(values)
        else:
            st.error(f"Erro na API do Facebook: {response.status_code} - {response.text}")
            return None
    return all_values