import streamlit as st


def mostrar_buscador():

    return st.text_input(
        "🔍 Buscar participante",
        placeholder="Escriba el nombre del participante..."
    )