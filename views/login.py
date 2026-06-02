import streamlit as st
from utils.ejercicios import puntos_iniciales_por_experiencia

def pantalla_login():
    st.markdown('<div class="title">KneePlay Rehab</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Sistema gamificado de apoyo para ejercicios domiciliarios de rodilla</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1.3, 1])

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.subheader("Inicio de sesión del paciente")
        st.write("Ingresa tus datos para iniciar tu rutina guiada.")

        nombre = st.text_input("Nombre del paciente")
        edad = st.number_input("Edad", min_value=18, max_value=100, value=45)
        dolor = st.slider("Nivel de dolor actual en la rodilla", 0, 10, 3)
        experiencia = st.selectbox(
            "Nivel de experiencia con ejercicios",
            ["Principiante", "Intermedio", "Avanzado"]
        )

        iniciar = st.button("Iniciar mi rehabilitación", use_container_width=True)

        if iniciar:
            if nombre.strip() == "":
                st.warning("Por favor, ingresa el nombre del paciente.")
            else:
                st.session_state.logged_in = True
                st.session_state.nombre = nombre
                st.session_state.edad = edad
                st.session_state.dolor = dolor
                st.session_state.experiencia = experiencia
                st.session_state.puntos = puntos_iniciales_por_experiencia(experiencia)
                st.session_state.nivel = 1
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)