import streamlit as st
import time
import os
import base64


def mostrar_video_autoplay(ruta_video, ancho="70%"):
    if not os.path.exists(ruta_video):
        st.warning("No se encontró el video tutorial.")
        return

    with open(ruta_video, "rb") as video_file:
        video_bytes = video_file.read()

    video_base64 = base64.b64encode(video_bytes).decode()

    video_html = f"""
    <div style="display: flex; justify-content: center;">
        <video width="{ancho}" autoplay muted playsinline style="border-radius: 18px;">
            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
        </video>
    </div>
    """

    st.markdown(video_html, unsafe_allow_html=True)


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
        '<div class="subtitle">Observa el tutorial antes de iniciar el ejercicio</div>',
        unsafe_allow_html=True
    )

    st.info("La cámara se activará automáticamente cuando termine el tutorial.")

    videos_tutorial = {
        1: "imagenes/tutorial_extension_rodilla.mp4",
        2: "imagenes/tutorial_elevacion_pierna.mp4",
        3: "imagenes/tutorial_mini_sentadilla.mp4",
        4: "imagenes/tutorial_puente_gluteo.mp4",
    }

    ruta_video = videos_tutorial.get(
        ejercicio["id"],
        "imagenes/tutorial_extension_rodilla.mp4"
    )

    mostrar_video_autoplay(ruta_video, ancho="70%")

    st.markdown("### Recomendaciones antes de iniciar")
    st.write("""
    - Mantén el cuerpo completo visible frente a la cámara.
    - Realiza el movimiento de forma lenta y controlada.
    - Evita movimientos bruscos.
    - Detén el ejercicio si sientes dolor intenso.
    """)

    contador = st.empty()

    duracion_tutorial = 8

    for segundos in range(duracion_tutorial, 0, -1):
        contador.info(f"El ejercicio iniciará automáticamente en {segundos} segundos...")
        time.sleep(1)

    st.session_state.ejercicio_activo = True
    st.session_state.ejercicio_completado = False
    st.session_state.puntos_ganados_ultimo = 0
    st.session_state.pantalla = "ejercicio"
    st.rerun()