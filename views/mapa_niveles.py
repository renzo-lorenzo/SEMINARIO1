import streamlit as st
from utils.ejercicios import (
    obtener_ejercicios,
    obtener_nombre_nivel,
    ejercicio_desbloqueado
)


def pantalla_mapa_niveles():
    st.markdown(
        '<div class="title">Mapa de rehabilitación</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Avanza ejercicio por ejercicio y desbloquea nuevas rutinas</div>',
        unsafe_allow_html=True
    )

    puntos_usuario = st.session_state.puntos
    ejercicios = obtener_ejercicios()

    st.info(
        f"Paciente: {st.session_state.nombre} | "
        f"Experiencia: {st.session_state.experiencia} | "
        f"Puntos actuales: {puntos_usuario}"
    )

    for nivel in [1, 2, 3]:
        st.markdown(f"## {obtener_nombre_nivel(nivel)}")

        ejercicios_nivel = [
            ejercicio for ejercicio in ejercicios
            if ejercicio["nivel_dificultad"] == nivel
        ]

        columnas = st.columns(3)

        for index, ejercicio in enumerate(ejercicios_nivel):
            desbloqueado = ejercicio_desbloqueado(
                ejercicio,
                puntos_usuario
            )

            with columnas[index % 3]:
                if desbloqueado:
                    st.success(f"🟢 {ejercicio['nombre']}")
                    st.write(ejercicio["descripcion"])
                    st.caption(f"Objetivo: {ejercicio['objetivo']}")
                    st.caption(
                        f"Requiere: {ejercicio['puntos_requeridos']} puntos"
                    )



                    if st.button(
                        f"Iniciar ejercicio {ejercicio['id']}",
                        key=f"iniciar_{ejercicio['id']}",
                        use_container_width=True
                    ):
                        st.session_state.ejercicio_actual = ejercicio
                        st.session_state.pantalla = "tutorial"
                        st.rerun()

                else:
                    st.warning(f"🔒 {ejercicio['nombre']}")
                    st.write(ejercicio["descripcion"])
                    st.caption(
                        f"Requiere: {ejercicio['puntos_requeridos']} puntos"
                    )
                    st.caption(
                        f"Te faltan {ejercicio['puntos_requeridos'] - puntos_usuario} puntos para desbloquearlo."
                    )

        st.divider()

    if st.button("Volver al dashboard"):
        st.session_state.pantalla = "dashboard"
        st.rerun()