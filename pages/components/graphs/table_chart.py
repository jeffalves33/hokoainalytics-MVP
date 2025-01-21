# pages/components/graphs/table_chart.py
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from google.analytics.data import BetaAnalyticsDataClient
from google.oauth2 import service_account
from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
from api.googleAnalytics_api import get_googleAnalytics_traffic, get_googleAnalytics_search_volume
import json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
credentials_path = os.path.join(current_dir, "../../../auth/credentials.json")
with open(credentials_path, "r") as f:
    credentials_info = json.load(f)
property_id = os.getenv("GOOGLE_PROPERTY_ID")

credentials = service_account.Credentials.from_service_account_info(credentials_info)
client = BetaAnalyticsDataClient(credentials=credentials)

def table_chart_websiteTraffic(start_date, end_date):
    start = datetime.strptime(start_date.isoformat(), "%Y-%m-%d")
    end = datetime.strptime(end_date.isoformat(), "%Y-%m-%d")

    googleAnalytics_traffic = get_googleAnalytics_traffic(start_date, end_date)

    data = []
    for row in googleAnalytics_traffic.rows:
        row_data = {
            "Date": row.dimension_values[1].value,
            "Channel Group": row.dimension_values[0].value,
            "Sessions": int(row.metric_values[0].value),
        }
        data.append(row_data)

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
    df = df.sort_values("Date")

    start_date = pd.to_datetime(start, format="%Y-%m-%d")
    end_date = pd.to_datetime(end, format="%Y-%m-%d")
    all_dates = pd.date_range(start=start_date, end=end_date)

    df_full = pd.DataFrame({"Date": all_dates})
    df_full = df_full.merge(df, on="Date", how="left")

    df_full["Channel Group"] = df_full["Channel Group"].fillna("No Data")
    df_full["Sessions"] = df_full["Sessions"].fillna(0).astype(int)

    pivot_table = df_full.pivot_table(
        index="Date",
        columns="Channel Group",
        values="Sessions",
        aggfunc="sum",
    ).fillna(0).astype(int)

    if "No Data" in pivot_table.columns:
        pivot_table = pivot_table.drop(columns=["No Data"])

    pivot_table.index = pivot_table.index.strftime("%Y-%m-%d")

    st.markdown("<br><h5><strong>Tráfego de site</strong></h5>", unsafe_allow_html=True)
    st.dataframe(pivot_table, height=300, use_container_width=True)
    #st.table(pivot_table)

def table_chart_searchVolume(start_date, end_date):
    start = datetime.strptime(start_date.isoformat(), "%Y-%m-%d")
    end = datetime.strptime(end_date.isoformat(), "%Y-%m-%d")

    search_volume = get_googleAnalytics_search_volume(start_date, end_date)

    data = []
    for date, sessions in zip(
        [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end - start).days + 1)],
        search_volume,
    ):
        data.append({"Date": date, "Sessions": sessions})

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    df = df.sort_values("Date")

    all_dates = pd.date_range(start=start, end=end)
    df_full = pd.DataFrame({"Date": all_dates})
    df_full = df_full.merge(df, on="Date", how="left")
    df_full["Sessions"] = df_full["Sessions"].fillna(0).astype(int)

    df_full["Date"] = df_full["Date"].dt.strftime("%Y-%m-%d")

    pivot_table = df_full.pivot_table(
        index="Date",
        values="Sessions",
        aggfunc="sum",
    )

    st.markdown("<br><h5><strong>Volume de Pesquisa Orgânica</strong></h5>", unsafe_allow_html=True)
    st.dataframe(pivot_table, height=300, use_container_width=True)
