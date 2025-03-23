# pages/components/filters.py
import streamlit as st
from datetime import date

def date_inputs():
    col1, col2 = st.columns(2)

    with col1:
        data_inicial = st.date_input('Data inicial', value=date.today())

    with col2:
        data_final = st.date_input('Data final', value=date.today())

    if data_inicial > data_final:
        st.error('A data inicial não pode ser posterior à data final!')
        return {"data_inicial": date.today(), "data_final": date.today()}
    else:
        return {"data_inicial": data_inicial, "data_final": data_final}

def gender():
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        option_man = st.checkbox(label="Homem", value=True)
    with col2:
        option_woman = st.checkbox(label="Mulher", value=True)

    return {
        "genero_homem": option_man,
        "genero_mulher": option_woman
    }

def platform():
    radio = st.radio(
        "",
        ["Facebook", "Google Analytics", "Instagram"],
        horizontal=True
    )
    return {"platform": radio}

def filters(page):
    filters_obj = {}
    date_data = date_inputs()
    platform_data = None

    if date_data:
        filters_obj.update(date_data)

    if(page == "analyzes_page"):
        platform_data = platform()
        filters_obj.update(platform_data)

    return filters_obj
