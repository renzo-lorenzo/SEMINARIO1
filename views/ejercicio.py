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

from utils.visuales import dibujar_feedback_repeticion


mp_pose = mp.solutions.pose


def identidad_abduccion_confiable(
    puntos_elegida,
    puntos_otra,
    estado,
    base_x,
    ahora
):
    """
    Comprueba que la pierna evaluada conserve su
    posición física respecto de la otra pierna.
    """

    if puntos_elegida is None or puntos_otra is None:
        estado.pop("_abd_orden_candidato", None)
        estado.pop("_abd_orden_desde", None)
        return False

    x_elegida = puntos_elegida["tobillo_norm"][0]
    x_otra = puntos_otra["tobillo_norm"][0]


    diferencia = x_elegida - x_otra

    # Cuando los tobillos están próximos,
    # comprobar también rodillas y caderas.
    if abs(diferencia) < 0.04:

        diferencia_rodillas = (
            puntos_elegida["rodilla_norm"][0]
            - puntos_otra["rodilla_norm"][0]
        )

        if abs(diferencia_rodillas) >= 0.02:

            diferencia = diferencia_rodillas

        else:

            diferencia_caderas = (
                puntos_elegida["cadera_norm"][0]
                - puntos_otra["cadera_norm"][0]
            )

            if abs(diferencia_caderas) < 0.035:

                estado.pop("_abd_orden_candidato", None)
                estado.pop("_abd_orden_desde", None)
                return False

            diferencia = diferencia_caderas


    orden_actual = 1 if diferencia > 0 else -1
    orden_fijo = estado.get("_abd_orden_fijo")

    # Establecer la identidad física inicial.
    if orden_fijo is None:

        # Comprobar coherencia con la calibración.
        if (
            base_x is not None
            and abs(x_elegida - base_x)
            > abs(x_otra - base_x) + 0.02
        ):
            estado.pop("_abd_orden_candidato", None)
            estado.pop("_abd_orden_desde", None)
            return False

        if estado.get("_abd_orden_candidato") != orden_actual:
            estado["_abd_orden_candidato"] = orden_actual
            estado["_abd_orden_desde"] = ahora
            return False

        # Exigir 0,4 segundos de identificación estable.
        if ahora - estado["_abd_orden_desde"] < 0.4:
            return False

        estado["_abd_orden_fijo"] = orden_actual

    # Nunca aceptar una inversión del orden fijado.
    return orden_actual == estado["_abd_orden_fijo"]

def identidad_extension_confiable(
    elegida, otra, estado, base_x, ahora
):
    """
    Mantiene la pierna calibrada durante la extensión
    de rodilla sentado, sin cambiar a la contraria.
    """

    if elegida is None:
        return False

    # La cadera y la rodilla son más estables
    # que el tobillo durante este ejercicio.
    orden_actual = None

    if otra is not None:
        dx_cadera = (
            elegida["cadera_norm"][0]
            - otra["cadera_norm"][0]
        )

        dx_rodilla = (
            elegida["rodilla_norm"][0]
            - otra["rodilla_norm"][0]
        )

        diferencia = (
            dx_cadera
            if abs(dx_cadera) >= 0.025
            else dx_rodilla
        )

        if abs(diferencia) >= 0.025:
            orden_actual = 1 if diferencia > 0 else -1

    orden_fijo = estado.get("_ext_orden_fijo")

    # Confirmar la identidad al comenzar.
    if orden_fijo is None:

        if orden_actual is None:
            return False

        # Comprobar la posición inicial calibrada.
        if base_x is not None:
            x_elegida = elegida["tobillo_norm"][0]
            x_otra = otra["tobillo_norm"][0]

            if (
                abs(x_elegida - base_x)
                > abs(x_otra - base_x) + 0.025
            ):
                estado.pop("_ext_orden_candidato", None)
                estado.pop("_ext_orden_desde", None)
                return False

        if estado.get("_ext_orden_candidato") != orden_actual:
            estado["_ext_orden_candidato"] = orden_actual
            estado["_ext_orden_desde"] = ahora
            return False

        if ahora - estado["_ext_orden_desde"] < 0.35:
            return False

        estado["_ext_orden_fijo"] = orden_actual

    elif (
        orden_actual is not None
        and orden_actual != orden_fijo
    ):
        return False

    # Verificar continuidad de la pierna.
    ultima = estado.get("_ext_ultima_posicion")
    tiempo_ultima = estado.get("_ext_ultimo_tiempo")

    # Si la otra pierna desaparece, aceptar únicamente
    # una identificación reciente de la pierna elegida.
    if otra is None and (
        ultima is None
        or tiempo_ultima is None
        or ahora - tiempo_ultima > 0.6
    ):
        return False

    if (
        ultima is not None
        and tiempo_ultima is not None
        and ahora - tiempo_ultima <= 0.6
    ):

        def distancia(p, q):
            return (
                (p[0] - q[0]) ** 2
                + (p[1] - q[1]) ** 2
            ) ** 0.5

        # Rechazar saltos bruscos de cadera o rodilla.
        if (
            distancia(
                elegida["cadera_norm"],
                ultima["cadera"]
            ) > 0.09
            or distancia(
                elegida["rodilla_norm"],
                ultima["rodilla"]
            ) > 0.09
        ):
            return False

        # Detectar si MediaPipe trasladó el tobillo
        # seleccionado hacia la otra pierna.
        if otra is not None:

            salto = distancia(
                elegida["tobillo_norm"],
                ultima["tobillo"]
            )

            alternativa = distancia(
                otra["tobillo_norm"],
                ultima["tobillo"]
            )

            if (
                salto > 0.12
                and alternativa < 0.05
                and alternativa + 0.05 < salto
            ):
                return False

    # Guardar los puntos confiables más recientes.
    estado["_ext_ultima_posicion"] = {
        "cadera": elegida["cadera_norm"],
        "rodilla": elegida["rodilla_norm"],
        "tobillo": elegida["tobillo_norm"]
    }

    estado["_ext_ultimo_tiempo"] = ahora

    return True

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
    # CALIBRACIÓN OBTENIDA EN EL TUTORIAL
    # ======================================================

    calibracion = st.session_state.get(
        "calibracion_ejercicio",
        None
    )

    calibracion_valida = (
        calibracion is not None
        and
        calibracion.get("ejercicio_id") == ejercicio["id"]
        and
        calibracion.get("lado") in ["RIGHT", "LEFT"]
    )

    # Solo exigimos calibración mientras el ejercicio
    # todavía no ha terminado.
    if (
        not st.session_state.ejercicio_completado
        and
        not calibracion_valida
    ):

        st.warning(
            "Este ejercicio necesita completar primero "
            "la fase de preparación."
        )

        if st.button(
            "Volver a preparar el ejercicio",
            use_container_width=True
        ):

            st.session_state.pantalla = "tutorial"
            st.rerun()

        return

    # ======================================================
    # PANTALLA FINAL
    # ======================================================

    if st.session_state.ejercicio_completado:

        hablar_fin_ejercicio_si_corresponde()

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

    hablar(
        f"Vamos a iniciar el ejercicio {ejercicio['nombre']}.",
        clave=f"inicio_ejercicio_{ejercicio['id']}",
        cooldown=60
    )

    # ======================================================
    # MODO DE EJECUCIÓN COMPACTO
    # ======================================================

    st.markdown(
        """
        <style>

        /* Reducir espacio superior solo en esta vista */
        .block-container {
            padding-top: 0.6rem !important;
        }

        /* Acercar los títulos de cámara y guía */
        h3 {
            margin-top: 0rem !important;
            margin-bottom: 0.35rem !important;
        }

        </style>
        """,
        unsafe_allow_html=True
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

        # Crear el panel de resultados una sola vez
        st.markdown("### Resultados")

        col_rep, col_est, col_tiempo = st.columns(3)

        with col_rep:
            repeticiones_placeholder = st.empty()

        with col_est:
            estrellas_placeholder = st.empty()

        with col_tiempo:
            tiempo_placeholder = st.empty()

        # Feedback gamificado que aparece
        # cuando se reconoce una repetición.
        feedback_placeholder = st.empty()

        # Reservar altura fija para que la barra no suba/baje
        feedback_placeholder.markdown(
            """
            <div style="
                height: 42px;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
            </div>
            """,
            unsafe_allow_html=True
        )

        # Barra de progreso independiente.
        barra_progreso_placeholder = st.empty()

        estado_placeholder = st.empty()

        # Ángulo mostrado debajo de la barra.
        angulo_placeholder = st.empty()

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

    # Control visual del feedback "+1"
    feedback_repeticion_hasta = 0

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

    # Recuperar las referencias obtenidas durante
    # los 13 segundos de preparación.
    estado_eval["base_tobillo_y"] = calibracion.get(
        "base_tobillo_y"
    )

    estado_eval["base_tobillo_x"] = calibracion.get(
        "base_tobillo_x"
    )

    estado_eval["base_cadera_y"] = calibracion.get(
        "base_cadera_y"
    )

    estado_eval["base_rodilla_y"] = calibracion.get(
        "base_rodilla_y"
    )

    # La pierna elegida durante la preparación
    # queda bloqueada para toda la ejecución.
    lado_calibrado = calibracion["lado"]

    estado_movimiento = "inicio"

    angulo_actual = 0

    angulo_minimo = 999

    angulo_maximo = 0

    angulos = []

    # ======================================================
    # CRONÓMETRO
    # ======================================================

    tiempo_inicio = time.time()

    # ======================================================
    # CONTROL DE ACTUALIZACIONES VISUALES
    # ======================================================

    ultimo_rep_mostrado = None
    ultimas_estrellas_mostradas = None
    ultimo_tiempo_mostrado = None

    ultimo_progreso_mostrado = None
    ultimo_estado_mostrado = None

    ultima_actualizacion_angulo = 0.0

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

        fps_inicio = time.perf_counter()
        frames_medidos = 0

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
                # USAR ÚNICAMENTE LA PIERNA CALIBRADA
                # ------------------------------------------

                puntos_pierna = obtener_puntos_pierna(
                    landmarks=landmarks,
                    width=width,
                    height=height,
                    lado=lado_calibrado
                )

                
                # ------------------------------------------
                # PROTEGER LA IDENTIDAD EN ABDUCCIÓN
                # ------------------------------------------

                if ejercicio.get("tipo_evaluacion") == "abduccion_cadera":

                    lado_opuesto = (
                        "RIGHT"
                        if lado_calibrado == "LEFT"
                        else "LEFT"
                    )

                    # La otra pierna se utiliza únicamente
                    # para comprobar la identidad.
                    puntos_otra = obtener_puntos_pierna(
                        landmarks=landmarks,
                        width=width,
                        height=height,
                        lado=lado_opuesto
                    )

                    identidad_correcta = identidad_abduccion_confiable(
                        puntos_pierna,
                        puntos_otra,
                        estado_eval,
                        calibracion.get("base_tobillo_x"),
                        time.monotonic()
                    )


                    if not identidad_correcta:

                        # No dibujar ni evaluar una pierna dudosa.
                        puntos_pierna = None

                        # Cancelar confirmaciones incompletas.
                        estado_eval["fase_candidata"] = None
                        estado_eval["fase_candidata_desde"] = None

                        # Registrar cuánto tiempo lleva perdida
                        # la identificación de la pierna.
                        ahora_perdida = time.monotonic()

                        inicio_perdida = estado_eval.get(
                            "_abd_perdida_desde"
                        )

                        if inicio_perdida is None:
                            estado_eval["_abd_perdida_desde"] = ahora_perdida

                        elif ahora_perdida - inicio_perdida >= 1.0:

                            # Solo reiniciar si la pérdida
                            # dura al menos un segundo.
                            estado_eval["fase"] = "inicio"
                            estado_eval["intento_activo"] = False
                            estado_eval["intento_candidato_desde"] = None

                    else:

                        # Identificación recuperada.
                        estado_eval.pop("_abd_perdida_desde", None)

                # ==========================================
                # MARCHA EN EL SITIO: DETECTAR AMBAS PIERNAS
                # ==========================================

                if (
                    ejercicio.get("tipo_evaluacion") == "marcha_sitio"
                    and puntos_pierna is not None
                ):

                    otro_lado = (
                        "LEFT" if lado_calibrado == "RIGHT"
                        else "RIGHT"
                    )

                    puntos_otra = obtener_puntos_pierna(
                        landmarks=landmarks,
                        width=width,
                        height=height,
                        lado=otro_lado
                    )

                    if puntos_otra is None:
                        puntos_pierna = None

                    else:
                        # Evitar aceptar una inversión evidente
                        # de las etiquetas izquierda y derecha.
                        diferencia_caderas = (
                            puntos_pierna["cadera_norm"][0]
                            - puntos_otra["cadera_norm"][0]
                        )

                        if abs(diferencia_caderas) >= 0.035:

                            orden_actual = (
                                1 if diferencia_caderas > 0 else -1
                            )

                            orden_fijo = estado_eval.get(
                                "_marcha_orden_caderas"
                            )

                            if orden_fijo is None:
                                estado_eval[
                                    "_marcha_orden_caderas"
                                ] = orden_actual

                            elif orden_actual != orden_fijo:
                                puntos_pierna = None

                        if puntos_pierna is not None:
                            puntos_pierna = dict(puntos_pierna)
                            puntos_pierna["lado"] = lado_calibrado
                            puntos_pierna["contraria"] = puntos_otra

                
                # ==========================================
                # EXTENSIÓN SENTADO: PROTEGER LA PIERNA
                # ==========================================

                if ejercicio.get("tipo_evaluacion") == "extension_rodilla":

                    otro_lado = (
                        "RIGHT" if lado_calibrado == "LEFT"
                        else "LEFT"
                    )

                    puntos_otra_ext = obtener_puntos_pierna(
                        landmarks=landmarks,
                        width=width,
                        height=height,
                        lado=otro_lado
                    )

                    confiable_ext = identidad_extension_confiable(
                        puntos_pierna,
                        puntos_otra_ext,
                        estado_eval,
                        calibracion.get("base_tobillo_x"),
                        time.monotonic()
                    )

                    if not confiable_ext:

                        # Evitar dibujar o evaluar una pierna
                        # cuya identidad sea dudosa.
                        puntos_pierna = None

                        # Cancelar confirmaciones incompletas.
                        estado_eval["fase_candidata"] = None
                        estado_eval["fase_candidata_desde"] = None

                        ahora_perdida = time.monotonic()

                        inicio = estado_eval.setdefault(
                            "_ext_perdida_desde",
                            ahora_perdida
                        )

                        # No reiniciar la fase por pérdidas breves.
                        if ahora_perdida - inicio >= 1.0:

                            estado_eval["fase"] = "inicio"
                            estado_eval["intento_activo"] = False
                            estado_eval["intento_candidato_desde"] = None
                            estado_eval["angulo_max_intento"] = None

                    else:

                        # La identidad fue recuperada.
                        estado_eval.pop(
                            "_ext_perdida_desde",
                            None
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

                    # STEP BÁSICO: obtener también la otra pierna
                    if ejercicio.get("tipo_evaluacion") == "step_basico":
                        lado_contrario = (
                            "LEFT" if lado_calibrado == "RIGHT" else "RIGHT"
                        )

                        puntos_pierna["lado"] = lado_calibrado
                        puntos_pierna["contraria"] = obtener_puntos_pierna(
                            landmarks=landmarks,
                            width=width,
                            height=height,
                            lado=lado_contrario
                        )

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
                    # Mostrar también la segunda pierna
                    # únicamente durante Marcha en el sitio.
                    if ejercicio.get("tipo_evaluacion") == "marcha_sitio":

                        dibujar_solo_pierna(
                            frame=frame,
                            puntos=puntos_pierna["contraria"],
                            angulo_actual=None
                        )

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
                        
                        # Mostrar feedback visual aproximadamente
                        # durante un segundo.

                        feedback_placeholder.markdown(
                            """
                            <style>

                            @keyframes subirFeedback {

                                0% {
                                    opacity: 0;
                                    transform: translateY(12px) scale(0.9);
                                }

                                20% {
                                    opacity: 1;
                                    transform: translateY(4px) scale(1.05);
                                }

                                70% {
                                    opacity: 1;
                                    transform: translateY(-4px) scale(1);
                                }

                                100% {
                                    opacity: 0;
                                    transform: translateY(-12px) scale(0.95);
                                }
                            }

                            .feedback-contenedor {
                                height: 42px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                            }

                            .feedback-repeticion {
                                font-size: 2rem;
                                font-weight: 800;
                                animation:
                                    subirFeedback
                                    0.9s
                                    ease-out
                                    forwards;
                            }

                            </style>

                            <div class="feedback-contenedor">
                                <div class="feedback-repeticion">
                                    +1 &nbsp; ¡Muy bien!
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

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
                        # Iniciar el aviso visual después de solicitar la voz
                        feedback_repeticion_hasta = time.time() + 1.8

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

            # Superponer animación cuando se valida una repetición
            frame = dibujar_feedback_repeticion(
                frame,
                feedback_repeticion_hasta
            )

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
            # RESULTADOS EN TIEMPO REAL (OPTIMIZADOS)
            # ==================================================

            tiempo_restante = max(
                duracion_maxima - tiempo_actual,
                0
            )

            # Actualizar repeticiones únicamente cuando cambien
            if repeticiones != ultimo_rep_mostrado:

                repeticiones_placeholder.metric(
                    "Repeticiones",
                    f"{repeticiones}/{total_repeticiones}"
                )

                ultimo_rep_mostrado = repeticiones


            # Actualizar estrellas únicamente cuando cambien
            if estrellas_ganadas != ultimas_estrellas_mostradas:

                estrellas_placeholder.metric(
                    "Estrellas",
                    estrellas_ganadas
                )

                ultimas_estrellas_mostradas = estrellas_ganadas


            # Actualizar tiempo únicamente cuando cambie el segundo
            if tiempo_restante != ultimo_tiempo_mostrado:

                tiempo_placeholder.metric(
                    "Tiempo restante",
                    f"{tiempo_restante} s"
                )

                ultimo_tiempo_mostrado = tiempo_restante

            # ==================================================
            # FEEDBACK GAMIFICADO
            # ==================================================

            if (
                feedback_repeticion_hasta > 0
                and
                time.time() >= feedback_repeticion_hasta
            ):

                feedback_placeholder.markdown(
                    """
                    <div style="
                        height: 42px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                feedback_repeticion_hasta = 0

            # ==================================================
            # BARRA DE PROGRESO
            # ==================================================

            if progreso != ultimo_progreso_mostrado:

                barra_progreso_placeholder.progress(
                    progreso
                )

                ultimo_progreso_mostrado = progreso

            # ==================================================
            # ESTADO DEL MOVIMIENTO
            # ==================================================

            if estado_movimiento != ultimo_estado_mostrado:

                estado_placeholder.caption(
                    f"Estado: {estado_movimiento}"
                )

                ultimo_estado_mostrado = estado_movimiento

            # ==================================================
            # ÁNGULO DEL PANEL LATERAL
            # ==================================================

            ahora_angulo = time.monotonic()

            # Actualizar el panel aproximadamente cada 250 ms
            if ahora_angulo - ultima_actualizacion_angulo >= 0.25:

                if angulo_actual is not None:

                    angulo_texto = (
                        f"{round(angulo_actual, 1)}°"
                    )

                else:

                    angulo_texto = "-"

                angulo_placeholder.metric(
                    "Ángulo",
                    angulo_texto
                )

                ultima_actualizacion_angulo = ahora_angulo

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
            frames_medidos += 1
            segundos = time.perf_counter() - fps_inicio

            if segundos >= 3:
                fps_actual = frames_medidos / segundos

                print(f"FPS reales de Activate: {fps_actual:.1f}")

                fps_inicio = time.perf_counter()
                frames_medidos = 0
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