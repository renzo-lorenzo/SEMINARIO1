import streamlit as st

from components.participant_search import mostrar_buscador
from components.participant_list import mostrar_lista_participantes
from components.participant_form import mostrar_formulario_participante


def pantalla_login():

    st.title("👋 Bienvenido")
    st.write("Seleccione el participante que realizará los ejercicios.")

    st.divider()

    # ==========================================
    # BUSCADOR
    # ==========================================

    busqueda = mostrar_buscador()

    # ==========================================
    # COLUMNAS
    # ==========================================

    col_lista, espacio, col_formulario = st.columns([2.3, 0.15, 1.5])

    # ==========================================
    # LISTA
    # ==========================================

    with col_lista:

        mostrar_lista_participantes(busqueda)

    # ==========================================
    # FORMULARIO
    # ==========================================

    with col_formulario:

        mostrar_formulario_participante()