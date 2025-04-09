# pages/components/graphs/table_chart.py
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from api.googleAnalytics_api import get_googleAnalytics_traffic, get_googleAnalytics_search_volume

def table_chart_websiteTraffic(start_date, end_date):
    start = datetime.strptime(start_date.isoformat(), "%Y-%m-%d")
    end = datetime.strptime(end_date.isoformat(), "%Y-%m-%d")
    all_dates = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end - start).days + 1)]

    googleAnalytics_traffic = get_googleAnalytics_traffic(start_date, end_date)

    data = []
    for date, sessions in zip(all_dates, googleAnalytics_traffic):
        row_data = {
            "Date": date,
            "Sessions": sessions,
        }
        data.append(row_data)

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    df = df.sort_values("Date")

    pivot_table = df.pivot_table(
        index="Date",
        values="Sessions",
        aggfunc="sum",
    ).fillna(0).astype(int)

    pivot_table.index = pivot_table.index.strftime("%Y-%m-%d")

    st.markdown("<br><h5><strong>Tráfego de site</strong></h5>", unsafe_allow_html=True)
    st.dataframe(pivot_table, height=300, use_container_width=True)

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
