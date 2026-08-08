import streamlit as st

from database.participant_repository import delete_participant


def mostrar_tarjeta_participante(participante):

    nombre = f"{participante['first_name']} {participante['last_name']}"
    edad = participante["age"]

    with st.container(border=True):

        # ============================================
        # ENCABEZADO
        # ============================================

        col_info, col_start, col_menu = st.columns(
            [7.2, 1.6, 0.2],
            vertical_alignment="center"
        )

        # ============================================
        # INFORMACIÓN
        # ============================================

        with col_info:

            st.markdown(f"### 👤 {nombre}")
            st.caption(f"Edad: {edad} años")

        # ============================================
        # BOTÓN COMENZAR
        # ============================================

        with col_start:

            if st.button(
                "▶ Comenzar",
                key=f"start_{participante['id']}",
                use_container_width=True
            ):

                st.session_state.logged_in = True

                st.session_state.participant_id = participante["id"]
                st.session_state.participant_name = participante["first_name"]
                st.session_state.participant_last_name = participante["last_name"]

                st.session_state.nombre = nombre
                st.session_state.edad = edad

                st.session_state.puntos = 0
                st.session_state.nivel = 1

                st.rerun()

        # ============================================
        # MENÚ
        # ============================================

        with col_menu:

            with st.popover("⋮"):

                st.write("### Opciones")

                if st.button(
                    "🗑 Eliminar participante",
                    key=f"delete_{participante['id']}",
                    use_container_width=True
                ):

                    st.session_state.confirm_delete = participante["id"]

        # ============================================
        # CONFIRMACIÓN DE ELIMINACIÓN
        # ============================================

        if st.session_state.get("confirm_delete") == participante["id"]:

            st.warning(
                f"¿Está seguro de eliminar al participante **{nombre}**?"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Cancelar",
                    key=f"cancel_{participante['id']}",
                    use_container_width=True
                ):

                    st.session_state.confirm_delete = None
                    st.rerun()

            with col2:

                if st.button(
                    "Eliminar",
                    key=f"confirm_{participante['id']}",
                    use_container_width=True
                ):

                    delete_participant(participante["id"])

                    st.session_state.confirm_delete = None

                    st.success("Participante eliminado correctamente.")

                    st.rerun()