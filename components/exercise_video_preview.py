import streamlit as st
import base64
from pathlib import Path


def mostrar_video_preview(video_path, key):
    """
    Muestra una vista previa pequeña del video.

    Comportamiento:
    - El video permanece pausado inicialmente.
    - Al colocar el mouse encima, comienza a reproducirse.
    - Se reproduce en bucle.
    - No tiene sonido.
    - Al retirar el mouse, vuelve a pausarse.
    """

    ruta = Path(video_path)

    if not ruta.exists():
        st.warning(f"No se encontró el video: {video_path}")
        return

    try:
        video_bytes = ruta.read_bytes()
        video_base64 = base64.b64encode(video_bytes).decode()

        video_html = f"""
        <div
            class="exercise-video-preview"
            onmouseenter="this.querySelector('video').play()"
            onmouseleave="this.querySelector('video').pause()"
        >
            <video
                muted
                loop
                playsinline
                preload="metadata"
            >
                <source
                    src="data:video/mp4;base64,{video_base64}"
                    type="video/mp4"
                >
            </video>
        </div>

        <style>
            .exercise-video-preview {{
                width: 100%;
                height: 150px;
                overflow: hidden;
                border-radius: 10px;
                margin: 10px 0 15px 0;
                background-color: #f1f5f9;
                cursor: pointer;
            }}

            .exercise-video-preview video {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            }}

            .exercise-video-preview:hover {{
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
            }}
        </style>
        """

        st.components.v1.html(
            video_html,
            height=180,
            scrolling=False
        )

    except Exception as e:
        st.warning(f"No se pudo cargar el video: {e}")