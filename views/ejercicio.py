import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import time
import os
import base64


mp_pose = mp.solutions.pose


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


def mostrar_video_loop(ruta_video):
    if not os.path.exists(ruta_video):
        st.warning("No se encontró la animación del ejercicio.")
        return

    with open(ruta_video, "rb") as video_file:
        video_bytes = video_file.read()

    video_base64 = base64.b64encode(video_bytes).decode()

    video_html = f"""
    <video width="100%" autoplay loop muted playsinline style="border-radius: 16px;">
        <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
    </video>
    """

    st.markdown(video_html, unsafe_allow_html=True)


def pantalla_ejercicio():
    ejercicio = st.session_state.get("ejercicio_actual", None)

    if ejercicio is None:
        st.warning("No se seleccionó ningún ejercicio.")
        if st.button("Volver al mapa"):
            st.session_state.pantalla = "mapa"
            st.rerun()
        return

    st.markdown(
        f'<div class="title">{ejercicio["nombre"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="subtitle">Nivel {ejercicio["nivel_dificultad"]} - {ejercicio["objetivo"]}</div>',
        unsafe_allow_html=True
    )

    st.info("Ubícate frente a la cámara. El sistema analizará tu movimiento automáticamente.")

    col_camara, col_derecha = st.columns([2.2, 1])

    with col_camara:
        st.subheader("Cámara del paciente")
        camara_placeholder = st.empty()

    with col_derecha:
        st.subheader("Animación guía")
        animacion_placeholder = st.empty()

        st.subheader("Resultados")
        resultados_placeholder = st.empty()

    with animacion_placeholder.container():
        mostrar_video_loop("imagenes/tutorial_flexion.mp4")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("No se pudo activar la cámara.")
        return

    repeticiones = 0
    total_repeticiones = 10
    puntos_ganados = 0

    estado_movimiento = "extendido"
    angulo_actual = 0
    angulo_minimo = 999
    angulo_maximo = 0
    angulos = []

    tiempo_inicio = time.time()
    duracion_maxima = 60

    detener = st.button("Detener ejercicio", use_container_width=True)

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:

        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                st.error("No se pudo leer la cámara.")
                break

            frame = cv2.flip(frame, 1)
            height, width, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            mensaje = "Colócate de lado y muestra cuerpo completo"

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                cadera = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
                rodilla = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
                tobillo = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]

                punto_cadera = (int(cadera.x * width), int(cadera.y * height))
                punto_rodilla = (int(rodilla.x * width), int(rodilla.y * height))
                punto_tobillo = (int(tobillo.x * width), int(tobillo.y * height))

                angulo_actual = calcular_angulo(
                    punto_cadera,
                    punto_rodilla,
                    punto_tobillo
                )

                angulos.append(angulo_actual)
                angulo_minimo = min(angulo_minimo, angulo_actual)
                angulo_maximo = max(angulo_maximo, angulo_actual)

                cv2.line(frame, punto_cadera, punto_rodilla, (255, 255, 255), 4)
                cv2.line(frame, punto_rodilla, punto_tobillo, (255, 255, 255), 4)

                cv2.circle(frame, punto_cadera, 8, (0, 0, 255), -1)
                cv2.circle(frame, punto_rodilla, 10, (0, 255, 255), -1)
                cv2.circle(frame, punto_tobillo, 8, (0, 0, 255), -1)

                cv2.putText(
                    frame,
                    f"{int(angulo_actual)} grados",
                    (punto_rodilla[0] + 20, punto_rodilla[1] + 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )

                if angulo_actual < 120 and estado_movimiento == "extendido":
                    estado_movimiento = "flexionado"
                    mensaje = "Buena flexión, ahora vuelve lentamente"

                elif angulo_actual > 150 and estado_movimiento == "flexionado":
                    estado_movimiento = "extendido"
                    repeticiones += 1
                    puntos_ganados += 10
                    mensaje = "Repetición válida"

                else:
                    mensaje = "Sigue el movimiento de forma controlada"

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            camara_placeholder.image(
                frame_rgb,
                channels="RGB",
                use_container_width=True
            )

            tiempo_actual = int(time.time() - tiempo_inicio)
            progreso = min(repeticiones / total_repeticiones, 1.0)

            if angulos:
                promedio = round(sum(angulos) / len(angulos), 2)
                min_texto = round(angulo_minimo, 2)
                max_texto = round(angulo_maximo, 2)
            else:
                promedio = "-"
                min_texto = "-"
                max_texto = "-"

            with resultados_placeholder.container():
                st.metric("Repeticiones", f"{repeticiones}/{total_repeticiones}")
                st.progress(progreso)

                st.metric("Ángulo actual", f"{round(angulo_actual, 2)}°")
                st.write(f"**Estado:** {estado_movimiento}")
                st.write(f"**Retroalimentación:** {mensaje}")

                st.divider()

                st.write(f"**Ángulo mínimo:** {min_texto}°")
                st.write(f"**Ángulo máximo:** {max_texto}°")
                st.write(f"**Promedio:** {promedio}°")

                st.divider()

                st.metric("Puntos ganados", puntos_ganados)
                st.write(f"**Tiempo:** {tiempo_actual} segundos")

            if repeticiones >= total_repeticiones:
                st.session_state.puntos += puntos_ganados
                st.success("Rutina completada correctamente.")
                st.success(f"Ganaste +{puntos_ganados} puntos.")
                st.balloons()
                break

            if tiempo_actual >= duracion_maxima:
                st.session_state.puntos += puntos_ganados
                st.warning("Tiempo máximo alcanzado.")
                st.info(f"Ganaste +{puntos_ganados} puntos.")
                break

            if detener:
                st.session_state.puntos += puntos_ganados
                st.warning("Ejercicio detenido.")
                st.info(f"Ganaste +{puntos_ganados} puntos.")
                break

            time.sleep(0.03)

    cap.release()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Volver al mapa de niveles", use_container_width=True):
            st.session_state.pantalla = "mapa"
            st.rerun()

    with col2:
        if st.button("Volver al dashboard", use_container_width=True):
            st.session_state.pantalla = "dashboard"
            st.rerun()