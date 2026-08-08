import streamlit as st


def mostrar_logout():

    st.divider()

    col1, col2, col3 = st.columns([5, 1, 0.1])

    with col2:

        st.markdown(
            """
            <style>

            div[data-testid="stButton"]:has(button[kind="secondary"]) button {
                min-height: 45px !important;
                border-radius: 10px !important;
                font-size: 16px !important;
                background-color: #d9534f !important;
                border-color: #d9534f !important;
                color: white !important;
            }

            div[data-testid="stButton"]:has(button[kind="secondary"]) button:hover {
                background-color: #c9302c !important;
                border-color: #c9302c !important;
                color: white !important;
            }

            </style>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Cerrar sesión",
            use_container_width=True,
            type="secondary"
        ):

            st.session_state.logged_in = False

            st.session_state.participant_id = None

            st.session_state.participant_name = ""

            st.session_state.participant_last_name = ""

            st.session_state.nombre = ""

            st.session_state.edad = 0

            st.session_state.puntos = 0

            st.session_state.nivel = 1

            st.session_state.pantalla = "dashboard"

            st.rerun()