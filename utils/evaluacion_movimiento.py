import cv2
import numpy as np
import time
import mediapipe as mp

mp_pose = mp.solutions.pose


def calcular_angulo(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    norma_ba = np.linalg.norm(ba)
    norma_bc = np.linalg.norm(bc)

    if norma_ba == 0 or norma_bc == 0:
        return None

    coseno = np.dot(ba, bc) / (norma_ba * norma_bc)
    coseno = np.clip(coseno, -1.0, 1.0)
    return np.degrees(np.arccos(coseno))


def obtener_puntos_pierna(landmarks, width, height, lado="RIGHT"):
    if lado == "LEFT":
        hip_id = mp_pose.PoseLandmark.LEFT_HIP.value
        knee_id = mp_pose.PoseLandmark.LEFT_KNEE.value
        ankle_id = mp_pose.PoseLandmark.LEFT_ANKLE.value
    else:
        hip_id = mp_pose.PoseLandmark.RIGHT_HIP.value
        knee_id = mp_pose.PoseLandmark.RIGHT_KNEE.value
        ankle_id = mp_pose.PoseLandmark.RIGHT_ANKLE.value

    cadera = landmarks[hip_id]
    rodilla = landmarks[knee_id]
    tobillo = landmarks[ankle_id]

    visibilidad_minima = 0.50

    if (
        cadera.visibility < visibilidad_minima
        or rodilla.visibility < visibilidad_minima
        or tobillo.visibility < visibilidad_minima
    ):
        return None

    punto_cadera = (int(cadera.x * width), int(cadera.y * height))
    punto_rodilla = (int(rodilla.x * width), int(rodilla.y * height))
    punto_tobillo = (int(tobillo.x * width), int(tobillo.y * height))

    return {
        "cadera": punto_cadera,
        "rodilla": punto_rodilla,
        "tobillo": punto_tobillo,
        "cadera_norm": (cadera.x, cadera.y),
        "rodilla_norm": (rodilla.x, rodilla.y),
        "tobillo_norm": (tobillo.x, tobillo.y),
    }

def obtener_muestra_calibracion(
    landmarks,
    width,
    height,
    lado="RIGHT"
):
    """
    Obtiene una muestra válida de cadera, rodilla y tobillo
    para una pierna durante la fase de preparación.

    MediaPipe no se modifica. Esta función solamente utiliza
    los landmarks que MediaPipe ya estimó.
    """

    puntos = obtener_puntos_pierna(
        landmarks=landmarks,
        width=width,
        height=height,
        lado=lado
    )

    if puntos is None:
        return None

    if lado == "LEFT":

        hip_id = (
            mp_pose.PoseLandmark.LEFT_HIP.value
        )

        knee_id = (
            mp_pose.PoseLandmark.LEFT_KNEE.value
        )

        ankle_id = (
            mp_pose.PoseLandmark.LEFT_ANKLE.value
        )

    else:

        hip_id = (
            mp_pose.PoseLandmark.RIGHT_HIP.value
        )

        knee_id = (
            mp_pose.PoseLandmark.RIGHT_KNEE.value
        )

        ankle_id = (
            mp_pose.PoseLandmark.RIGHT_ANKLE.value
        )

    visibilidades = [
        float(
            landmarks[hip_id].visibility
        ),
        float(
            landmarks[knee_id].visibility
        ),
        float(
            landmarks[ankle_id].visibility
        ),
    ]

    return {
        "lado": lado,

        "visibilidad_media": float(
            np.mean(visibilidades)
        ),

        "visibilidad_minima": float(
            min(visibilidades)
        ),

        "cadera_x": float(
            puntos["cadera_norm"][0]
        ),

        "cadera_y": float(
            puntos["cadera_norm"][1]
        ),

        "rodilla_x": float(
            puntos["rodilla_norm"][0]
        ),

        "rodilla_y": float(
            puntos["rodilla_norm"][1]
        ),

        "tobillo_x": float(
            puntos["tobillo_norm"][0]
        ),

        "tobillo_y": float(
            puntos["tobillo_norm"][1]
        ),
    }


def seleccionar_lado_calibracion(
    muestras_por_lado
):
    """
    Compara ambos lados durante la preparación y selecciona
    la pierna que presentó más frames válidos y mejor
    visibilidad.
    """

    mejor_lado = None
    mejor_puntaje = -1

    for lado in (
        "RIGHT",
        "LEFT"
    ):

        muestras = muestras_por_lado.get(
            lado,
            []
        )

        if not muestras:
            continue

        visibilidad_mediana = float(
            np.median(
                [
                    muestra["visibilidad_media"]
                    for muestra in muestras
                ]
            )
        )

        # Premia tanto la cantidad de frames válidos
        # como la calidad de detección.
        puntaje = (
            len(muestras)
            *
            visibilidad_mediana
        )

        if puntaje > mejor_puntaje:

            mejor_puntaje = puntaje
            mejor_lado = lado

    return mejor_lado


def calcular_referencia_estable(
    muestras,
    ventana=18,
    desplazamiento_maximo=0.035
):
    """
    Construye una referencia corporal usando la mediana
    de varios frames recientes.

    Solo devuelve una referencia cuando la posición del
    participante se mantiene suficientemente estable.
    """

    if len(muestras) < ventana:
        return None

    recientes = muestras[
        -ventana:
    ]

    claves_posicion = [
        "cadera_x",
        "cadera_y",
        "rodilla_x",
        "rodilla_y",
        "tobillo_x",
        "tobillo_y",
    ]

    # Verificar que la persona no se esté moviendo
    # demasiado durante la captura de referencia.
    for clave in claves_posicion:

        valores = np.array(
            [
                muestra[clave]
                for muestra in recientes
            ],
            dtype=float
        )

        if (
            np.ptp(valores)
            >
            desplazamiento_maximo
        ):
            return None

    return {
        "base_tobillo_y": float(
            np.median(
                [
                    muestra["tobillo_y"]
                    for muestra in recientes
                ]
            )
        ),

        "base_tobillo_x": float(
            np.median(
                [
                    muestra["tobillo_x"]
                    for muestra in recientes
                ]
            )
        ),

        "base_cadera_y": float(
            np.median(
                [
                    muestra["cadera_y"]
                    for muestra in recientes
                ]
            )
        ),

        "base_rodilla_y": float(
            np.median(
                [
                    muestra["rodilla_y"]
                    for muestra in recientes
                ]
            )
        ),

        "visibilidad_media": float(
            np.median(
                [
                    muestra["visibilidad_media"]
                    for muestra in recientes
                ]
            )
        ),

        "muestras_utilizadas": len(
            recientes
        ),
    }

def dibujar_solo_pierna(frame, puntos, angulo_actual):
    cadera = puntos["cadera"]
    rodilla = puntos["rodilla"]
    tobillo = puntos["tobillo"]

    cv2.line(frame, cadera, rodilla, (255, 255, 255), 4)
    cv2.line(frame, rodilla, tobillo, (255, 255, 255), 4)

    cv2.circle(frame, cadera, 8, (0, 0, 255), -1)
    cv2.circle(frame, rodilla, 10, (0, 255, 255), -1)
    cv2.circle(frame, tobillo, 8, (0, 0, 255), -1)

    if angulo_actual is not None:
        cv2.putText(
            frame,
            f"{int(angulo_actual)} grados",
            (rodilla[0] + 20, rodilla[1] + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )


def inicializar_estado_evaluacion():

    return {

        "fase": "inicio",

        "base_tobillo_y": None,
        "base_tobillo_x": None,
        "base_cadera_y": None,
        "base_rodilla_y": None,

        # Control de estabilidad de las fases
        "fase_candidata": None,
        "fase_candidata_desde": None,

        # Control de intentos
        "intento_activo": False,
        "intento_candidato_desde": None,
        "intento_no_completado_evento": False,
        "angulo_max_intento": None,
    }

def confirmar_fase_estable(
    estado_eval,
    fase_candidata,
    duracion_minima=0.30
):
    """
    Confirma una fase solamente si la condición
    se mantiene durante un tiempo mínimo.

    Esto ayuda a evitar falsos positivos producidos
    por cambios momentáneos de MediaPipe.
    """

    ahora = time.time()

    # Se detectó una fase candidata nueva
    if estado_eval.get("fase_candidata") != fase_candidata:

        estado_eval["fase_candidata"] = fase_candidata
        estado_eval["fase_candidata_desde"] = ahora

        return False

    inicio = estado_eval.get(
        "fase_candidata_desde"
    )

    if inicio is None:

        estado_eval["fase_candidata_desde"] = ahora

        return False

    # La condición se mantuvo el tiempo suficiente
    if ahora - inicio >= duracion_minima:

        estado_eval["fase_candidata"] = None
        estado_eval["fase_candidata_desde"] = None

        return True

    return False

def actualizar_inicio_intento(
    estado_eval,
    condicion_inicio,
    duracion_minima=0.20
):
    """
    Marca que un intento realmente comenzó
    cuando el movimiento parcial se mantiene
    durante un tiempo mínimo.
    """

    if estado_eval.get("intento_activo", False):
        return

    ahora = time.time()

    if condicion_inicio:

        if estado_eval.get("intento_candidato_desde") is None:

            estado_eval["intento_candidato_desde"] = ahora

        elif (
            ahora
            - estado_eval["intento_candidato_desde"]
            >= duracion_minima
        ):

            estado_eval["intento_activo"] = True

    else:

        estado_eval["intento_candidato_desde"] = None


def reiniciar_intento(estado_eval):
    """
    Limpia el estado de un intento.
    """

    estado_eval["intento_activo"] = False
    estado_eval["intento_candidato_desde"] = None
    estado_eval["angulo_max_intento"] = None


def detectar_retorno_sin_completar(
    estado_eval,
    condicion_retorno
):
    """
    Detecta cuando una persona inició el movimiento,
    pero regresó a la posición inicial sin alcanzar
    la fase objetivo.
    """

    if (
        estado_eval.get("intento_activo", False)
        and condicion_retorno
    ):

        estado_eval[
            "intento_no_completado_evento"
        ] = True

        reiniciar_intento(estado_eval)

        return True

    return False

def evaluar_extension_rodilla(angulo, estado_eval):
    """
    Ejercicio: Extensión de rodilla sentado.

    Movimiento esperado:
    rodilla flexionada -> rodilla extendida.

    Se confirma cada fase durante un tiempo mínimo
    y también se detectan intentos iniciados pero
    no completados.
    """

    rep_valida = False

    # Este valor solo dura un ciclo/frame.
    # ejercicio.py lo leerá si ocurrió un intento no completado.
    estado_eval["intento_no_completado_evento"] = False

    if angulo is None:

        estado_eval["fase_candidata"] = None
        estado_eval["fase_candidata_desde"] = None

        estado_eval["intento_candidato_desde"] = None

        return (
            rep_valida,
            estado_eval,
            "No se detecta correctamente la rodilla"
        )

    ahora = time.time()

    # ==================================================
    # DETECTAR QUE REALMENTE COMENZÓ UN INTENTO
    # ==================================================

    if (
        estado_eval["fase"] == "flexionado"
        and angulo >= 130
    ):

        if estado_eval["intento_candidato_desde"] is None:

            estado_eval["intento_candidato_desde"] = ahora

        elif (
            ahora
            - estado_eval["intento_candidato_desde"]
            >= 0.20
        ):

            estado_eval["intento_activo"] = True

            if estado_eval["angulo_max_intento"] is None:

                estado_eval["angulo_max_intento"] = angulo

            else:

                estado_eval["angulo_max_intento"] = max(
                    estado_eval["angulo_max_intento"],
                    angulo
                )

    elif (
        estado_eval["fase"] == "flexionado"
        and not estado_eval["intento_activo"]
    ):

        estado_eval["intento_candidato_desde"] = None

    # ==================================================
    # INTENTO INICIADO PERO NO COMPLETADO
    # ==================================================

    if (
        estado_eval["fase"] == "flexionado"
        and
        estado_eval["intento_activo"]
        and
        angulo < 120
    ):

        estado_eval["intento_no_completado_evento"] = True

        estado_eval["intento_activo"] = False
        estado_eval["intento_candidato_desde"] = None
        estado_eval["angulo_max_intento"] = None

    # ==================================================
    # FASE FLEXIONADA
    # ==================================================

    if angulo < 120:

        if estado_eval["fase"] != "flexionado":

            flexion_confirmada = confirmar_fase_estable(
                estado_eval,
                "flexionado",
                duracion_minima=0.30
            )

            if flexion_confirmada:

                estado_eval["fase"] = "flexionado"

                mensaje = (
                    "Buena flexión, ahora estira la pierna"
                )

            else:

                mensaje = (
                    "Mantén la posición de flexión un momento"
                )

        else:

            mensaje = (
                "Buena flexión, ahora estira la pierna"
            )

    # ==================================================
    # FASE EXTENDIDA
    # ==================================================

    elif (
        angulo > 150
        and
        estado_eval["fase"] == "flexionado"
    ):

        extension_confirmada = confirmar_fase_estable(
            estado_eval,
            "extendido",
            duracion_minima=0.30
        )

        if extension_confirmada:

            rep_valida = True

            estado_eval["fase"] = "extendido"

            # El intento terminó correctamente
            estado_eval["intento_activo"] = False
            estado_eval["intento_candidato_desde"] = None
            estado_eval["angulo_max_intento"] = None

            mensaje = (
                "Repetición válida: rodilla extendida"
            )

        else:

            mensaje = (
                "Mantén la extensión un momento"
            )

    # ==================================================
    # ZONA INTERMEDIA
    # ==================================================

    else:

        estado_eval["fase_candidata"] = None
        estado_eval["fase_candidata_desde"] = None

        mensaje = (
            "Realiza el movimiento de forma lenta y controlada"
        )

    return rep_valida, estado_eval, mensaje


def evaluar_sentadilla(
    angulo,
    estado_eval,
    umbral_bajada=130,
    umbral_subida=150
):

    rep_valida = False

    estado_eval[
        "intento_no_completado_evento"
    ] = False

    if angulo is None:

        return (
            rep_valida,
            estado_eval,
            "No se detecta correctamente la rodilla"
        )

    abajo = angulo < umbral_bajada
    arriba = angulo > umbral_subida

    # Punto intermedio que indica que
    # realmente comenzó a flexionar.
    umbral_inicio_intento = (
        umbral_bajada + umbral_subida
    ) / 2

    movimiento_parcial = (
        angulo < umbral_inicio_intento
    )

    # ------------------------------------------
    # POSICIÓN INICIAL
    # ------------------------------------------

    if estado_eval["fase"] == "inicio":

        if arriba:

            if confirmar_fase_estable(
                estado_eval,
                "arriba",
                0.30
            ):

                estado_eval["fase"] = "arriba"

                mensaje = (
                    "Posición inicial detectada, "
                    "puedes comenzar"
                )

            else:

                mensaje = (
                    "Mantén la posición de pie un momento"
                )

        else:

            mensaje = (
                "Colócate de pie para comenzar"
            )

        return rep_valida, estado_eval, mensaje

    # ------------------------------------------
    # DESDE ARRIBA: COMIENZA SENTADILLA
    # ------------------------------------------

    if estado_eval["fase"] == "arriba":

        actualizar_inicio_intento(
            estado_eval,
            movimiento_parcial,
            0.20
        )

        if abajo:

            if confirmar_fase_estable(
                estado_eval,
                "abajo",
                0.30
            ):

                estado_eval["fase"] = "abajo"

                reiniciar_intento(
                    estado_eval
                )

                mensaje = (
                    "Buena bajada, ahora sube lentamente"
                )

            else:

                mensaje = (
                    "Mantén la posición baja un momento"
                )

        elif detectar_retorno_sin_completar(
            estado_eval,
            arriba
        ):

            mensaje = (
                "Intenta flexionar un poco más las rodillas"
            )

        else:

            mensaje = (
                "Flexiona las rodillas con control"
            )

    # ------------------------------------------
    # REGRESO ARRIBA
    # ------------------------------------------

    elif estado_eval["fase"] == "abajo":

        if arriba:

            if confirmar_fase_estable(
                estado_eval,
                "arriba",
                0.30
            ):

                rep_valida = True
                estado_eval["fase"] = "arriba"

                mensaje = (
                    "Repetición válida: "
                    "subiste con control"
                )

            else:

                mensaje = (
                    "Mantén la posición de pie un momento"
                )

        else:

            mensaje = (
                "Ahora vuelve a subir lentamente"
            )

    return rep_valida, estado_eval, mensaje


def evaluar_elevacion_pierna_recta(
    angulo,
    puntos,
    estado_eval
):

    rep_valida = False

    estado_eval[
        "intento_no_completado_evento"
    ] = False

    if angulo is None:

        return (
            rep_valida,
            estado_eval,
            "No se detecta correctamente la pierna"
        )

    tobillo_y = puntos["tobillo_norm"][1]

    if estado_eval["base_tobillo_y"] is None:

        estado_eval["base_tobillo_y"] = tobillo_y

    diferencia_altura = (
        estado_eval["base_tobillo_y"]
        - tobillo_y
    )

    rodilla_extendida = angulo > 145

    pierna_elevada = diferencia_altura > 0.10
    pierna_abajo = diferencia_altura < 0.04

    movimiento_parcial = (
        diferencia_altura > 0.05
    )

    # ------------------------------------------
    # POSICIÓN INICIAL
    # ------------------------------------------

    if estado_eval["fase"] == "inicio":

        if pierna_abajo:

            if confirmar_fase_estable(
                estado_eval,
                "abajo",
                0.30
            ):

                estado_eval["fase"] = "abajo"

                mensaje = (
                    "Posición inicial detectada"
                )

            else:

                mensaje = (
                    "Mantén la pierna abajo un momento"
                )

        else:

            mensaje = (
                "Coloca la pierna en la posición inicial"
            )

        return rep_valida, estado_eval, mensaje

    # ------------------------------------------
    # SUBIDA
    # ------------------------------------------

    if estado_eval["fase"] == "abajo":

        actualizar_inicio_intento(
            estado_eval,
            movimiento_parcial,
            0.20
        )

        if (
            pierna_elevada
            and rodilla_extendida
        ):

            if confirmar_fase_estable(
                estado_eval,
                "arriba",
                0.30
            ):

                estado_eval["fase"] = "arriba"

                reiniciar_intento(
                    estado_eval
                )

                mensaje = (
                    "Pierna elevada, "
                    "ahora baja lentamente"
                )

            else:

                mensaje = (
                    "Mantén la pierna elevada un momento"
                )

        elif detectar_retorno_sin_completar(
            estado_eval,
            pierna_abajo
        ):

            mensaje = (
                "Intenta elevar un poco más la pierna"
            )

        elif not rodilla_extendida:

            mensaje = (
                "Mantén la rodilla más extendida"
            )

        else:

            mensaje = (
                "Eleva la pierna lentamente"
            )

    # ------------------------------------------
    # BAJADA
    # ------------------------------------------

    elif estado_eval["fase"] == "arriba":

        if pierna_abajo:

            if confirmar_fase_estable(
                estado_eval,
                "abajo",
                0.30
            ):

                rep_valida = True
                estado_eval["fase"] = "abajo"

                mensaje = (
                    "Repetición válida: elevación completa"
                )

            else:

                mensaje = (
                    "Mantén la posición inicial un momento"
                )

        else:

            mensaje = (
                "Baja lentamente la pierna"
            )

    return rep_valida, estado_eval, mensaje


def evaluar_step_basico(
    angulo,
    puntos,
    estado_eval
):

    rep_valida = False

    estado_eval[
        "intento_no_completado_evento"
    ] = False

    if angulo is None:

        return (
            rep_valida,
            estado_eval,
            "No se detecta correctamente la pierna"
        )

    tobillo_y = puntos["tobillo_norm"][1]

    if estado_eval["base_tobillo_y"] is None:
        estado_eval["base_tobillo_y"] = tobillo_y

    diferencia_altura = (
        estado_eval["base_tobillo_y"]
        - tobillo_y
    )

    subio = (
        diferencia_altura > 0.08
        and angulo > 130
    )

    bajo = diferencia_altura < 0.03

    movimiento_parcial = (
        diferencia_altura > 0.04
    )

    if estado_eval["fase"] == "inicio":

        if bajo:

            if confirmar_fase_estable(
                estado_eval,
                "abajo",
                0.30
            ):

                estado_eval["fase"] = "abajo"
                mensaje = "Posición inicial detectada"

            else:

                mensaje = (
                    "Mantén la posición inicial un momento"
                )

        else:

            mensaje = "Colócate en la posición inicial"

        return rep_valida, estado_eval, mensaje

    if estado_eval["fase"] == "abajo":

        actualizar_inicio_intento(
            estado_eval,
            movimiento_parcial,
            0.20
        )

        if subio:

            if confirmar_fase_estable(
                estado_eval,
                "arriba",
                0.30
            ):

                estado_eval["fase"] = "arriba"

                reiniciar_intento(
                    estado_eval
                )

                mensaje = (
                    "Subida detectada, "
                    "ahora baja con control"
                )

            else:

                mensaje = (
                    "Mantén la subida un momento"
                )

        elif detectar_retorno_sin_completar(
            estado_eval,
            bajo
        ):

            mensaje = (
                "Intenta completar un poco más la subida"
            )

        else:

            mensaje = (
                "Realiza la subida de forma controlada"
            )

    elif estado_eval["fase"] == "arriba":

        if bajo:

            if confirmar_fase_estable(
                estado_eval,
                "abajo",
                0.30
            ):

                rep_valida = True
                estado_eval["fase"] = "abajo"

                mensaje = (
                    "Repetición válida: step completo"
                )

            else:

                mensaje = (
                    "Mantén la posición inicial un momento"
                )

        else:

            mensaje = (
                "Baja de forma controlada"
            )

    return rep_valida, estado_eval, mensaje


def evaluar_puente_gluteo(
    angulo,
    puntos,
    estado_eval
):

    rep_valida = False

    estado_eval[
        "intento_no_completado_evento"
    ] = False

    cadera_y = puntos["cadera_norm"][1]

    if estado_eval.get("base_cadera_y") is None:
        estado_eval["base_cadera_y"] = cadera_y

    diferencia_altura = (
        estado_eval["base_cadera_y"]
        - cadera_y
    )

    pelvis_arriba = diferencia_altura > 0.08
    pelvis_abajo = diferencia_altura < 0.03

    movimiento_parcial = (
        diferencia_altura > 0.04
    )

    if estado_eval["fase"] == "inicio":

        if pelvis_abajo:

            if confirmar_fase_estable(
                estado_eval,
                "abajo",
                0.30
            ):

                estado_eval["fase"] = "abajo"
                mensaje = "Posición inicial detectada"

            else:

                mensaje = (
                    "Mantén la posición inicial un momento"
                )

        else:

            mensaje = (
                "Coloca la pelvis en la posición inicial"
            )

        return rep_valida, estado_eval, mensaje

    if estado_eval["fase"] == "abajo":

        actualizar_inicio_intento(
            estado_eval,
            movimiento_parcial,
            0.20
        )

        if pelvis_arriba:

            if confirmar_fase_estable(
                estado_eval,
                "arriba",
                0.30
            ):

                estado_eval["fase"] = "arriba"

                reiniciar_intento(
                    estado_eval
                )

                mensaje = (
                    "Puente detectado, "
                    "baja lentamente"
                )

            else:

                mensaje = (
                    "Mantén la pelvis elevada un momento"
                )

        elif detectar_retorno_sin_completar(
            estado_eval,
            pelvis_abajo
        ):

            mensaje = (
                "Intenta elevar un poco más la pelvis"
            )

        else:

            mensaje = (
                "Eleva la pelvis con control"
            )

    elif estado_eval["fase"] == "arriba":

        if pelvis_abajo:

            if confirmar_fase_estable(
                estado_eval,
                "abajo",
                0.30
            ):

                rep_valida = True
                estado_eval["fase"] = "abajo"

                mensaje = (
                    "Repetición válida: puente completo"
                )

            else:

                mensaje = (
                    "Mantén la posición inicial un momento"
                )

        else:

            mensaje = (
                "Baja lentamente la pelvis"
            )

    return rep_valida, estado_eval, mensaje


def evaluar_abduccion_cadera(
    angulo,
    puntos,
    estado_eval
):

    rep_valida = False

    estado_eval[
        "intento_no_completado_evento"
    ] = False

    tobillo_x = puntos["tobillo_norm"][0]

    if estado_eval["base_tobillo_x"] is None:
        estado_eval["base_tobillo_x"] = tobillo_x

    desplazamiento = (
        tobillo_x
        - estado_eval["base_tobillo_x"]
    )

    desplazamiento_abs = abs(
        desplazamiento
    )

    pierna_abierta = desplazamiento_abs > 0.08
    pierna_centro = desplazamiento_abs < 0.03

    movimiento_parcial = (
        desplazamiento_abs > 0.04
    )

    if estado_eval["fase"] == "inicio":

        if pierna_centro:

            if confirmar_fase_estable(
                estado_eval,
                "centro",
                0.30
            ):

                estado_eval["fase"] = "centro"
                mensaje = "Posición inicial detectada"

            else:

                mensaje = (
                    "Mantén la pierna al centro un momento"
                )

        else:

            mensaje = (
                "Coloca la pierna en la posición inicial"
            )

        return rep_valida, estado_eval, mensaje

    if estado_eval["fase"] == "centro":

        actualizar_inicio_intento(
            estado_eval,
            movimiento_parcial,
            0.20
        )

        if pierna_abierta:

            if confirmar_fase_estable(
                estado_eval,
                "abierta",
                0.30
            ):

                estado_eval["fase"] = "abierta"

                reiniciar_intento(
                    estado_eval
                )

                mensaje = (
                    "Pierna separada, "
                    "vuelve lentamente al centro"
                )

            else:

                mensaje = (
                    "Mantén la pierna separada un momento"
                )

        elif detectar_retorno_sin_completar(
            estado_eval,
            pierna_centro
        ):

            mensaje = (
                "Intenta separar un poco más la pierna"
            )

        else:

            mensaje = (
                "Separa la pierna lateralmente"
            )

    elif estado_eval["fase"] == "abierta":

        if pierna_centro:

            if confirmar_fase_estable(
                estado_eval,
                "centro",
                0.30
            ):

                rep_valida = True
                estado_eval["fase"] = "centro"

                mensaje = (
                    "Repetición válida: "
                    "abducción completa"
                )

            else:

                mensaje = (
                    "Mantén la posición inicial un momento"
                )

        else:

            mensaje = (
                "Vuelve lentamente al centro"
            )

    return rep_valida, estado_eval, mensaje


def evaluar_sit_to_stand(
    angulo,
    estado_eval
):

    rep_valida = False

    estado_eval[
        "intento_no_completado_evento"
    ] = False

    if angulo is None:

        return (
            rep_valida,
            estado_eval,
            "No se detecta correctamente la rodilla"
        )

    sentado = angulo < 120
    de_pie = angulo > 155

    movimiento_parcial = (
        angulo > 135
    )

    # ------------------------------------------
    # POSICIÓN INICIAL SENTADO
    # ------------------------------------------

    if estado_eval["fase"] == "inicio":

        if sentado:

            if confirmar_fase_estable(
                estado_eval,
                "sentado",
                0.30
            ):

                estado_eval["fase"] = "sentado"

                mensaje = (
                    "Posición inicial detectada"
                )

            else:

                mensaje = (
                    "Mantén la posición sentado un momento"
                )

        else:

            mensaje = (
                "Siéntate para comenzar el ejercicio"
            )

        return rep_valida, estado_eval, mensaje

    # ------------------------------------------
    # LEVANTARSE
    # ------------------------------------------

    if estado_eval["fase"] == "sentado":

        actualizar_inicio_intento(
            estado_eval,
            movimiento_parcial,
            0.20
        )

        if de_pie:

            if confirmar_fase_estable(
                estado_eval,
                "de_pie",
                0.30
            ):

                estado_eval["fase"] = "de_pie"

                reiniciar_intento(
                    estado_eval
                )

                mensaje = (
                    "De pie detectado, "
                    "vuelve a sentarte con control"
                )

            else:

                mensaje = (
                    "Mantén la posición de pie un momento"
                )

        elif detectar_retorno_sin_completar(
            estado_eval,
            sentado
        ):

            mensaje = (
                "Intenta completar el movimiento al levantarte"
            )

        else:

            mensaje = (
                "Levántate de forma controlada"
            )

    # ------------------------------------------
    # VOLVER A SENTARSE
    # ------------------------------------------

    elif estado_eval["fase"] == "de_pie":

        if sentado:

            if confirmar_fase_estable(
                estado_eval,
                "sentado",
                0.30
            ):

                rep_valida = True
                estado_eval["fase"] = "sentado"

                mensaje = (
                    "Repetición válida: "
                    "sentado y de pie completo"
                )

            else:

                mensaje = (
                    "Mantén la posición sentado un momento"
                )

        else:

            mensaje = (
                "Siéntate lentamente y con control"
            )

    return rep_valida, estado_eval, mensaje


def evaluar_marcha_sitio(
    angulo,
    puntos,
    estado_eval
):

    rep_valida = False

    estado_eval[
        "intento_no_completado_evento"
    ] = False

    rodilla_y = puntos["rodilla_norm"][1]

    if estado_eval.get("base_rodilla_y") is None:
        estado_eval["base_rodilla_y"] = rodilla_y

    diferencia_altura = (
        estado_eval["base_rodilla_y"]
        - rodilla_y
    )

    rodilla_arriba = diferencia_altura > 0.08
    rodilla_abajo = diferencia_altura < 0.03

    movimiento_parcial = (
        diferencia_altura > 0.04
    )

    if estado_eval["fase"] == "inicio":

        if rodilla_abajo:

            if confirmar_fase_estable(
                estado_eval,
                "abajo",
                0.30
            ):

                estado_eval["fase"] = "abajo"
                mensaje = "Posición inicial detectada"

            else:

                mensaje = (
                    "Mantén la posición inicial un momento"
                )

        else:

            mensaje = (
                "Colócate en la posición inicial"
            )

        return rep_valida, estado_eval, mensaje

    if estado_eval["fase"] == "abajo":

        actualizar_inicio_intento(
            estado_eval,
            movimiento_parcial,
            0.20
        )

        if rodilla_arriba:

            if confirmar_fase_estable(
                estado_eval,
                "arriba",
                0.30
            ):

                estado_eval["fase"] = "arriba"

                reiniciar_intento(
                    estado_eval
                )

                mensaje = (
                    "Rodilla elevada, "
                    "baja con control"
                )

            else:

                mensaje = (
                    "Mantén la rodilla elevada un momento"
                )

        elif detectar_retorno_sin_completar(
            estado_eval,
            rodilla_abajo
        ):

            mensaje = (
                "Intenta elevar un poco más la rodilla"
            )

        else:

            mensaje = (
                "Eleva la rodilla con control"
            )

    elif estado_eval["fase"] == "arriba":

        if rodilla_abajo:

            if confirmar_fase_estable(
                estado_eval,
                "abajo",
                0.30
            ):

                rep_valida = True
                estado_eval["fase"] = "abajo"

                mensaje = (
                    "Repetición válida: marcha en el sitio"
                )

            else:

                mensaje = (
                    "Mantén la posición inicial un momento"
                )

        else:

            mensaje = (
                "Baja la rodilla con control"
            )

    return rep_valida, estado_eval, mensaje


def evaluar_movimiento(ejercicio, angulo, puntos, estado_eval):
    tipo = ejercicio.get("tipo_evaluacion", "extension_rodilla")

    if tipo == "extension_rodilla":
        return evaluar_extension_rodilla(angulo, estado_eval)

    if tipo == "elevacion_pierna_recta":
        return evaluar_elevacion_pierna_recta(angulo, puntos, estado_eval)

    if tipo == "mini_sentadilla":
        return evaluar_sentadilla(angulo, estado_eval, umbral_bajada=135, umbral_subida=150)

    if tipo == "puente_gluteo":
        return evaluar_puente_gluteo(angulo, puntos, estado_eval)

    if tipo == "step_basico":
        return evaluar_step_basico(angulo, puntos, estado_eval)

    if tipo == "abduccion_cadera":
        return evaluar_abduccion_cadera(angulo, puntos, estado_eval)

    if tipo == "sit_to_stand":
        return evaluar_sit_to_stand(angulo, estado_eval)

    if tipo == "marcha_sitio":
        return evaluar_marcha_sitio(angulo, puntos, estado_eval)

    return evaluar_extension_rodilla(angulo, estado_eval)