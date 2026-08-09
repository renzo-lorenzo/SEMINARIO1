import streamlit as st

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from database.participant_repository import (
    get_session_count,
    register_session_with_exercises,
    cancel_last_session,
    get_session_history,
    delete_session
)


# ==================================================
# CONVERTIR FECHA A HORA DE PERÚ
# ==================================================

def convertir_hora_peru(session_date):

    if session_date is None:
        return None

    try:

        fecha = datetime.fromisoformat(
            str(session_date)
        )

        if fecha.tzinfo is None:
            fecha = fecha.replace(
                tzinfo=ZoneInfo("UTC")
            )

        return fecha.astimezone(
            ZoneInfo("America/Lima")
        )

    except (ValueError, TypeError):

        return None

# ==================================================
# DIÁLOGO: REGISTRAR SESIÓN
# ==================================================

@st.dialog("Registrar sesión")
def confirmar_registro_sesion(participant_id):

    ejercicios_pendientes = (
        st.session_state.get(
            "ejercicios_pendientes",
            []
        )
    )

    st.write(
        "¿Está seguro de que desea registrar esta sesión "
        "para este participante?"
    )

    st.write(
        f"Ejercicios realizados en esta sesión: "
        f"**{len(ejercicios_pendientes)}**"
    )

    st.write(
        "Al registrar la sesión, todos los ejercicios "
        "realizados hasta este momento quedarán guardados "
        "en el historial."
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Cancelar",
            use_container_width=True
        ):

            st.rerun()

    with col2:

        if st.button(
            "Sí, registrar",
            type="primary",
            use_container_width=True
        ):

            # ==========================================
            # REGISTRAR SESIÓN + EJERCICIOS
            # ==========================================

            register_session_with_exercises(
                participant_id,
                ejercicios_pendientes
            )

            # ==========================================
            # LIMPIAR EJERCICIOS DE LA SESIÓN ACTUAL
            # ==========================================

            st.session_state.ejercicios_pendientes = []

            st.success(
                "Sesión registrada correctamente."
            )

            st.rerun()


# ==================================================
# DIÁLOGO: ANULAR SESIÓN
# ==================================================

@st.dialog("Anular última sesión")
def confirmar_anulacion_sesion(participant_id):

    st.write(
        "¿Está seguro de que desea anular la última "
        "sesión registrada?"
    )

    st.warning(
        "La sesión no será eliminada. Quedará registrada "
        "como anulada en el historial."
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Cancelar",
            use_container_width=True
        ):

            st.rerun()

    with col2:

        if st.button(
            "Sí, anular",
            type="primary",
            use_container_width=True
        ):

            resultado = cancel_last_session(
                participant_id
            )

            if resultado:

                st.success(
                    "La última sesión fue anulada correctamente."
                )

            st.rerun()


# ==================================================
# DIÁLOGO: HISTORIAL DE SESIONES
# ==================================================

@st.dialog("Historial de sesiones")
def mostrar_historial_sesiones(participant_id):

    historial = get_session_history(
        participant_id
    )

    if not historial:

        st.info(
            "Todavía no hay sesiones registradas "
            "para este participante."
        )

        return

    st.write(
        "Aquí se muestran las sesiones registradas "
        "y las sesiones que hayan sido anuladas."
    )

    st.divider()

    # ==================================================
    # RECORRER HISTORIAL
    # ==================================================

    for session in historial:

        session_id = session[0]
        session_date = session[1]
        status = session[2]

        # ------------------------------------------
        # FECHA Y HORA
        # ------------------------------------------

        fecha_peru = convertir_hora_peru(session_date)

        if fecha_peru is not None:

            fecha = fecha_peru.strftime(
                "%d/%m/%Y"
            )

            hora = fecha_peru.strftime(
                "%H:%M"
            )

        else:

            fecha = "Fecha no disponible"
            hora = "Hora no disponible"

        # ------------------------------------------
        # ESTADO
        # ------------------------------------------

        if status == "active":

            estado = "🟢 Sesión realizada"

        else:

            estado = "🔴 Sesión anulada"

        # ------------------------------------------
        # INFORMACIÓN + ELIMINAR
        # ------------------------------------------

        col_info, col_delete = st.columns(
            [7, 1]
        )

        with col_info:

            st.markdown(
                f"""
                **{fecha} — {hora}**

                {estado}
                """
            )

        with col_delete:

            if st.button(
                "🗑️",
                key=f"delete_session_{session_id}",
                help="Eliminar registro"
            ):

                delete_session(
                    session_id
                )

                st.rerun()

        # ------------------------------------------
        # SEPARADOR
        # ------------------------------------------

        st.divider()


# ==================================================
# DASHBOARD STATS
# ==================================================

def mostrar_dashboard_stats():

    # ==================================================
    # ESTILOS
    # ==================================================

    st.markdown(
        """
        <style>

        /* ==========================================
           TÍTULO DETALLES
           ========================================== */

        .details-title {
            font-size: 30px;
            font-weight: 600;
            color: #111827;
            margin-bottom: 12px;
        }


        /* ==========================================
           TÍTULO PROGRESO
           ========================================== */

        .progress-title {
            text-align: center;
            font-size: 30px;
            font-weight: 600;
            color: #555555;
            margin-bottom: 10px;
        }


        /* ==========================================
        BOTONES DEL MENÚ DE SESIONES
        ========================================== */

        div[data-testid="stPopoverBody"] button {
            background-color: transparent !important;
            color: #333333 !important;

            border: 1px solid #CFCFCF !important;
            border-radius: 8px !important;

            box-shadow: none !important;
        }

        /* ==========================================
        HOVER
        ========================================== */

        div[data-testid="stPopoverBody"] button:hover {
            background-color: #F3F4F6 !important;
            color: #222222 !important;

            border-color: #AAAAAA !important;

            box-shadow: none !important;
        }


        /* ==========================================
           EFECTO AL PASAR EL MOUSE
           ========================================== */

        div[data-testid="stPopover"] button:hover {
            background-color: #f2f2f2 !important;

            border-color: #b8b8b8 !important;

            color: #222222 !important;
        }


        /* ==========================================
           BOTÓN DE CERRAR EL POPOVER
           ========================================== */

        div[data-testid="stPopover"] > div > button {
            background-color: transparent !important;

            border: 1px solid #d0d0d0 !important;

            color: #333333 !important;
        }


        </style>
        """,
        unsafe_allow_html=True
    )


    # ==================================================
    # PARTICIPANTE ACTUAL
    # ==================================================

    participant_id = st.session_state.participant_id

    sesiones = get_session_count(
        participant_id
    )


    # ==================================================
    # COLUMNAS PRINCIPALES
    # ==================================================

    col_details, col_progress = st.columns(
        [0.75, 1.4]
    )


    # ==================================================
    # DETALLES
    # ==================================================

    with col_details:

        st.markdown(
            '<div class="details-title">DETALLES:</div>',
            unsafe_allow_html=True
        )


        with st.container(border=True):

            # ==========================================
            # ESTRELLAS
            # ==========================================

            st.markdown("### ⭐ Estrellas")

            st.markdown(
                f"## {st.session_state.puntos}"
            )


            # ==========================================
            # NIVEL
            # ==========================================

            st.markdown("### 🌱 Nivel actual")

            st.markdown(
                f"## {st.session_state.nivel}"
            )


            # ==========================================
            # SESIONES
            # ==========================================

            col_session, col_menu = st.columns(
                [5, 1]
            )


            with col_session:

                st.markdown("### 📅 Sesiones")

                st.markdown(
                    f"## {sesiones}"
                )


            with col_menu:

                st.markdown("")


                # ======================================
                # MENÚ DE SESIONES
                # ======================================
                with st.popover("⋮"):

                    st.markdown("### Sesiones")

                    if st.button(
                        "Registrar sesión",
                        key="registrar_sesion_menu",
                        use_container_width=True,
                        type="secondary"
                    ):
                        confirmar_registro_sesion(
                            participant_id
                        )

                    if sesiones > 0:

                        if st.button(
                            "Anular última sesión",
                            key="anular_sesion_menu",
                            use_container_width=True,
                            type="secondary"
                        ):
                            confirmar_anulacion_sesion(
                                participant_id
                            )

                    if st.button(
                        "Ver historial",
                        key="ver_historial_menu",
                        use_container_width=True,
                        type="secondary"
                    ):
                        mostrar_historial_sesiones(
                            participant_id
                        )


    # ==================================================
    # PROGRESO
    # ==================================================

    with col_progress:

        st.markdown(
            '<div class="progress-title">TU PROGRESO</div>',
            unsafe_allow_html=True
        )


        st.html(
            """
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                height: 280px;
            ">

                <div style="
                    width: 230px;
                    height: 230px;
                    border-radius: 50%;

                    background: conic-gradient(
                        #2e8b57 0deg,
                        #e5e7eb 0deg
                    );

                    display: flex;
                    justify-content: center;
                    align-items: center;
                ">

                    <div style="
                        width: 165px;
                        height: 165px;
                        border-radius: 50%;

                        background: white;

                        display: flex;
                        justify-content: center;
                        align-items: center;

                        font-size: 34px;
                        font-weight: 600;

                        color: #333333;
                    ">

                        0%

                    </div>

                </div>

            </div>
            """
        )