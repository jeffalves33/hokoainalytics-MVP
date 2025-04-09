import requests
import streamlit as st

BASE_URL= "https://graph.facebook.com/v20.0"

def get_facebook_insights(since, until, metric, period="day"):
    if not st.session_state.selected_client_data or 'keys' not in st.session_state.selected_client_data:
        raise ValueError("Chaves do cliente não encontradas")
    
    keys = st.session_state.selected_client_data['keys']
    page_id = keys['facebook_page_id']
    access_token = keys['facebook_access_token']

    url = f"{BASE_URL}/{page_id}/insights"
    params = {
        "metric": metric,
        "access_token": access_token,
        "period": period,
        "since": since,
        "until": until
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        values = [item["value"] for item in data["data"][0]["values"]]
        return values
    else:
        st.error(f"Erro na API do Facebook: {response.status_code} - {response.text}")
        return None