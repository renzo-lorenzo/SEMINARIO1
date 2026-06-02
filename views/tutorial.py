import streamlit as st
import time


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
        "Observa con atención la postura, el movimiento de la rodilla y la velocidad del ejercicio antes de iniciar."
    )

    # OPCIÓN 1: Video desde archivo local
    # Guarda tu video en la carpeta imagenes con el nombre tutorial_flexion.mp4
    ruta_video = "imagenes/tutorial_flexion.mp4"

    try:
        st.video(ruta_video)
    except:
        st.info("Aquí aparecerá el video tutorial cuando lo agregues en la carpeta imagenes.")

    st.markdown("""
    **Recomendaciones antes de iniciar:**

    - Mantén el cuerpo completo visible frente a la cámara.
    - Realiza el movimiento de forma lenta y controlada.
    - Evita movimientos bruscos.
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
            st.rerun()