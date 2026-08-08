import streamlit as st

from utils.ejercicios import (
    obtener_ejercicios,
    obtener_nombre_nivel,
    ejercicio_desbloqueado
)

from components.exercise_video_preview import mostrar_video_preview


def pantalla_mapa_niveles():

    st.markdown(
        "Mapa de ejercicios",
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Elige un ejercicio y comienza a moverte</div>',
        unsafe_allow_html=True
    )

    puntos_usuario = st.session_state.puntos
    ejercicios = obtener_ejercicios()

    st.info(
        f"Participante: "
        f"{st.session_state.participant_name} "
        f"{st.session_state.participant_last_name} | "
        f"Puntos: {puntos_usuario}"
    )

    # ==========================================
    # NIVELES
    # ==========================================

    for nivel in [1, 2, 3]:

        st.markdown(
            f"## {obtener_nombre_nivel(nivel)}"
        )

        ejercicios_nivel = [
            ejercicio
            for ejercicio in ejercicios
            if ejercicio["nivel_dificultad"] == nivel
        ]

        columnas = st.columns(3)

        # ==========================================
        # EJERCICIOS DEL NIVEL
        # ==========================================

        for index, ejercicio in enumerate(ejercicios_nivel):

            desbloqueado = ejercicio_desbloqueado(
                ejercicio,
                puntos_usuario
            )

            with columnas[index % 3]:

                # ==================================
                # EJERCICIO DESBLOQUEADO
                # ==================================

                if desbloqueado:

                    st.success(
                        f"🟢 {ejercicio['nombre']}"
                    )

                    # Vista previa del ejercicio
                    mostrar_video_preview(
                        ejercicio["video"],
                        key=f"video_{ejercicio['id']}"
                    )

                    st.write(
                        ejercicio["descripcion"]
                    )

                    st.caption(
                        f"Objetivo: {ejercicio['objetivo']}"
                    )

                    st.caption(
                        f"Requiere: {ejercicio['puntos_requeridos']} puntos"
                    )

                    if st.button(
                        f"Iniciar ejercicio {ejercicio['id']}",
                        key=f"iniciar_{nivel}_{index}_{ejercicio['id']}",
                        use_container_width=True
                    ):

                        st.session_state.ejercicio_actual = ejercicio
                        st.session_state.pantalla = "tutorial"
                        st.rerun()

                # ==================================
                # EJERCICIO BLOQUEADO
                # ==================================

                else:

                    st.warning(
                        f"🔒 {ejercicio['nombre']}"
                    )

                    # También mostramos el video
                    # para que el participante pueda
                    # conocer el ejercicio.
                    mostrar_video_preview(
                        ejercicio["video"],
                        key=f"video_{ejercicio['id']}"
                    )

                    st.write(
                        ejercicio["descripcion"]
                    )

                    st.caption(
                        f"Requiere: {ejercicio['puntos_requeridos']} puntos"
                    )

                    puntos_faltantes = (
                        ejercicio["puntos_requeridos"]
                        - puntos_usuario
                    )

                    st.caption(
                        f"Te faltan {puntos_faltantes} "
                        f"puntos para desbloquearlo."
                    )

        st.divider()

    # ==========================================
    # VOLVER AL INICIO
    # ==========================================

    if st.button(
        "← Volver al inicio",
        use_container_width=False
    ):

        st.session_state.pantalla = "dashboard"
        st.rerun()