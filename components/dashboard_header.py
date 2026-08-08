import streamlit as st


def mostrar_dashboard_header():

    st.title(f"👋 Hola, {st.session_state.nombre}")

    st.markdown(
        """
        <div style='font-size:22px;
                    color:#666;
                    margin-bottom:25px;'>

        ¡Nos alegra verte nuevamente!

        </div>
        """,
        unsafe_allow_html=True
    )