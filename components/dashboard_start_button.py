import streamlit as st


def mostrar_boton_comenzar():

    st.markdown(
        """
        <style>

        div[data-testid="stButton"] button[kind="primary"] {
            min-height: 90px;
            font-size: 28px !important;
            font-weight: 700 !important;
            border-radius: 18px !important;

            background-color: #2e8b57 !important;
            border-color: #2e8b57 !important;
            color: white !important;
        }

        div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: #267349 !important;
            border-color: #267349 !important;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "▶  COMENZAR EJERCICIOS",
        use_container_width=True,
        type="primary"
    ):

        st.session_state.pantalla = "mapa"

        st.rerun()