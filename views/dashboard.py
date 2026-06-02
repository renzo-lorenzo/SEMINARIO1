import streamlit as st

def pantalla_dashboard():
    st.markdown(f'<div class="title">Hola, {st.session_state.nombre}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Bienvenido, continúa tu progreso de rehabilitación de rodilla</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="level-box">
        <div class="level-title">Nivel 1: Movilidad Inicial</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{st.session_state.puntos}</div>
            <div class="metric-label">Puntos acumulados</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{st.session_state.nivel}</div>
            <div class="metric-label">Nivel actual</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{st.session_state.dolor}/10</div>
            <div class="metric-label">Dolor inicial</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-number">0%</div>
            <div class="metric-label">Progreso semanal</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    col_a, col_b = st.columns([1.2, 1])

    with col_a:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Rutina recomendada de hoy")
        st.write("Completa una sesión corta de ejercicios guiados para avanzar en tu progreso.")

        st.markdown("""
        **Ejercicio 1:** Flexión controlada de rodilla  
        **Ejercicio 2:** Sentadilla asistida  
        **Ejercicio 3:** Extensión suave de pierna  
        """)

        st.progress(0.0)

        if st.button("Ver mapa de rehabilitación", use_container_width=True):
            st.session_state.pantalla = "mapa"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Recompensas:")

        st.markdown("""
        🟢 **+10 puntos** por completar una repetición válida  
        🟡 **+25 puntos** por mantener buena postura  
        🔵 **+50 puntos** por completar la rutina diaria  
        🏆 **Nuevo nivel** al llegar a 300 puntos  
        """)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Mapa de niveles")

    col_n1, col_n2, col_n3 = st.columns(3)

    with col_n1:
        st.success("Nivel 1: Movilidad inicial\n\nFlexión suave y postura básica")

    with col_n2:
        st.info("Nivel 2: Control y estabilidad\n\nMayor precisión del movimiento")

    with col_n3:
        st.warning("Nivel 3: Fuerza funcional\n\nRutinas más completas")

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.rerun()