# api/googleAnalytics.py
from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
from google.oauth2 import service_account
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

property_id = os.getenv("GOOGLE_PROPERTY_ID")
credentials_info = {
    "type": os.getenv("GOOGLE_CREDENTIALS_TYPE"),
    "project_id": os.getenv("GOOGLE_CREDENTIALS_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_CREDENTIALS_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_CREDENTIALS_PRIVATE_KEY"),
    "client_email": os.getenv("GOOGLE_CREDENTIALS_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CREDENTIALS_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_CREDENTIALS_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_CREDENTIALS_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_CREDENTIALS_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CREDENTIALS_CLIENT_X509_CERT_URL"),
}

credentials = service_account.Credentials.from_service_account_info(credentials_info)
client = BetaAnalyticsDataClient(credentials=credentials)

def get_googleAnalytics_impressions(start_date, end_date):
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

def get_googleAnalytics_traffic(start_date, end_date):
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

def get_googleAnalytics_search_volume(start_date, end_date):
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