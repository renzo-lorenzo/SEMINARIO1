import streamlit as st
from utils.asistente_voz import (
    inicializar_asistente_voz,
    mostrar_control_voz_global,
    hablar_bienvenida_si_corresponde
)
from utils.styles import cargar_estilos
from views.login import pantalla_login
from views.dashboard import pantalla_dashboard
from views.ejercicio import pantalla_ejercicio
from views.mapa_niveles import pantalla_mapa_niveles
from views.tutorial import pantalla_tutorial
from database.participant_repository import initialize_database
initialize_database()


st.set_page_config(
    page_title="Activate",
    page_icon="🦵",
    layout="wide"
)

inicializar_asistente_voz()
mostrar_control_voz_global()

cargar_estilos()
inicializar_asistente_voz()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "pantalla" not in st.session_state:
    st.session_state.pantalla = "dashboard"

if "nombre" not in st.session_state:
    st.session_state.nombre = ""

if "participant_id" not in st.session_state:
    st.session_state.participant_id = None

if "participant_name" not in st.session_state:
    st.session_state.participant_name = ""

if "participant_last_name" not in st.session_state:
    st.session_state.participant_last_name = ""

if "edad" not in st.session_state:
    st.session_state.edad = 0

if "puntos" not in st.session_state:
    st.session_state.puntos = 0

if "nivel" not in st.session_state:
    st.session_state.nivel = 1

inicializar_asistente_voz()

if not st.session_state.logged_in:
    pantalla_login()
else:
    hablar_bienvenida_si_corresponde()

    if st.session_state.pantalla == "dashboard":
        pantalla_dashboard()
    elif st.session_state.pantalla == "ejercicio":
        pantalla_ejercicio()
    elif st.session_state.pantalla == "mapa":
        pantalla_mapa_niveles()
    elif st.session_state.pantalla == "tutorial":
        pantalla_tutorial() 