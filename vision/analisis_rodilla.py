import cv2
import mediapipe as mp
import numpy as np
import tempfile
import os
import time
import streamlit as st

mp_pose = mp.solutions.pose


def calcular_angulo(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    coseno = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    coseno = np.clip(coseno, -1.0, 1.0)

    return np.degrees(np.arccos(coseno))


def clasificar_flexion(angulo):
    if angulo >= 150:
        return "Pierna extendida"
    elif 100 <= angulo < 150:
        return "Flexion moderada"
    else:
        return "Flexion profunda"


def redimensionar_frame(frame, ancho_deseado=640):
    alto, ancho, _ = frame.shape

    if ancho <= ancho_deseado:
        return frame

    escala = ancho_deseado / ancho
    nuevo_alto = int(alto * escala)

    return cv2.resize(frame, (ancho_deseado, nuevo_alto))


def guardar_video_temporal(video_file):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp.write(video_file.getbuffer())
    temp.close()
    return temp.name


def procesar_video_dinamico(video_file, video_placeholder, panel_placeholder):
    ruta_video = guardar_video_temporal(video_file)
    cap = cv2.VideoCapture(ruta_video)

    if not cap.isOpened():
        os.remove(ruta_video)
        return {
            "detectado": False,
            "mensaje": "No se pudo abrir el video."
        }

    angulos = []
    puntos = 0
    frames_procesados = 0
    frames_detectados = 0

    # Para no saturar Streamlit
    salto_frames = 3
    frame_actual = 0

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:

        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                break

            frame_actual += 1

            if frame_actual % salto_frames != 0:
                continue

            frames_procesados += 1

            frame = redimensionar_frame(frame, ancho_deseado=640)
            height, width, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            angulo_rodilla = None
            estado = "No detectado"
            evaluacion = "Esperando postura"

            if results.pose_landmarks:
                frames_detectados += 1

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

                angulos.append(angulo_rodilla)
                estado = clasificar_flexion(angulo_rodilla)

                if 70 <= angulo_rodilla <= 120:
                    evaluacion = "Buen movimiento"
                    puntos += 1
                else:
                    evaluacion = "Requiere ajuste"

                # Dibujar líneas
                cv2.line(frame, punto_cadera, punto_rodilla, (255, 255, 255), 4)
                cv2.line(frame, punto_rodilla, punto_tobillo, (255, 255, 255), 4)

                # Dibujar puntos
                cv2.circle(frame, punto_cadera, 8, (0, 0, 255), -1)
                cv2.circle(frame, punto_rodilla, 10, (0, 255, 255), -1)
                cv2.circle(frame, punto_tobillo, 8, (0, 0, 255), -1)

                # Mostrar ángulo en el video
                cv2.putText(
                    frame,
                    f"{int(angulo_rodilla)} grados",
                    (punto_rodilla[0] + 20, punto_rodilla[1] + 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )

            else:
                cv2.putText(
                    frame,
                    "No se detecto postura",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            # Convertir frame BGR a RGB para Streamlit
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Actualizar video a la izquierda
            video_placeholder.image(
                frame_rgb,
                channels="RGB",
                use_container_width=True
            )

            # Datos dinámicos del panel derecho
            if angulo_rodilla is not None:
                angulo_actual = round(angulo_rodilla, 2)
            else:
                angulo_actual = "No detectado"

            if angulos:
                angulo_min = round(min(angulos), 2)
                angulo_max = round(max(angulos), 2)
                angulo_prom = round(sum(angulos) / len(angulos), 2)
            else:
                angulo_min = "-"
                angulo_max = "-"
                angulo_prom = "-"

            # Actualizar panel derecho
            with panel_placeholder.container():
                st.markdown("### Estado del ejercicio")

                if angulo_rodilla is not None:
                    st.metric(
                        label="Ángulo actual de rodilla",
                        value=f"{round(angulo_rodilla, 2)}°"
                    )
                else:
                    st.metric(
                        label="Ángulo actual de rodilla",
                        value="No detectado"
                    )

                if evaluacion == "Buen movimiento":
                    st.success("Buen movimiento. Sigue así.")
                elif evaluacion == "Requiere ajuste":
                    st.warning("Ajusta un poco la postura.")
                else:
                    st.info("Colócate frente a la cámara o video.")

                st.write(f"**Estado:** {estado}")

                st.divider()

                st.markdown("### Progreso del análisis")

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Ángulo mínimo", f"{angulo_min}°")

                with col2:
                    st.metric("Ángulo máximo", f"{angulo_max}°")

                st.metric("Promedio", f"{angulo_prom}°")

                st.divider()

                st.markdown("### Recompensas")

                st.metric("Puntos acumulados", puntos)

                if puntos >= 50:
                    st.success("Logro desbloqueado: sesión constante")
                elif puntos > 0:
                    st.info("Vas sumando puntos por buenos movimientos.")
                else:
                    st.warning("Aún no se sumaron puntos. Intenta una flexión más controlada.")

                st.progress(min(puntos / 50, 1.0))

                st.caption("Puntos usados para el análisis: cadera, rodilla y tobillo.")

            # Pausa corta para simular reproducción
            time.sleep(0.03)

    cap.release()
    os.remove(ruta_video)

    if not angulos:
        return {
            "detectado": False,
            "mensaje": "No se detectó postura durante el video."
        }

    return {
        "detectado": True,
        "angulo_min": round(min(angulos), 2),
        "angulo_max": round(max(angulos), 2),
        "angulo_promedio": round(sum(angulos) / len(angulos), 2),
        "frames_procesados": frames_procesados,
        "frames_detectados": frames_detectados,
        "puntos": puntos
    }