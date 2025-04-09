# api/googleAnalytics.py
from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
from google.oauth2 import service_account
from datetime import datetime, timedelta
import streamlit as st

def get_analytics_client():
    if not st.session_state.selected_client_data or 'keys' not in st.session_state.selected_client_data:
        raise ValueError("Chaves do cliente não encontradas")

    keys = st.session_state.selected_client_data['keys']
    credentials_info = keys['google_credentials']
    property_id = keys['google_property_id']
    
    if 'private_key' in credentials_info:
        credentials_info['private_key'] = credentials_info['private_key'].replace('\\n', '\n')
    
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    client = BetaAnalyticsDataClient(credentials=credentials)

    return client, property_id

def get_googleAnalytics_impressions(start_date, end_date):
    try:
        client, property_id = get_analytics_client()
        start = datetime.strptime(start_date.isoformat(), "%Y-%m-%d")
        end = datetime.strptime(end_date.isoformat(), "%Y-%m-%d")
        all_dates = [(start + timedelta(days=i)).strftime("%Y%m%d") for i in range((end - start).days + 1)]

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))],
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="sessions")],
        )

        response = client.run_report(request)
        results = {row.dimension_values[0].value: int(row.metric_values[0].value) for row in response.rows}
        sessions_array = [results.get(date, 0) for date in all_dates]

        return sessions_array
    except Exception as e:
        st.error(f"Erro ao buscar dados do Google Analytics: {str(e)}")
        return []

def get_googleAnalytics_traffic(start_date, end_date):
    try:
        client, property_id = get_analytics_client()
        start = datetime.strptime(start_date.isoformat(), "%Y-%m-%d")
        end = datetime.strptime(end_date.isoformat(), "%Y-%m-%d")
        all_dates = [(start + timedelta(days=i)).strftime("%Y%m%d") for i in range((end - start).days + 1)]

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))],
            dimensions=[Dimension(name="sessionDefaultChannelGroup"), Dimension(name="date")],
            metrics=[Metric(name="sessions")],
        )

        response = client.run_report(request)

        results = {}
        for row in response.rows:
            date = row.dimension_values[0].value
            sessions = int(row.metric_values[0].value)
            results[date] = results.get(date, 0) + sessions

        sessions_array = [results.get(date, 0) for date in all_dates]

        return sessions_array
    except Exception as e:
        st.error(f"Erro ao buscar dados do Google Analytics: {str(e)}")
        return []

def get_googleAnalytics_search_volume(start_date, end_date):
    try:
        client, property_id = get_analytics_client()
        start = datetime.strptime(start_date.isoformat(), "%Y-%m-%d")
        end = datetime.strptime(end_date.isoformat(), "%Y-%m-%d")
        all_dates = [(start + timedelta(days=i)).strftime("%Y%m%d") for i in range((end - start).days + 1)]

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))],
            dimensions=[
                Dimension(name="date"),
                Dimension(name="searchTerm"),
            ],
            metrics=[Metric(name="sessions")],
        )

        response = client.run_report(request)

        results = {}
        for row in response.rows:
            date = row.dimension_values[0].value
            sessions = int(row.metric_values[0].value)
            results[date] = results.get(date, 0) + sessions

        sessions_array = [results.get(date, 0) for date in all_dates]

        return sessions_array
    except Exception as e:
        st.error(f"Erro ao buscar dados do Google Analytics: {str(e)}")
        return []