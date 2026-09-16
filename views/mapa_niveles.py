import streamlit as st

from utils.ejercicios import (
    obtener_ejercicios,
    obtener_nombre_nivel,
    obtener_costo_ejercicio,
    obtener_nivel_actual_por_ejercicios,
    ejercicio_desbloqueado
)

from components.exercise_video_preview import (
    mostrar_video_preview
)

from database.participant_repository import (
    get_exercise_repetitions,
    set_exercise_repetitions,
    get_total_points_by_participant,
    get_total_spent_points_by_participant,
    get_unlocked_exercises_by_participant,
    unlock_exercise_for_participant
)

def sincronizar_progreso_participante(participant_id):

    puntos_guardados = get_total_points_by_participant(
        participant_id
    )

    puntos_gastados = get_total_spent_points_by_participant(
        participant_id
    )

    puntos_sesion_actual = sum(
        ejercicio.get("puntos", 0)
        for ejercicio in st.session_state.get(
            "ejercicios_pendientes",
            []
        )
    )

    ejercicios_desbloqueados = get_unlocked_exercises_by_participant(
        participant_id
    )

    puntos_ganados_total = (
        puntos_guardados + puntos_sesion_actual
    )

    puntos_disponibles = max(
        puntos_ganados_total - puntos_gastados,
        0
    )

    st.session_state.puntos_ganados_total = puntos_ganados_total

    st.session_state.puntos_guardados = puntos_guardados

    st.session_state.puntos_sesion_actual = puntos_sesion_actual

    st.session_state.puntos_gastados = puntos_gastados

    st.session_state.puntos = puntos_disponibles

    st.session_state.ejercicios_desbloqueados = ejercicios_desbloqueados

    st.session_state.nivel = obtener_nivel_actual_por_ejercicios(
        ejercicios_desbloqueados
    )

    return st.session_state.puntos, ejercicios_desbloqueados


def mostrar_boton_desbloqueo_ejercicio(
    participant_id,
    ejercicio,
    puntos_usuario,
    ejercicios_desbloqueados
):

    if ejercicio_desbloqueado(
        ejercicio,
        ejercicios_desbloqueados
    ):

        return

    costo_ejercicio = obtener_costo_ejercicio(
        ejercicio
    )

    if puntos_usuario >= costo_ejercicio:

        st.info(
            f"Tienes {puntos_usuario} estrellas disponibles. "
            f"Puedes desbloquear este ejercicio por {costo_ejercicio} estrellas."
        )

        if st.button(
            f"🔓 Desbloquear por {costo_ejercicio} estrellas",
            key=f"desbloquear_ejercicio_{ejercicio['id']}_{participant_id}",
            use_container_width=True,
            type="primary"
        ):

            desbloqueado = unlock_exercise_for_participant(
                participant_id,
                ejercicio["id"],
                costo_ejercicio
            )

            if desbloqueado:

                st.success(
                    f"{ejercicio['nombre']} desbloqueado correctamente."
                )

                st.rerun()

            else:

                st.warning(
                    "Este ejercicio ya fue desbloqueado anteriormente."
                )

    else:

        puntos_faltantes = costo_ejercicio - puntos_usuario

        st.warning(
            f"Te faltan {puntos_faltantes} estrellas para desbloquear este ejercicio."
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

    puntos_usuario, ejercicios_desbloqueados = sincronizar_progreso_participante(
        participant_id
    )

    ejercicios = obtener_ejercicios()

    st.info(
        f"Participante: "
        f"{st.session_state.participant_name} "
        f"{st.session_state.participant_last_name} | "
        f"Estrellas disponibles: {puntos_usuario} | "
        f"Nivel máximo alcanzado: {st.session_state.nivel}"
    )

    # ==========================================
    # NIVELES SOLO COMO AGRUPACIÓN VISUAL
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
                ejercicios_desbloqueados
            )

            with columnas[index % 3]:

                # ==================================
                # EJERCICIO DESBLOQUEADO
                # ==================================

                if desbloqueado:

                    st.success(
                        f"🟢 {ejercicio['nombre']}"
                    )

                    mostrar_video_preview(
                        ejercicio["video"],
                        key=f"video_{ejercicio['id']}"
                    )

                    st.write(
                        ejercicio["descripcion"]
                    )

                    st.caption(
                        f"Objetivo: "
                        f"{ejercicio['objetivo']}"
                    )

                    st.caption(
                        f"Ejercicio desbloqueado · Nivel {ejercicio['nivel_dificultad']}"
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

                        ejercicio_actual = ejercicio.copy()

                        ejercicio_actual["repeticiones_objetivo"] = repeticiones

                        st.session_state.ejercicio_actual = ejercicio_actual

                        st.session_state.repeticiones_objetivo = repeticiones

                        st.session_state.pantalla = "tutorial"

                        st.rerun()

                # ==================================
                # EJERCICIO BLOQUEADO
                # ==================================

                else:

                    st.warning(
                        f"🔒 {ejercicio['nombre']}"
                    )

                    mostrar_video_preview(
                        ejercicio["video"],
                        key=f"video_{ejercicio['id']}"
                    )

                    st.write(
                        ejercicio["descripcion"]
                    )

                    st.caption(
                        f"Nivel {ejercicio['nivel_dificultad']} · "
                        f"Costo: {obtener_costo_ejercicio(ejercicio)} estrellas"
                    )

                    mostrar_boton_desbloqueo_ejercicio(
                        participant_id,
                        ejercicio,
                        puntos_usuario,
                        ejercicios_desbloqueados
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