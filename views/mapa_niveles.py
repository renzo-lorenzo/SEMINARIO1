import streamlit as st

from utils.ejercicios import (
    obtener_ejercicios,
    obtener_nombre_nivel,
    ejercicio_desbloqueado
)

from components.exercise_video_preview import (
    mostrar_video_preview
)

from database.participant_repository import (
    get_exercise_repetitions,
    set_exercise_repetitions
)


def pantalla_mapa_niveles():

    st.markdown(
        "Mapa de ejercicios",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="subtitle">
            Elige un ejercicio y comienza a moverte
        </div>
        """,
        unsafe_allow_html=True
    )

    # ==========================================
    # DATOS DEL PARTICIPANTE
    # ==========================================

    participant_id = st.session_state.participant_id

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
        # EJERCICIOS
        # ==========================================

        for index, ejercicio in enumerate(
            ejercicios_nivel
        ):

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

                    # ----------------------------------
                    # VIDEO
                    # ----------------------------------

                    mostrar_video_preview(
                        ejercicio["video"],
                        key=f"video_{ejercicio['id']}"
                    )

                    # ----------------------------------
                    # DESCRIPCIÓN
                    # ----------------------------------

                    st.write(
                        ejercicio["descripcion"]
                    )

                    st.caption(
                        f"Objetivo: "
                        f"{ejercicio['objetivo']}"
                    )

                    # ----------------------------------
                    # PUNTOS
                    # ----------------------------------

                    st.caption(
                        f"Requiere: "
                        f"{ejercicio['puntos_requeridos']} "
                        f"puntos"
                    )

                    # ----------------------------------
                    # REPETICIONES
                    # ----------------------------------

                    repeticiones = (
                        get_exercise_repetitions(
                            participant_id,
                            ejercicio["id"],
                            ejercicio[
                                "repeticiones_objetivo"
                            ]
                        )
                    )

                    st.markdown(
                        """
                        <div style="
                            text-align: center;
                            font-size: 18px;
                            font-weight: 600;
                            margin-top: 10px;
                            margin-bottom: 5px;
                        ">
                            Repeticiones
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    col_minus, col_value, col_plus = (
                        st.columns([1, 1.5, 1])
                    )

                    with col_minus:

                        if st.button(
                            "−",
                            key=(
                                f"minus_"
                                f"{participant_id}_"
                                f"{ejercicio['id']}"
                            ),
                            use_container_width=True
                        ):

                            nuevas_repeticiones = max(
                                1,
                                repeticiones - 1
                            )

                            set_exercise_repetitions(
                                participant_id,
                                ejercicio["id"],
                                nuevas_repeticiones
                            )

                            st.rerun()

                    with col_value:

                        st.markdown(
                            f"""
                            <div style="
                                text-align: center;
                                font-size: 26px;
                                font-weight: 700;
                                padding: 5px;
                            ">
                                {repeticiones}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col_plus:

                        if st.button(
                            "+",
                            key=(
                                f"plus_"
                                f"{participant_id}_"
                                f"{ejercicio['id']}"
                            ),
                            use_container_width=True
                        ):

                            nuevas_repeticiones = min(
                                100,
                                repeticiones + 1
                            )

                            set_exercise_repetitions(
                                participant_id,
                                ejercicio["id"],
                                nuevas_repeticiones
                            )

                            st.rerun()

                    # ----------------------------------
                    # INICIAR EJERCICIO
                    # ----------------------------------

                    if st.button(
                        f"Iniciar ejercicio "
                        f"{ejercicio['id']}",
                        key=(
                            f"iniciar_"
                            f"{nivel}_"
                            f"{index}_"
                            f"{ejercicio['id']}"
                        ),
                        use_container_width=True
                    ):

                        # ==========================================
                        # GUARDAR EJERCICIO ACTUAL
                        # ==========================================

                        ejercicio_actual = ejercicio.copy()

                        # Usar la cantidad de repeticiones
                        # configurada por la fisioterapeuta
                        ejercicio_actual["repeticiones_objetivo"] = repeticiones

                        st.session_state.ejercicio_actual = ejercicio_actual

                        # También la dejamos disponible en session_state
                        st.session_state.repeticiones_objetivo = repeticiones

                        st.session_state.pantalla = "tutorial"

                        st.rerun()

                        st.session_state.pantalla = (
                            "tutorial"
                        )

                        st.rerun()

                # ==================================
                # EJERCICIO BLOQUEADO
                # ==================================

                else:

                    st.warning(
                        f"🔒 {ejercicio['nombre']}"
                    )

                    # ----------------------------------
                    # VIDEO
                    # ----------------------------------

                    mostrar_video_preview(
                        ejercicio["video"],
                        key=f"video_{ejercicio['id']}"
                    )

                    # ----------------------------------
                    # DESCRIPCIÓN
                    # ----------------------------------

                    st.write(
                        ejercicio["descripcion"]
                    )

                    # ----------------------------------
                    # PUNTOS
                    # ----------------------------------

                    st.caption(
                        f"Requiere: "
                        f"{ejercicio['puntos_requeridos']} "
                        f"puntos"
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