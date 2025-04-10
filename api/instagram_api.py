import requests
from datetime import timedelta
import streamlit as st

BASE_URL= "https://graph.facebook.com/v22.0"

def get_instagram_credentials():
    if not st.session_state.selected_client_data or 'keys' not in st.session_state.selected_client_data:
        raise ValueError("Chaves do cliente não encontradas")
    
    keys = st.session_state.selected_client_data['keys']
    return {
        'page_id': keys['instagram_page_id'],
        'access_token': keys['instagram_access_token']
    }

def get_instagram_reach(since, until, period="day"):
    credentials = get_instagram_credentials()

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
        url = f"{BASE_URL}/{credentials['page_id']}/insights"
        params = {
            "metric": 'reach',
            "access_token": credentials['access_token'],
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
            st.error(f"Erro na API do Instagram: {response.status_code} - {response.text}")
            return None

    return all_values

def get_instagram_impressions(since, until, period="day"):
    credentials = get_instagram_credentials()
    start = since
    end = until

    daily_results = []

    current_date = start
    while current_date < end:
        # Calculate the next day
        next_date = current_date + timedelta(days=1)
        
        # Format dates for API
        since = current_date.strftime("%Y-%m-%d")
        until = next_date.strftime("%Y-%m-%d")
        
        # Prepare URL and parameters
        url = f"{BASE_URL}/{credentials['page_id']}/insights"
        params = {
            "metric": 'views',
            "metric_type": 'total_value',
            "access_token": credentials['access_token'],
            "period": "day",
            "since": since,
            "until": until
        }
        
        # Make the request
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            # Extract total value for the day
            if "data" in data and len(data["data"]) > 0:
                daily_value = data["data"][0]["total_value"]["value"]
                daily_results.append(daily_value)
            else:
                print(f"No data found for {since}")
                daily_results.append({
                    "value": 0,
                    "date": since
                })
        else:
            print(f"Error for {since}: {response.status_code} - {response.text}")
            daily_results.append({
                "value": None,
                "date": since
            })
        
        # Move to next day
        current_date = next_date
    
    return daily_results

def get_instagram_follows():
    credentials = get_instagram_credentials()

    url = f"{BASE_URL}/{credentials['page_id']}"
    params = {
        "fields": 'followers_count',
        "access_token": credentials['access_token'],
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        value = data["followers_count"]
        return value
    else:
        st.error(f"Erro na API do Instagram: {response.status_code} - {response.text}")
        return None