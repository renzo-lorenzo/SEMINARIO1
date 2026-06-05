import streamlit as st
import time
import os


def obtener_video_tutorial(ejercicio_id):
    videos_tutoriales = {
        1: "imagenes/tutorial_flexion.mp4",
        2: "imagenes/tutorial_elevacion_pierna.mp4",
        3: "imagenes/tutorial_mini_sentadilla.mp4",
    }

    return videos_tutoriales.get(
        ejercicio_id,
        "imagenes/tutorial_extension_rodilla.mp4"
    )


def pantalla_tutorial():
    ejercicio = st.session_state.get("ejercicio_actual", None)

    if ejercicio is None:
        st.warning("No se seleccionó ningún ejercicio.")
        if st.button("Volver al mapa de niveles"):
            st.session_state.pantalla = "mapa"
            st.rerun()
        return

    st.markdown(
        f'<div class="title">{ejercicio["nombre"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Antes de iniciar, revisa el video tutorial del ejercicio</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Ten en cuenta el video tutorial")

    st.write(
        "Observa cómo se realiza el movimiento antes de comenzar. "
        "Puedes repetir el video las veces que necesites."
    )

    ruta_video = obtener_video_tutorial(ejercicio["id"])

    if os.path.exists(ruta_video):
        col_izq, col_centro, col_der = st.columns([1, 2, 1])

        with col_centro:
            st.video(ruta_video)
    else:
        st.warning("No se encontró el video tutorial de este ejercicio.")
        st.info(f"Ruta esperada: {ruta_video}")

    st.markdown("""
    ### Recomendaciones

    - Ubícate frente a la cámara.
    - Asegúrate de que se vea tu cuerpo completo.
    - Realiza el movimiento de forma lenta y controlada.
    - Detén el ejercicio si sientes dolor intenso.
    """)

    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Volver al mapa de niveles", use_container_width=True):
            st.session_state.pantalla = "mapa"
            st.rerun()

    with col2:
        if st.button("Listo para iniciar", use_container_width=True):
            st.session_state.pantalla = "ejercicio"
            st.session_state.repeticiones = 0
            st.session_state.total_repeticiones = 10
            st.session_state.tiempo_inicio = time.time()
            st.session_state.ejercicio_activo = True
            st.session_state.ejercicio_completado = False
            st.session_state.puntos_ganados_ultimo = 0
            st.rerun()