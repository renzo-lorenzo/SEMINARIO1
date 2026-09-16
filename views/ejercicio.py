import streamlit as st
import cv2
import mediapipe as mp
import time
import os
from datetime import datetime

from utils.asistente_voz import (
    inicializar_asistente_voz,
    mostrar_control_voz_global,
    hablar,
    hablar_repeticion,
    hablar_fin_ejercicio_si_corresponde
)

from utils.ejercicios import (
    obtener_ejercicios
)

from utils.evaluacion_movimiento import (
    calcular_angulo,
    obtener_puntos_pierna,
    dibujar_solo_pierna,
    inicializar_estado_evaluacion,
    evaluar_movimiento
)


mp_pose = mp.solutions.pose


# ==========================================================
# VIDEO DE ANIMACIÓN
# ==========================================================

def mostrar_video_loop(ruta_video):

    if not os.path.exists(ruta_video):
        st.warning("No se encontró la animación del ejercicio.")
        return

    st.video(
        ruta_video,
        format="video/mp4",
        autoplay=True,
        loop=True,
        muted=True
    )


# ==========================================================
# REGISTRAR RESULTADO TEMPORAL DE LA SESIÓN ACTUAL
# ==========================================================

def registrar_resultado_temporal(
    ejercicio,
    total_repeticiones,
    repeticiones,
    estrellas_ganadas,
    tiempo_actual,
    resultado
):
    """
    Guarda el ejercicio en una lista temporal para que luego pueda
    aparecer en el historial cuando se registre la sesión desde el dashboard.
    Las estrellas se suman de inmediato a la interfaz.
    """

    if "ejercicios_pendientes" not in st.session_state:
        st.session_state.ejercicios_pendientes = []

    resultado_ejercicio = {
        "ejercicio_id": ejercicio["id"],
        "nombre": ejercicio["nombre"],
        "repeticiones_objetivo": total_repeticiones,
        "repeticiones_realizadas": repeticiones,
        "puntos": estrellas_ganadas,
        "duracion_segundos": tiempo_actual,
        "fecha_hora": datetime.now().isoformat(
            timespec="seconds"
        ),
        "resultado": resultado
    }

    st.session_state.ejercicios_pendientes.append(
        resultado_ejercicio
    )

    if "puntos" not in st.session_state:
        st.session_state.puntos = 0

    if "puntos_ganados_total" not in st.session_state:
        st.session_state.puntos_ganados_total = 0

    st.session_state.puntos += estrellas_ganadas

    st.session_state.puntos_ganados_total += estrellas_ganadas

    st.session_state.puntos_ganados_ultimo = estrellas_ganadas

    st.session_state.tiempo_ultimo_ejercicio = tiempo_actual


# ==========================================================
# PANTALLA DEL EJERCICIO
# ==========================================================

def pantalla_ejercicio():

    inicializar_asistente_voz()
    mostrar_control_voz_global()
    # ------------------------------------------------------
    # OBTENER EJERCICIO ACTUAL
    # ------------------------------------------------------

    ejercicio_actual = st.session_state.get(
        "ejercicio_actual",
        None
    )

    if ejercicio_actual is None:

        st.warning(
            "No se seleccionó ningún ejercicio."
        )

        if st.button("Volver al mapa"):

            st.session_state.pantalla = "mapa"

            st.rerun()

        return

    # ------------------------------------------------------
    # ACTUALIZAR EL EJERCICIO DESDE ejercicios.py
    # ------------------------------------------------------
    # Esto evita que session_state conserve una versión
    # antigua del ejercicio.
    # ------------------------------------------------------

    ejercicios_actualizados = obtener_ejercicios()

    ejercicio_id = ejercicio_actual.get("id")

    ejercicio = next(
        (
            e for e in ejercicios_actualizados
            if e["id"] == ejercicio_id
        ),
        ejercicio_actual
    )

    st.session_state.ejercicio_actual = ejercicio

    # ------------------------------------------------------
    # ESTADOS INICIALES
    # ------------------------------------------------------

    if "ejercicio_completado" not in st.session_state:
        st.session_state.ejercicio_completado = False

    if "puntos_ganados_ultimo" not in st.session_state:
        st.session_state.puntos_ganados_ultimo = 0

    if "tiempo_ultimo_ejercicio" not in st.session_state:
        st.session_state.tiempo_ultimo_ejercicio = 0

    if "ejercicios_pendientes" not in st.session_state:
        st.session_state.ejercicios_pendientes = []

    if "puntos" not in st.session_state:
        st.session_state.puntos = 0

    if "puntos_ganados_total" not in st.session_state:
        st.session_state.puntos_ganados_total = 0

    # ======================================================
    # CONFIGURACIÓN DEL EJERCICIO
    # ======================================================

    total_repeticiones = st.session_state.get(
        "repeticiones_objetivo",
        ejercicio.get("repeticiones_objetivo", 10)
    )

    # ======================================================
    # PANTALLA FINAL
    # ======================================================

    if st.session_state.ejercicio_completado:

        hablar_fin_ejercicio_si_corresponde()

        st.markdown(
            f'<div class="title">{ejercicio["nombre"]}</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="subtitle">'
            'Rutina finalizada'
            '</div>',
            unsafe_allow_html=True
        )

        st.success(
            "Rutina finalizada correctamente."
        )

        st.info(
            f"Ganaste +{st.session_state.puntos_ganados_ultimo} estrellas. "
            f"Ahora tienes {st.session_state.puntos} estrellas disponibles. "
            "Recuerda registrar la sesión al finalizar para guardar el historial."
        )

        # --------------------------------------------------
        # RESULTADOS FINALES
        # --------------------------------------------------

        col_p1, col_p2, col_p3 = st.columns(3)

        with col_p1:

            st.metric(
                "Estrellas ganadas",
                st.session_state.puntos_ganados_ultimo
            )

        with col_p2:

            st.metric(
                "Estrellas disponibles",
                st.session_state.puntos
            )

        with col_p3:

            tiempo_total = (
                st.session_state.tiempo_ultimo_ejercicio
            )

            minutos = tiempo_total // 60
            segundos = tiempo_total % 60

            st.metric(
                "Tiempo",
                f"{minutos} min {segundos} s"
            )

        st.write("")

        # --------------------------------------------------
        # BOTONES
        # --------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Volver al mapa de ejercicios",
                use_container_width=True,
                key="volver_mapa_completado"
            ):

                st.session_state.ejercicio_activo = False

                st.session_state.ejercicio_completado = False

                st.session_state.pantalla = "mapa"

                st.rerun()

        with col2:

            if st.button(
                "Volver al dashboard",
                use_container_width=True,
                key="volver_dashboard_completado"
            ):

                st.session_state.ejercicio_activo = False

                st.session_state.ejercicio_completado = False

                st.session_state.pantalla = "dashboard"

                st.rerun()

        return

    # ======================================================
    # ENCABEZADO
    # ======================================================

    st.markdown(
        f'<div class="title">{ejercicio["nombre"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'''
        <div class="subtitle">
            Nivel {ejercicio["nivel_dificultad"]}
            -
            {ejercicio["objetivo"]}
        </div>
        ''',
        unsafe_allow_html=True
    )

    st.info(
        "Ubícate frente a la cámara. "
        "El sistema analizará tu movimiento automáticamente."
    )

    hablar(
        f"Vamos a iniciar el ejercicio {ejercicio['nombre']}. "
        "Ubícate frente a la cámara y mantén el cuerpo visible.",
        clave=f"inicio_ejercicio_{ejercicio['id']}",
        cooldown=60
    )

    # ======================================================
    # COLUMNAS PRINCIPALES
    # ======================================================

    col_camara, col_derecha = st.columns(
        [1.35, 1]
    )

    # ------------------------------------------------------
    # CÁMARA
    # ------------------------------------------------------

    with col_camara:

        st.subheader(
            "Cámara del participante"
        )

        camara_placeholder = st.empty()

    # ------------------------------------------------------
    # ANIMACIÓN + RESULTADOS
    # ------------------------------------------------------

    with col_derecha:

        st.subheader(
            "Animación guía"
        )

        animacion_placeholder = st.empty()

        resultados_placeholder = st.empty()

    # ======================================================
    # VIDEOS
    # ======================================================

    videos_animacion = {
        1: "imagenes/tutorial_extension_rodilla.mp4",
        2: "imagenes/tutorial_elevacion_pierna.mp4",
        3: "imagenes/tutorial_mini_sentadilla.mp4",
        4: "imagenes/tutorial_puente_gluteo.mp4",
        5: "imagenes/tutorial_step_basico.mp4",
        6: "imagenes/tutorial_abduccion_cadera.mp4",
        7: "imagenes/tutorial_sit_to_stand.mp4",
        8: "imagenes/tutorial_marcha_sitio.mp4",
    }

    ruta_animacion = videos_animacion.get(
        ejercicio["id"],
        "imagenes/tutorial_extension_rodilla.mp4"
    )

    with animacion_placeholder.container():

        mostrar_video_loop(
            ruta_animacion
        )

    # ======================================================
    # CÁMARA
    # ======================================================

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        st.error(
            "No se pudo activar la cámara."
        )

        return

    # ======================================================
    # CONFIGURACIÓN DEL EJERCICIO
    # ======================================================

    repeticiones = 0

    estrellas_ganadas = 0

    # ======================================================
    # ESTADO DE EVALUACIÓN
    # ======================================================

    estado_eval = (
        inicializar_estado_evaluacion()
    )

    estado_movimiento = "inicio"

    angulo_actual = 0

    angulo_minimo = 999

    angulo_maximo = 0

    angulos = []

    # ======================================================
    # CRONÓMETRO
    # ======================================================

    tiempo_inicio = time.time()

    duracion_maxima = 300

    # ======================================================
    # BOTÓN DETENER
    # ======================================================

    detener = st.button(
        "Detener ejercicio",
        use_container_width=True
    )

    # ======================================================
    # MEDIAPIPE
    # ======================================================

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    ) as pose:

        # --------------------------------------------------
        # BUCLE PRINCIPAL
        # --------------------------------------------------

        while (
            cap.isOpened()
            and
            st.session_state.get(
                "ejercicio_activo",
                True
            )
        ):

            # ==============================================
            # CAPTURAR FRAME
            # ==============================================

            ret, frame = cap.read()

            if not ret:

                st.error(
                    "No se pudo leer la cámara."
                )

                break

            # ==============================================
            # PREPARAR FRAME
            # ==============================================

            frame = cv2.resize(
                frame,
                (520, 390)
            )

            frame = cv2.flip(
                frame,
                1
            )

            height, width, _ = frame.shape

            # ==============================================
            # MEDIAPIPE
            # ==============================================

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            results = pose.process(
                rgb
            )

            mensaje = (
                "Colócate de lado y "
                "muestra la pierna completa"
            )

            # ==============================================
            # DETECCIÓN DE POSTURA
            # ==============================================

            if results.pose_landmarks:

                landmarks = (
                    results.pose_landmarks.landmark
                )

                # ------------------------------------------
                # PIERNA DERECHA
                # ------------------------------------------

                puntos_pierna = obtener_puntos_pierna(
                    landmarks=landmarks,
                    width=width,
                    height=height,
                    lado="RIGHT"
                )

                # ------------------------------------------
                # SI NO DETECTA DERECHA,
                # INTENTA IZQUIERDA
                # ------------------------------------------

                if puntos_pierna is None:

                    puntos_pierna = obtener_puntos_pierna(
                        landmarks=landmarks,
                        width=width,
                        height=height,
                        lado="LEFT"
                    )

                # ------------------------------------------
                # NO DETECTÓ LA PIERNA
                # ------------------------------------------

                if puntos_pierna is None:

                    mensaje = (
                        "No se detectan correctamente "
                        "los puntos corporales necesarios. "
                        "Ajusta tu posición frente a la cámara."
                    )

                    hablar(
                        mensaje,
                        clave="ajustar_posicion",
                        cooldown=8
                    )

                # ------------------------------------------
                # PIERNA DETECTADA
                # ------------------------------------------

                else:

                    punto_cadera = (
                        puntos_pierna["cadera"]
                    )

                    punto_rodilla = (
                        puntos_pierna["rodilla"]
                    )

                    punto_tobillo = (
                        puntos_pierna["tobillo"]
                    )

                    # --------------------------------------
                    # CALCULAR ÁNGULO
                    # --------------------------------------

                    angulo_actual = calcular_angulo(
                        punto_cadera,
                        punto_rodilla,
                        punto_tobillo
                    )

                    # --------------------------------------
                    # GUARDAR ÁNGULOS
                    # --------------------------------------

                    if angulo_actual is not None:

                        angulos.append(
                            angulo_actual
                        )

                        angulo_minimo = min(
                            angulo_minimo,
                            angulo_actual
                        )

                        angulo_maximo = max(
                            angulo_maximo,
                            angulo_actual
                        )

                    # --------------------------------------
                    # DIBUJAR PIERNA
                    # --------------------------------------

                    dibujar_solo_pierna(
                        frame=frame,
                        puntos=puntos_pierna,
                        angulo_actual=angulo_actual
                    )

                    # --------------------------------------
                    # EVALUAR MOVIMIENTO
                    # --------------------------------------

                    rep_valida, estado_eval, mensaje = (
                        evaluar_movimiento(
                            ejercicio=ejercicio,
                            angulo=angulo_actual,
                            puntos=puntos_pierna,
                            estado_eval=estado_eval
                        )
                    )

                    estado_movimiento = (
                        estado_eval["fase"]
                    )

                    # --------------------------------------
                    # REPETICIÓN VÁLIDA
                    # --------------------------------------

                    if rep_valida:

                        repeticiones += 1

                        estrellas_ganadas += 10

                        hablar_repeticion(
                            repeticiones,
                            total_repeticiones,
                            ejercicio["id"]
                        )

            else:

                mensaje = (
                    "No se detectó la postura. "
                    "Ubícate frente a la cámara y "
                    "mantén el cuerpo visible."
                )

                hablar(
                    mensaje,
                    clave="no_detecta_postura",
                    cooldown=8
                )

            # ==================================================
            # MOSTRAR CÁMARA
            # ==================================================

            frame_rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            camara_placeholder.image(
                frame_rgb,
                channels="RGB",
                use_container_width=True
            )

            # ==================================================
            # TIEMPO
            # ==================================================

            tiempo_actual = int(
                time.time()
                -
                tiempo_inicio
            )

            # ==================================================
            # PROGRESO
            # ==================================================

            progreso = min(
                repeticiones
                /
                total_repeticiones,
                1.0
            )

            # ==================================================
            # ÁNGULOS
            # ==================================================

            if angulos:

                promedio = round(
                    sum(angulos)
                    /
                    len(angulos),
                    2
                )

                min_texto = round(
                    angulo_minimo,
                    2
                )

                max_texto = round(
                    angulo_maximo,
                    2
                )

            else:

                promedio = "-"

                min_texto = "-"

                max_texto = "-"

            # ==================================================
            # RESULTADOS EN TIEMPO REAL
            # ==================================================

            with resultados_placeholder.container():

                st.markdown(
                    "### Resultados"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Repeticiones",
                        f"{repeticiones}/{total_repeticiones}"
                    )

                with col2:

                    st.metric(
                        "Estrellas",
                        estrellas_ganadas
                    )

                st.progress(
                    progreso
                )

                # ------------------------------------------
                # ÁNGULO
                # ------------------------------------------

                if angulo_actual is not None:

                    angulo_texto = (
                        f"{round(angulo_actual, 1)}°"
                    )

                else:

                    angulo_texto = "-"

                st.metric(
                    "Ángulo",
                    angulo_texto
                )

                # ------------------------------------------
                # ESTADO
                # ------------------------------------------

                st.caption(
                    f"Estado: {estado_movimiento}"
                )

                st.caption(
                    f"Retroalimentación: {mensaje}"
                )

                # ------------------------------------------
                # TIEMPO
                # ------------------------------------------

                minutos = (
                    tiempo_actual // 60
                )

                segundos = (
                    tiempo_actual % 60
                )

                st.caption(
                    f"Tiempo: {minutos} min {segundos} s"
                )

            # ==================================================
            # EJERCICIO COMPLETADO
            # ==================================================

            if repeticiones >= total_repeticiones:

                registrar_resultado_temporal(
                    ejercicio=ejercicio,
                    total_repeticiones=total_repeticiones,
                    repeticiones=repeticiones,
                    estrellas_ganadas=estrellas_ganadas,
                    tiempo_actual=tiempo_actual,
                    resultado="Completado"
                )

                st.session_state.ejercicio_activo = False

                st.session_state.voz_fin_ejercicio_pendiente = True

                st.session_state.ejercicio_completado = True

                hablar(
                    f"Rutina completada. Ganaste {estrellas_ganadas} estrellas. Buen trabajo.",
                    clave=f"rutina_completada_{ejercicio['id']}",
                    cooldown=3
                )

                st.balloons()

                break

            # ==================================================
            # TIEMPO MÁXIMO
            # ==================================================

            if tiempo_actual >= duracion_maxima:

                registrar_resultado_temporal(
                    ejercicio=ejercicio,
                    total_repeticiones=total_repeticiones,
                    repeticiones=repeticiones,
                    estrellas_ganadas=estrellas_ganadas,
                    tiempo_actual=tiempo_actual,
                    resultado="Tiempo máximo"
                )

                st.session_state.ejercicio_activo = False

                st.session_state.ejercicio_completado = True

                st.warning(
                    "Tiempo máximo alcanzado."
                )

                break

            # ==================================================
            # DETENER MANUALMENTE
            # ==================================================

            if detener:

                registrar_resultado_temporal(
                    ejercicio=ejercicio,
                    total_repeticiones=total_repeticiones,
                    repeticiones=repeticiones,
                    estrellas_ganadas=estrellas_ganadas,
                    tiempo_actual=tiempo_actual,
                    resultado="Detenido"
                )

                st.session_state.ejercicio_activo = False

                st.session_state.ejercicio_completado = True

                st.warning(
                    "Ejercicio detenido."
                )

                break

            # ==================================================
            # PEQUEÑA PAUSA
            # ==================================================

            time.sleep(0.03)

    # ======================================================
    # LIBERAR CÁMARA
    # ======================================================

    cap.release()

    # ======================================================
    # MOSTRAR PANTALLA FINAL
    # ======================================================

    if st.session_state.ejercicio_completado:

        st.rerun()

    # ======================================================
    # BOTONES INFERIORES
    # ======================================================

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Volver al mapa de ejercicios",
            use_container_width=True,
            key="btn_volver_mapa"
        ):

            st.session_state.ejercicio_activo = False

            st.session_state.pantalla = "mapa"

            st.rerun()

    with col2:

        if st.button(
            "Volver al dashboard",
            use_container_width=True,
            key="btn_volver_dashboard"
        ):

            st.session_state.ejercicio_activo = False

            st.session_state.pantalla = "dashboard"

            st.rerun()