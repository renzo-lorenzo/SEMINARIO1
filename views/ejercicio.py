import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import time


mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


def calcular_angulo(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    coseno = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    coseno = np.clip(coseno, -1.0, 1.0)

    angulo = np.degrees(np.arccos(coseno))
    return angulo


def pantalla_ejercicio():
    ejercicio = st.session_state.get("ejercicio_actual", None)

    if ejercicio is None:
        st.warning("No se seleccionó ningún ejercicio.")
        if st.button("Volver al mapa de niveles"):
            st.session_state.pantalla = "mapa"
            st.rerun()
        return

    if "repeticiones" not in st.session_state:
        st.session_state.repeticiones = 0

    if "total_repeticiones" not in st.session_state:
        st.session_state.total_repeticiones = 10

    if "tiempo_inicio" not in st.session_state:
        st.session_state.tiempo_inicio = time.time()

    st.markdown(
        f'<div class="title">{ejercicio["nombre"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="subtitle">Nivel {ejercicio["nivel_dificultad"]} - {ejercicio["objetivo"]}</div>',
        unsafe_allow_html=True
    )

    tiempo_actual = int(time.time() - st.session_state.tiempo_inicio)
    minutos = tiempo_actual // 60
    segundos = tiempo_actual % 60

    progreso = st.session_state.repeticiones / st.session_state.total_repeticiones
    porcentaje = int(progreso * 100)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{minutos:02d}:{segundos:02d}</div>
            <div class="metric-label">Temporizador</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{st.session_state.repeticiones} / {st.session_state.total_repeticiones}</div>
            <div class="metric-label">Repeticiones completadas</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{porcentaje}%</div>
            <div class="metric-label">Progreso</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Vista de cámara")

    st.info("Colócate frente a la cámara. El sistema contará una repetición cuando flexiones y vuelvas a extender la rodilla.")

    video_placeholder = st.empty()
    panel_placeholder = st.empty()

    st.markdown('</div>', unsafe_allow_html=True)

    st.progress(progreso)

    col_a, col_b, col_c = st.columns(3)

    iniciar = False

    with col_a:
        if st.button("Iniciar cámara", use_container_width=True):
            iniciar = True
            st.session_state.repeticiones = 0
            st.session_state.tiempo_inicio = time.time()

    with col_b:
        if st.button("Reiniciar ejercicio", use_container_width=True):
            st.session_state.repeticiones = 0
            st.session_state.tiempo_inicio = time.time()
            st.rerun()

    with col_c:
        if st.button("Finalizar ejercicio", use_container_width=True):
            puntos_ganados = st.session_state.repeticiones * 10
            st.session_state.puntos += puntos_ganados
            st.success(f"Ejercicio finalizado. Ganaste +{puntos_ganados} puntos.")

    col_volver1, col_volver2 = st.columns(2)

    with col_volver1:
        if st.button("Volver al tutorial", use_container_width=True):
            st.session_state.pantalla = "tutorial"
            st.rerun()

    with col_volver2:
        if st.button("Volver al mapa de niveles", use_container_width=True):
            st.session_state.pantalla = "mapa"
            st.rerun()

    if iniciar:
        ejecutar_camara(video_placeholder, panel_placeholder)


def ejecutar_camara(video_placeholder, panel_placeholder):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("No se pudo acceder a la cámara. Revisa que tu webcam esté conectada y no esté siendo usada por otra app.")
        return

    estado_movimiento = "extendido"
    repeticiones = 0
    total_repeticiones = st.session_state.total_repeticiones
    tiempo_inicio = time.time()

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:

        while cap.isOpened() and repeticiones < total_repeticiones:
            ret, frame = cap.read()

            if not ret:
                st.error("No se pudo leer la imagen de la cámara.")
                break

            frame = cv2.flip(frame, 1)

            height, width, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = pose.process(rgb)

            angulo_rodilla = None
            mensaje_estado = "Postura no detectada"

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                cadera = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
                rodilla = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
                tobillo = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]

                punto_cadera = (int(cadera.x * width), int(cadera.y * height))
                punto_rodilla = (int(rodilla.x * width), int(rodilla.y * height))
                punto_tobillo = (int(tobillo.x * width), int(tobillo.y * height))

                angulo_rodilla = calcular_angulo(
                    punto_cadera,
                    punto_rodilla,
                    punto_tobillo
                )

                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

                cv2.putText(
                    frame,
                    f"Angulo: {int(angulo_rodilla)}",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    2
                )

                if angulo_rodilla < 120 and estado_movimiento == "extendido":
                    estado_movimiento = "flexionado"
                    mensaje_estado = "Rodilla flexionada"

                elif angulo_rodilla > 150 and estado_movimiento == "flexionado":
                    estado_movimiento = "extendido"
                    repeticiones += 1
                    st.session_state.repeticiones = repeticiones
                    mensaje_estado = "Repetición completada"

                else:
                    if estado_movimiento == "extendido":
                        mensaje_estado = "Extiende y luego flexiona la rodilla"
                    else:
                        mensaje_estado = "Ahora vuelve a extender la rodilla"

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            video_placeholder.image(
                frame_rgb,
                channels="RGB",
                use_container_width=True
            )

            tiempo_actual = int(time.time() - tiempo_inicio)
            minutos = tiempo_actual // 60
            segundos = tiempo_actual % 60
            progreso = repeticiones / total_repeticiones

            with panel_placeholder.container():
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Tiempo", f"{minutos:02d}:{segundos:02d}")

                with col2:
                    st.metric("Repeticiones", f"{repeticiones} / {total_repeticiones}")

                with col3:
                    if angulo_rodilla is not None:
                        st.metric("Ángulo rodilla", f"{int(angulo_rodilla)}°")
                    else:
                        st.metric("Ángulo rodilla", "No detectado")

                st.progress(progreso)

                if results.pose_landmarks:
                    st.success(mensaje_estado)
                else:
                    st.warning("Colócate frente a la cámara para detectar el cuerpo completo.")

            time.sleep(0.03)

    cap.release()

    if repeticiones >= total_repeticiones:
        puntos_ganados = repeticiones * 10
        st.session_state.puntos += puntos_ganados
        st.success(f"Rutina completada. Ganaste +{puntos_ganados} puntos.")
        st.balloons()