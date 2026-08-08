import streamlit as st

from database.participant_repository import (
    create_participant,
    get_participant_by_id
)


def mostrar_formulario_participante():

    if "mostrar_formulario" not in st.session_state:
        st.session_state.mostrar_formulario = False

    # ==========================================
    # BOTÓN PARA ABRIR FORMULARIO
    # ==========================================

    if not st.session_state.mostrar_formulario:

        if st.button(
            "➕ Registrar nuevo participante",
            use_container_width=True
        ):

            st.session_state.mostrar_formulario = True
            st.rerun()

        return

    # ==========================================
    # FORMULARIO
    # ==========================================

    with st.container(border=True):

        st.subheader("Nuevo participante")

        nombre = st.text_input(
            "Nombre",
            key="nuevo_nombre"
        )

        apellido = st.text_input(
            "Apellido",
            key="nuevo_apellido"
        )

        edad = st.number_input(
            "Edad",
            min_value=60,
            max_value=100,
            value=65,
            key="nueva_edad"
        )

        col1, col2 = st.columns(2)

        # ==========================================
        # GUARDAR
        # ==========================================

        with col1:

            if st.button(
                "Guardar",
                use_container_width=True
            ):

                if nombre.strip() == "" or apellido.strip() == "":

                    st.warning("Complete todos los campos.")

                else:

                    participant_id = create_participant(

                        nombre.strip().title(),

                        apellido.strip().title(),

                        edad

                    )

                    participante = get_participant_by_id(participant_id)

                    nombre_completo = (
                        f"{participante['first_name']} "
                        f"{participante['last_name']}"
                    )

                    # ===============================
                    # INICIAR SESIÓN AUTOMÁTICAMENTE
                    # ===============================

                    st.session_state.logged_in = True

                    st.session_state.participant_id = participant_id

                    st.session_state.participant_name = participante["first_name"]

                    st.session_state.participant_last_name = participante["last_name"]

                    st.session_state.nombre = nombre_completo

                    st.session_state.edad = participante["age"]

                    st.session_state.puntos = 0

                    st.session_state.nivel = 1

                    st.session_state.mostrar_formulario = False

                    st.rerun()

        # ==========================================
        # CANCELAR
        # ==========================================

        with col2:

            if st.button(
                "Cancelar",
                use_container_width=True
            ):

                st.session_state.mostrar_formulario = False

                st.rerun()