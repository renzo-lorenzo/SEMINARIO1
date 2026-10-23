import streamlit as st
import time
import os
import base64
import math
import cv2
import mediapipe as mp

from utils.asistente_voz import hablar_indicacion_tutorial
from utils.evaluacion_movimiento import (
    obtener_muestra_calibracion,
    seleccionar_lado_calibracion,
    calcular_referencia_estable,
)


mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


def mostrar_video_autoplay(ruta_video, ancho="100%"):
    if not os.path.exists(ruta_video):
        st.warning("No se encontró el video tutorial.")
        return

    with open(ruta_video, "rb") as video_file:
        video_bytes = video_file.read()

    video_base64 = base64.b64encode(video_bytes).decode()

    video_html = f"""
    <div style="display: flex; justify-content: center; width: 100%;">
        <video width="{ancho}" autoplay muted playsinline
               style="border-radius: 18px; width: 100%; height: auto;">
            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
        </video>
    </div>
    """

    st.markdown(
        video_html,
        unsafe_allow_html=True
    )


def _nombre_lado(lado):
    """
    La imagen utilizada por el sistema está espejada.
    Convertimos el nombre interno a la perspectiva
    física del participante.
    """
    if lado == "LEFT":
        return "derecha"

    if lado == "RIGHT":
        return "izquierda"

    return "por definir"


def pantalla_tutorial():
    ejercicio = st.session_state.get(
        "ejercicio_actual",
        None
    )

    if ejercicio is None:

        st.warning(
            "No se seleccionó ningún ejercicio."
        )

        if st.button(
            "Volver al mapa de niveles"
        ):
            st.session_state.pantalla = "mapa"
            st.rerun()

        return

    # ======================================================
    # TÍTULO
    # ======================================================

    st.markdown(
        f'<div class="title">{ejercicio["nombre"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '''
        <div class="subtitle">
            Observa el tutorial mientras el sistema prepara tu posición
        </div>
        ''',
        unsafe_allow_html=True
    )

    # ======================================================
    # CONFIGURACIÓN DEL EJERCICIO
    # ======================================================

    repeticiones_objetivo = (
        st.session_state.get(
            "repeticiones_objetivo",
            ejercicio.get(
                "repeticiones_objetivo",
                10
            )
        )
    )

    duracion_objetivo = (
        st.session_state.get(
            "duracion_objetivo_segundos",
            ejercicio.get(
                "duracion_objetivo_segundos",
                60
            )
        )
    )

    st.info(
        "Durante el tutorial, la cámara verificará tu posición "
        "y preparará la referencia inicial para el ejercicio. "
        f"Objetivo: {repeticiones_objetivo} repeticiones "
        f"en un máximo de {duracion_objetivo} segundos."
    )

    # ======================================================
    # VIDEO SEGÚN EJERCICIO
    # ======================================================

    videos_tutorial = {
        1: "imagenes/tutorial_extension_rodilla.mp4",
        2: "imagenes/tutorial_elevacion_pierna.mp4",
        3: "imagenes/tutorial_mini_sentadilla.mp4",
        4: "imagenes/tutorial_puente_gluteo.mp4",
        5: "imagenes/tutorial_step_basico.mp4",
        6: "imagenes/tutorial_abduccion_cadera.mp4",
        7: "imagenes/tutorial_sit_to_stand.mp4",
        8: "imagenes/tutorial_marcha_sitio.mp4",
    }

    ruta_video = videos_tutorial.get(
        ejercicio["id"],
        "imagenes/tutorial_extension_rodilla.mp4"
    )

    # ======================================================
    # DISEÑO:
    # IZQUIERDA = CÁMARA PEQUEÑA
    # DERECHA   = TUTORIAL GRANDE
    # ======================================================

    col_camara, col_tutorial = st.columns(
        [1, 2.15]
    )

    with col_camara:

        st.subheader(
            "Tu posición"
        )

        camara_placeholder = st.empty()

        estado_placeholder = st.empty()

    with col_tutorial:

        st.subheader(
            "Tutorial"
        )

        mostrar_video_autoplay(
            ruta_video,
            ancho="100%"
        )

    contador_placeholder = st.empty()

    # ======================================================
    # VOZ DEL TUTORIAL
    # ======================================================

    hablar_indicacion_tutorial(
        ejercicio
    )

    # ======================================================
    # ACTIVAR CÁMARA
    # ======================================================

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        st.error(
            "No se pudo activar la cámara "
            "para preparar el ejercicio."
        )

        return

    # ======================================================
    # MUESTRAS PARA CALIBRACIÓN
    # ======================================================

    muestras_por_lado = {
        "RIGHT": [],
        "LEFT": [],
    }

    duracion_tutorial = 13

    tiempo_inicio_preparacion = (
        time.time()
    )

    calibracion_actual = None

    ultimo_lado_candidato = None

    # ======================================================
    # MEDIAPIPE
    # MISMA CONFIGURACIÓN QUE EN EJECUCIÓN
    # ======================================================

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    ) as pose:

        while cap.isOpened():

            # ==============================================
            # CAPTURAR FRAME
            # ==============================================

            ret, frame = cap.read()

            if not ret:

                st.error(
                    "No se pudo leer la cámara "
                    "durante la preparación."
                )

                break

            # Mantener por ahora el mismo tratamiento
            # de imagen que utiliza ejercicio.py.

            frame = cv2.resize(
                frame,
                (520, 390)
            )

            frame = cv2.flip(
                frame,
                1
            )

            height, width, _ = (
                frame.shape
            )

            # ==============================================
            # PROCESAR CON MEDIAPIPE
            # ==============================================

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            results = pose.process(
                rgb
            )

            # En cada frame volvemos a comprobar
            # si la posición ACTUAL sigue siendo estable.

            calibracion_actual = None

            lado_candidato = None

            # ==============================================
            # LANDMARKS DETECTADOS
            # ==============================================

            if results.pose_landmarks:

                landmarks = (
                    results.pose_landmarks.landmark
                )

                # ------------------------------------------
                # PIERNA DERECHA
                # ------------------------------------------

                muestra_derecha = (
                    obtener_muestra_calibracion(
                        landmarks=landmarks,
                        width=width,
                        height=height,
                        lado="RIGHT"
                    )
                )

                # ------------------------------------------
                # PIERNA IZQUIERDA
                # ------------------------------------------

                muestra_izquierda = (
                    obtener_muestra_calibracion(
                        landmarks=landmarks,
                        width=width,
                        height=height,
                        lado="LEFT"
                    )
                )

                if muestra_derecha is not None:

                    muestras_por_lado[
                        "RIGHT"
                    ].append(
                        muestra_derecha
                    )

                if muestra_izquierda is not None:

                    muestras_por_lado[
                        "LEFT"
                    ].append(
                        muestra_izquierda
                    )

                # ------------------------------------------
                # CONSERVAR SOLO FRAMES RECIENTES
                # ------------------------------------------

                muestras_por_lado[
                    "RIGHT"
                ] = (
                    muestras_por_lado[
                        "RIGHT"
                    ][-120:]
                )

                muestras_por_lado[
                    "LEFT"
                ] = (
                    muestras_por_lado[
                        "LEFT"
                    ][-120:]
                )

                # ------------------------------------------
                # SELECCIONAR MEJOR PIERNA
                # ------------------------------------------

                lado_candidato = (
                    seleccionar_lado_calibracion(
                        muestras_por_lado
                    )
                )

                if lado_candidato is not None:

                    ultimo_lado_candidato = (
                        lado_candidato
                    )

                    # --------------------------------------
                    # BUSCAR REFERENCIA ESTABLE
                    # --------------------------------------

                    referencia = (
                        calcular_referencia_estable(
                            muestras=(
                                muestras_por_lado[
                                    lado_candidato
                                ]
                            ),
                            ventana=18,
                            desplazamiento_maximo=0.035
                        )
                    )

                    # Si la pierna que tiene mejor
                    # visibilidad todavía no está estable,
                    # comprobamos también la otra.

                    if referencia is None:

                        otro_lado = (
                            "LEFT"
                            if lado_candidato == "RIGHT"
                            else "RIGHT"
                        )

                        referencia_otro = (
                            calcular_referencia_estable(
                                muestras=(
                                    muestras_por_lado[
                                        otro_lado
                                    ]
                                ),
                                ventana=18,
                                desplazamiento_maximo=0.035
                            )
                        )

                        if (
                            referencia_otro
                            is not None
                        ):

                            lado_candidato = (
                                otro_lado
                            )

                            ultimo_lado_candidato = (
                                otro_lado
                            )

                            referencia = (
                                referencia_otro
                            )

                    # --------------------------------------
                    # CALIBRACIÓN VÁLIDA
                    # --------------------------------------

                    if referencia is not None:

                        calibracion_actual = {
                            "ejercicio_id": (
                                ejercicio["id"]
                            ),

                            "lado": (
                                lado_candidato
                            ),

                            "base_tobillo_y": (
                                referencia[
                                    "base_tobillo_y"
                                ]
                            ),

                            "base_tobillo_x": (
                                referencia[
                                    "base_tobillo_x"
                                ]
                            ),

                            "base_cadera_y": (
                                referencia[
                                    "base_cadera_y"
                                ]
                            ),

                            "base_rodilla_y": (
                                referencia[
                                    "base_rodilla_y"
                                ]
                            ),

                            "visibilidad_media": (
                                referencia[
                                    "visibilidad_media"
                                ]
                            ),

                            "muestras_utilizadas": (
                                referencia[
                                    "muestras_utilizadas"
                                ]
                            ),
                        }

                # ------------------------------------------
                # DIBUJAR LANDMARKS
                # ------------------------------------------

                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

            # ==============================================
            # MOSTRAR CÁMARA
            # ==============================================

            frame_rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            camara_placeholder.image(
                frame_rgb,
                channels="RGB",
                use_container_width=True
            )

            # ==============================================
            # TIEMPO DE PREPARACIÓN
            # ==============================================

            transcurrido = (
                time.time()
                -
                tiempo_inicio_preparacion
            )

            restante = max(
                math.ceil(
                    duracion_tutorial
                    -
                    transcurrido
                ),
                0
            )

            # ==============================================
            # MENSAJES DE PREPARACIÓN
            # ==============================================

            if not results.pose_landmarks:

                estado_placeholder.warning(
                    "Buscando tu cuerpo. "
                    "Mantente visible frente a la cámara."
                )

            elif calibracion_actual is None:

                texto_lado = _nombre_lado(
                    ultimo_lado_candidato
                )

                estado_placeholder.info(
                    "Cuerpo detectado. "
                    "Mantén la posición inicial un momento. "
                    f"Pierna candidata: {texto_lado}."
                )

            else:

                texto_lado = _nombre_lado(
                    calibracion_actual[
                        "lado"
                    ]
                )

                estado_placeholder.success(
                    "Posición inicial estable detectada. "
                    f"Pierna seleccionada: {texto_lado}."
                )

            # ==============================================
            # CUENTA REGRESIVA
            # ==============================================

            if (
                transcurrido
                <
                duracion_tutorial
            ):

                contador_placeholder.info(
                    "Preparando el ejercicio... "
                    f"{restante} s"
                )

            else:

                # Los 13 segundos terminaron.
                # Solo avanzamos si EN ESE MOMENTO
                # existe una referencia estable.

                if (
                    calibracion_actual
                    is not None
                ):

                    st.session_state[
                        "calibracion_ejercicio"
                    ] = (
                        calibracion_actual.copy()
                    )

                    break

                contador_placeholder.warning(
                    "El tutorial terminó. "
                    "Mantén la posición inicial "
                    "unos segundos más para completar "
                    "la preparación."
                )

            # Pequeña pausa para no saturar CPU.

            time.sleep(
                0.03
            )

    # ======================================================
    # CERRAR CÁMARA
    # ======================================================

    cap.release()

    # ======================================================
    # SI NO SE PUDO CALIBRAR
    # ======================================================

    if calibracion_actual is None:

        st.error(
            "No fue posible completar la preparación. "
            "Vuelve al mapa e intenta nuevamente procurando "
            "mantener el cuerpo visible frente a la cámara."
        )

        return

    # ======================================================
    # TRANSICIÓN
    # ======================================================

    contador_placeholder.empty()

    st.markdown(
        """
        <style>

        @keyframes preparacionLista {

            0% {
                opacity: 0;
                transform: scale(0.96);
            }

            100% {
                opacity: 1;
                transform: scale(1);
            }
        }

        .preparacion-lista {

            margin-top: 8px;

            padding: 14px 18px;

            border-radius: 16px;

            text-align: center;

            font-size: 1.05rem;

            font-weight: 700;

            animation:
                preparacionLista
                0.45s
                ease-out;
        }

        </style>

        <div class="preparacion-lista">
            Preparación completada.
            Iniciando ejercicio...
        </div>
        """,
        unsafe_allow_html=True
    )

    time.sleep(
        0.55
    )

    # ======================================================
    # PASAR A EJECUCIÓN
    # ======================================================

    st.session_state.ejercicio_activo = True

    st.session_state.ejercicio_completado = False

    st.session_state.puntos_ganados_ultimo = 0

    st.session_state.voz_fin_ejercicio_pendiente = False

    st.session_state.transicion_desde_tutorial = True

    st.session_state.pantalla = "ejercicio"

    st.rerun()