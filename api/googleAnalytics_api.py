# api/googleAnalytics.py
from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
from google.oauth2 import service_account
from datetime import datetime, timedelta
import pandas as pd
import json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
credentials_path = os.path.join(current_dir, "../../../auth/credentials.json")
with open(credentials_path, "r") as f:
    credentials_info = json.load(f)
property_id = os.getenv("GOOGLE_PROPERTY_ID")
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

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))],
        dimensions=[Dimension(name="sessionDefaultChannelGroup"), Dimension(name="date")],
        metrics=[Metric(name="sessions")],
    )

    response = client.run_report(request)

    return response

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