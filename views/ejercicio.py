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
    resultado,
    intentos_no_completados=0,
    mejor_racha=0,
    indicaciones_sistema=0,
    angulo_minimo=None,
    angulo_maximo=None,
    historial_intentos=None
):
    if historial_intentos is None:
        historial_intentos = []

    """
    Guarda el ejercicio en una lista temporal para que luego pueda
    aparecer en el historial cuando se registre la sesión desde el dashboard.
    Las estrellas se suman de inmediato a la interfaz.
    """

    intentos_totales = (
        repeticiones
        + intentos_no_completados
    )

    if intentos_totales > 0:

        efectividad_intentos = round(
            (
                repeticiones
                / intentos_totales
            )
            * 100
        )

    else:

        efectividad_intentos = 0


    # Limpiar valores angulares en caso
    # de que no se haya obtenido medición.

    if angulo_minimo == 999:
        angulo_minimo = None

    if angulo_maximo == 0:
        angulo_maximo = None

    if "ejercicios_pendientes" not in st.session_state:
        st.session_state.ejercicios_pendientes = []

    resultado_ejercicio = {
        "historial_intentos": historial_intentos.copy(),

        "intentos_no_completados": intentos_no_completados,

        "efectividad_intentos": efectividad_intentos,

        "mejor_racha": mejor_racha,

        "indicaciones_sistema": indicaciones_sistema,

        "angulo_minimo": angulo_minimo,

        "angulo_maximo": angulo_maximo,
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

    st.session_state.intentos_ultimo_ejercicio = (
    intentos_no_completados
    )

    st.session_state.efectividad_ultimo_ejercicio = (
        efectividad_intentos
    )

    st.session_state.mejor_racha_ultimo_ejercicio = (
        mejor_racha
    )

    st.session_state.indicaciones_ultimo_ejercicio = (
        indicaciones_sistema
    )

    st.session_state.angulo_minimo_ultimo_ejercicio = (
        angulo_minimo
    )

    st.session_state.angulo_maximo_ultimo_ejercicio = (
        angulo_maximo
    )

    st.session_state.repeticiones_ultimo_ejercicio = repeticiones

    st.session_state.objetivo_ultimo_ejercicio = total_repeticiones

    st.session_state.resultado_ultimo_ejercicio = resultado

    st.session_state.historial_intentos_ultimo_ejercicio = (
        historial_intentos.copy()
    )




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

    if "repeticiones_ultimo_ejercicio" not in st.session_state:
        st.session_state.repeticiones_ultimo_ejercicio = 0

    if "objetivo_ultimo_ejercicio" not in st.session_state:
        st.session_state.objetivo_ultimo_ejercicio = 0

    if "resultado_ultimo_ejercicio" not in st.session_state:
        st.session_state.resultado_ultimo_ejercicio = ""

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

    duracion_configurada = st.session_state.get(
        "duracion_objetivo_segundos",
        ejercicio.get("duracion_objetivo_segundos", 60)
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
            'Ejercicio finalizado'
            '</div>',
            unsafe_allow_html=True
        )

        resultado_final = st.session_state.resultado_ultimo_ejercicio

        if resultado_final == "Tiempo máximo":

            st.info(
                "El tiempo configurado ha finalizado."
            )

        elif resultado_final == "Detenido":

            st.warning(
                "El ejercicio fue detenido antes de finalizar."
            )

        # --------------------------------------------------
        # RESULTADOS FINALES
        # --------------------------------------------------

        repeticiones_realizadas = (
            st.session_state.repeticiones_ultimo_ejercicio
        )

        repeticiones_objetivo = (
            st.session_state.objetivo_ultimo_ejercicio
        )

        if repeticiones_objetivo > 0:

            porcentaje_cumplimiento = round(
                (
                    repeticiones_realizadas
                    / repeticiones_objetivo
                )
                * 100
            )

        else:

            porcentaje_cumplimiento = 0


        tiempo_total = (
            st.session_state.tiempo_ultimo_ejercicio
        )

        minutos = tiempo_total // 60
        segundos = tiempo_total % 60


        col_p1, col_p2, col_p3, col_p4 = st.columns(4)


        with col_p1:

            st.metric(
                "Repeticiones válidas",
                f"{repeticiones_realizadas}/{repeticiones_objetivo}"
            )


        with col_p2:

            st.metric(
                "Cumplimiento",
                f"{porcentaje_cumplimiento}%"
            )


        with col_p3:

            st.metric(
                "Estrellas ganadas",
                f"{st.session_state.puntos_ganados_ultimo} ⭐"
            )


        with col_p4:

            st.metric(
                "Tiempo",
                f"{minutos} min {segundos} s"
            )

        st.write("")

        st.markdown("### Tu desempeño")

        tipo_evaluacion = ejercicio.get(
            "tipo_evaluacion",
            ""
        )

        col_d1, col_d2, col_d3, col_d4 = st.columns(4)

        with col_d1:

            st.metric(
                "Intentos adicionales",
                st.session_state.get(
                    "intentos_ultimo_ejercicio",
                    0
                )
            )

        with col_d2:

            efectividad = st.session_state.get(
                "efectividad_ultimo_ejercicio",
                0
            )

            st.metric(
                "Efectividad",
                f"{efectividad}%"
            )

        with col_d3:

            st.metric(
                "Mejor racha",
                st.session_state.get(
                    "mejor_racha_ultimo_ejercicio",
                    0
                )
            )

        with col_d4:

            st.metric(
                "Indicaciones",
                st.session_state.get(
                    "indicaciones_ultimo_ejercicio",
                    0
                )
            )

        # --------------------------------------------------
        # SECUENCIA VISUAL
        # --------------------------------------------------

        historial = st.session_state.get(
            "historial_intentos_ultimo_ejercicio",
            []
        )

        if historial:

            st.markdown(
                "#### Secuencia de intentos"
            )

            secuencia_visual = " ".join(
                historial
            )

            st.markdown(
                f"""
                <div style="
                    font-size: 30px;
                    letter-spacing: 5px;
                    margin-top: 5px;
                    margin-bottom: 8px;
                ">
                    {secuencia_visual}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.caption(
                "✅ Repetición completada · "
                "❌ Intento adicional"
            )

        # --------------------------------------------------
        # DETALLES DEL EJERCICIO
        # --------------------------------------------------

        with st.expander(
            "Ver más detalles del ejercicio"
        ):

            angulo_min = st.session_state.get(
                "angulo_minimo_ultimo_ejercicio"
            )

            angulo_max = st.session_state.get(
                "angulo_maximo_ultimo_ejercicio"
            )

            if (
                angulo_min is not None
                and angulo_max is not None
            ):

                st.write(
                    "**Rango angular observado:** "
                    f"{round(angulo_min, 1)}° "
                    f"– {round(angulo_max, 1)}°"
                )

            resultado_final = st.session_state.get(
                "resultado_ultimo_ejercicio",
                "-"
            )

            st.write(
                "**Motivo de finalización:** "
                f"{resultado_final}"
            )

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

    # Métricas de desempeño
    intentos_no_completados = 0

    racha_actual = 0

    mejor_racha = 0

    historial_intentos = []

    # Indicaciones generadas por problemas
    # de posición o detección
    indicaciones_sistema = 0

    incidencia_deteccion_activa = False

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

    duracion_maxima = max(
        int(duracion_configurada),
        10
    )

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

                    # Solo contamos una nueva incidencia
                    # cuando comienza el problema.
                    # Dejamos 2 segundos iniciales de gracia.

                    if (
                        not incidencia_deteccion_activa
                        and
                        time.time() - tiempo_inicio >= 2
                    ):

                        indicaciones_sistema += 1

                        incidencia_deteccion_activa = True

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

                    # El problema de detección ya se solucionó.
                    # Si vuelve a ocurrir después, contará
                    # como una nueva indicación.

                    incidencia_deteccion_activa = False

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

                    # --------------------------------------
                    # INTENTO NO COMPLETADO
                    # --------------------------------------

                    if estado_eval.get(
                        "intento_no_completado_evento",
                        False
                    ):

                        intentos_no_completados += 1

                        # Una racha termina cuando hubo
                        # un intento que no se completó.
                        racha_actual = 0

                        historial_intentos.append("❌")

                        estado_eval[
                            "intento_no_completado_evento"
                        ] = False

                    estado_movimiento = (
                        estado_eval["fase"]
                    )

                    # --------------------------------------
                    # REPETICIÓN VÁLIDA
                    # --------------------------------------

                    if rep_valida:

                        repeticiones += 1

                        estrellas_ganadas += 10
                        

                        # ----------------------------------
                        # RACHA
                        # ----------------------------------

                        racha_actual += 1

                        mejor_racha = max(
                            mejor_racha,
                            racha_actual
                        )

                        historial_intentos.append("✅")

                        hablar_repeticion(
                            repeticiones,
                            total_repeticiones,
                            ejercicio["id"]
                        )

            else:

                if (
                    not incidencia_deteccion_activa
                    and
                    time.time() - tiempo_inicio >= 2
                ):

                    indicaciones_sistema += 1

                    incidencia_deteccion_activa = True

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

                tiempo_restante = max(
                    duracion_maxima - tiempo_actual,
                    0
                )

                col1, col2, col3 = st.columns(3)

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

                with col3:

                    st.metric(
                        "Tiempo restante",
                        f"{tiempo_restante} s"
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
                    f"Tiempo transcurrido: {minutos} min {segundos} s "
                    f"de {duracion_maxima} s configurados"
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
                    resultado="Completado",
                    intentos_no_completados=intentos_no_completados,
                    mejor_racha=mejor_racha,
                    indicaciones_sistema=indicaciones_sistema,
                    angulo_minimo=angulo_minimo,
                    angulo_maximo=angulo_maximo,
                    historial_intentos=historial_intentos
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
                    resultado="Tiempo máximo",
                    intentos_no_completados=intentos_no_completados,
                    mejor_racha=mejor_racha,
                    indicaciones_sistema=indicaciones_sistema,
                    angulo_minimo=angulo_minimo,
                    angulo_maximo=angulo_maximo,
                    historial_intentos=historial_intentos
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
                    resultado="Detenido",
                    intentos_no_completados=intentos_no_completados,
                    mejor_racha=mejor_racha,
                    indicaciones_sistema=indicaciones_sistema,
                    angulo_minimo=angulo_minimo,
                    angulo_maximo=angulo_maximo,
                    historial_intentos=historial_intentos
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