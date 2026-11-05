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

    # Colores en formato BGR de OpenCV
    turquesa = (225, 182, 0)       # Celeste intenso
    azul = (183, 95, 15)           # Azul principal
    sombra = (72, 66, 56)          # Gris oscuro
    blanco = (255, 255, 255)

    # Conexiones con contorno para mayor visibilidad
    for inicio, fin in [
        (cadera, rodilla),
        (rodilla, tobillo)
    ]:
        cv2.line(
            frame, inicio, fin,
            sombra, 9, cv2.LINE_AA
        )

        cv2.line(
            frame, inicio, fin,
            turquesa, 5, cv2.LINE_AA
        )

    # Articulaciones grandes y fáciles de identificar
    for punto in [cadera, rodilla, tobillo]:
        cv2.circle(
            frame, punto,
            12, blanco, -1, cv2.LINE_AA
        )

        cv2.circle(
            frame, punto,
            8, azul, -1, cv2.LINE_AA
        )

    # Mostrar el ángulo junto a la rodilla
    if angulo_actual is not None:
        texto = f"{int(angulo_actual)} grados"

        x = max(
            10,
            min(rodilla[0] + 18, frame.shape[1] - 110)
        )

        y = max(
            28,
            min(rodilla[1] - 15, frame.shape[0] - 10)
        )

        cv2.putText(
            frame, texto, (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65, sombra, 4, cv2.LINE_AA
        )

        cv2.putText(
            frame, texto, (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65, blanco, 2, cv2.LINE_AA
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
    umbral_bajada=145,
    umbral_subida=155
):
    """
    Mini sentadilla.

    Movimiento:
    de pie -> flexión parcial -> volver de pie.

    Se utilizan umbrales moderados para evitar exigir
    una sentadilla profunda a adultos mayores.
    """

    rep_valida = False

    if angulo is None:

        return (
            rep_valida,
            estado_eval,
            "No se detecta correctamente la rodilla"
        )

    # ------------------------------------------
    # BAJADA
    # ------------------------------------------

    if (
        angulo < umbral_bajada
        and
        estado_eval["fase"] in [
            "inicio",
            "arriba"
        ]
    ):

        estable = confirmar_fase_estable(
            estado_eval,
            "abajo",
            duracion_minima=0.15
        )

        if estable:

            estado_eval["fase"] = "abajo"

            mensaje = (
                "Muy bien, ahora vuelve a subir"
            )

        else:

            mensaje = (
                "Mantén la flexión un momento"
            )

    # ------------------------------------------
    # SUBIDA
    # ------------------------------------------

    elif (
        angulo > umbral_subida
        and
        estado_eval["fase"] == "abajo"
    ):

        estable = confirmar_fase_estable(
            estado_eval,
            "arriba",
            duracion_minima=0.15
        )

        if estable:

            rep_valida = True

            estado_eval["fase"] = "arriba"

            mensaje = (
                "Repetición válida"
            )

        else:

            mensaje = (
                "Termina de subir"
            )

    else:

        estado_eval[
            "fase_candidata"
        ] = None

        estado_eval[
            "fase_candidata_desde"
        ] = None

        mensaje = (
            "Flexiona y vuelve a subir con control"
        )

    return (
        rep_valida,
        estado_eval,
        mensaje
    )


def evaluar_elevacion_pierna_recta(
    angulo,
    puntos,
    estado_eval
):
    """
    Elevación de pierna recta.

    Utiliza la posición inicial calibrada del tobillo.
    La repetición se completa cuando:
    1. la pierna se eleva manteniendo la rodilla extendida;
    2. vuelve cerca de la posición inicial.
    """

    rep_valida = False

    if angulo is None:
        return (
            rep_valida,
            estado_eval,
            "No se detecta correctamente la pierna"
        )

    tobillo_y = puntos["tobillo_norm"][1]

    base_tobillo_y = estado_eval.get(
        "base_tobillo_y"
    )

    if base_tobillo_y is None:
        estado_eval["base_tobillo_y"] = tobillo_y
        base_tobillo_y = tobillo_y

    diferencia_altura = (
        base_tobillo_y - tobillo_y
    )

    # Más tolerante para adultos mayores.
    rodilla_extendida = angulo > 140

    # Antes era 0.10.
    # Con la calibración podemos aceptar menor amplitud.
    pierna_elevada = (
        diferencia_altura > 0.055
    )

    # Consideramos que volvió a la posición inicial.
    pierna_abajo = (
        diferencia_altura < 0.025
    )

    # ------------------------------------------
    # PIERNA SUBIENDO / ARRIBA
    # ------------------------------------------

    if (
        rodilla_extendida
        and
        pierna_elevada
        and
        estado_eval["fase"] in [
            "inicio",
            "abajo"
        ]
    ):

        estable = confirmar_fase_estable(
            estado_eval,
            "arriba",
            duracion_minima=0.15
        )

        if estable:

            estado_eval["fase"] = "arriba"

            mensaje = (
                "Muy bien, ahora baja la pierna"
            )

        else:

            mensaje = (
                "Mantén la pierna elevada un momento"
            )

    # ------------------------------------------
    # REGRESO A POSICIÓN INICIAL
    # ------------------------------------------

    elif (
        pierna_abajo
        and
        estado_eval["fase"] == "arriba"
    ):

        estable = confirmar_fase_estable(
            estado_eval,
            "abajo",
            duracion_minima=0.15
        )

        if estable:

            rep_valida = True

            estado_eval["fase"] = "abajo"

            mensaje = (
                "Repetición válida"
            )

        else:

            mensaje = (
                "Vuelve a la posición inicial"
            )

    else:

        estado_eval[
            "fase_candidata"
        ] = None

        estado_eval[
            "fase_candidata_desde"
        ] = None

        if not rodilla_extendida:

            mensaje = (
                "Mantén la pierna más recta"
            )

        else:

            mensaje = (
                "Eleva la pierna con control"
            )

    return (
        rep_valida,
        estado_eval,
        mensaje
    )



def evaluar_step_basico(angulo, puntos, estado_eval):
    """Reconoce suelo -> un pie arriba -> dos pies arriba -> suelo."""
    estado_eval["intento_no_completado_evento"] = False

    contrario = puntos.get("contraria") if puntos else None
    if contrario is None:
        estado_eval.pop("_step_candidato", None)
        estado_eval.pop("_step_desde", None)
        return False, estado_eval, "Mantén visibles ambas piernas"

    ahora = time.monotonic()
    ultima = estado_eval.get("_step_ultima_deteccion")

    if ultima is not None and ahora - ultima > 1.5:
        estado_eval["fase"] = "inicio"
        estado_eval.pop("_step_base", None)
        estado_eval.pop("_step_candidato", None)
        estado_eval.pop("_step_desde", None)

    estado_eval["_step_ultima_deteccion"] = ahora

    if puntos.get("lado") == "LEFT":
        izquierda, derecha = puntos, contrario
    else:
        izquierda, derecha = contrario, puntos

    tobillo_izq = izquierda["tobillo_norm"][1]
    tobillo_der = derecha["tobillo_norm"][1]
    cadera = (
        izquierda["cadera_norm"][1] + derecha["cadera_norm"][1]
    ) / 2

    escala = (
        abs(izquierda["cadera_norm"][1] - tobillo_izq)
        + abs(derecha["cadera_norm"][1] - tobillo_der)
    ) / 2
    escala = max(0.14, escala)

    umbral_pie = max(0.045, 0.17 * escala)
    umbral_cadera = max(0.026, 0.10 * escala)
    tolerancia = max(0.025, 0.09 * escala)

    if "_step_base" not in estado_eval:
        estado_eval["_step_base"] = (tobillo_izq, tobillo_der, cadera)

    base_izq, base_der, base_cadera = estado_eval["_step_base"]
    elevacion_izq = base_izq - tobillo_izq
    elevacion_der = base_der - tobillo_der
    elevacion_cadera = base_cadera - cadera

    solo_uno = (
        (elevacion_izq > umbral_pie and elevacion_der < 0.65 * umbral_pie)
        or (elevacion_der > umbral_pie and elevacion_izq < 0.65 * umbral_pie)
    )

    ambos_arriba = (
        elevacion_izq > umbral_pie
        and elevacion_der > umbral_pie
        and elevacion_cadera > umbral_cadera
    )

    ambos_abajo = (
        abs(elevacion_izq) < tolerancia
        and abs(elevacion_der) < tolerancia
        and abs(elevacion_cadera) < max(0.038, 0.12 * escala)
    )

    def confirmar(etapa, condicion, duracion):
        if not condicion:
            estado_eval.pop("_step_candidato", None)
            estado_eval.pop("_step_desde", None)
            return False

        if estado_eval.get("_step_candidato") != etapa:
            estado_eval["_step_candidato"] = etapa
            estado_eval["_step_desde"] = ahora
            return False

        if ahora - estado_eval["_step_desde"] >= duracion:
            estado_eval.pop("_step_candidato", None)
            estado_eval.pop("_step_desde", None)
            return True

        return False

    fase = estado_eval["fase"]

    if fase == "inicio":
        if confirmar("inicio", ambos_abajo, 0.25):
            estado_eval["fase"] = "abajo"
        return False, estado_eval, "Comienza con ambos pies en el suelo"

    if fase == "abajo":
        if confirmar("primero", solo_uno, 0.12):
            estado_eval["fase"] = "subiendo"
            return False, estado_eval, "Ahora sube el segundo pie"
        return False, estado_eval, "Coloca un pie sobre el escalón"

    if fase == "subiendo":
        if confirmar("ambos", ambos_arriba, 0.20):
            estado_eval["fase"] = "arriba"
            return False, estado_eval, "Ambos pies arriba; baja con control"

        if ambos_abajo:
            estado_eval["fase"] = "abajo"
            estado_eval["intento_no_completado_evento"] = True
            return False, estado_eval, "Intenta completar la subida"

        return False, estado_eval, "Sube el otro pie y eleva el cuerpo"

    if fase == "arriba":
        if elevacion_izq < 0.6 * umbral_pie or elevacion_der < 0.6 * umbral_pie:
            estado_eval["fase"] = "bajando"
            estado_eval.pop("_step_candidato", None)
            estado_eval.pop("_step_desde", None)
        return False, estado_eval, "Baja un pie y después el otro"

    if fase == "bajando":
        if confirmar("fin", ambos_abajo, 0.24):
            estado_eval["fase"] = "abajo"
            return True, estado_eval, "Step completo"
        return False, estado_eval, "Vuelve con ambos pies al suelo"

    estado_eval["fase"] = "inicio"
    return False, estado_eval, "Colócate frente al escalón"



def evaluar_puente_gluteo(
    angulo,
    puntos,
    estado_eval
):
    """
    Puente glúteo.

    Movimiento:
    pelvis en posición inicial
    -> elevar pelvis
    -> regresar a posición inicial.

    Se utiliza la referencia de cadera obtenida
    durante la calibración previa.
    """

    rep_valida = False

    cadera_y = puntos[
        "cadera_norm"
    ][1]

    base_cadera_y = estado_eval.get(
        "base_cadera_y"
    )

    if base_cadera_y is None:

        estado_eval[
            "base_cadera_y"
        ] = cadera_y

        base_cadera_y = cadera_y

    diferencia_altura = (
        base_cadera_y
        -
        cadera_y
    )

    # Un desplazamiento moderado es suficiente.
    # Antes era 0.08.
    pelvis_arriba = (
        diferencia_altura > 0.045
    )

    # Regreso cercano a la referencia inicial.
    pelvis_abajo = (
        diferencia_altura < 0.020
    )

    # ------------------------------------------
    # ELEVACIÓN DE PELVIS
    # ------------------------------------------

    if (
        pelvis_arriba
        and
        estado_eval["fase"] in [
            "inicio",
            "abajo"
        ]
    ):

        estable = confirmar_fase_estable(
            estado_eval,
            "arriba",
            duracion_minima=0.15
        )

        if estable:

            estado_eval["fase"] = "arriba"

            mensaje = (
                "Muy bien, baja la pelvis lentamente"
            )

        else:

            mensaje = (
                "Mantén la pelvis elevada un momento"
            )

    # ------------------------------------------
    # REGRESO
    # ------------------------------------------

    elif (
        pelvis_abajo
        and
        estado_eval["fase"] == "arriba"
    ):

        estable = confirmar_fase_estable(
            estado_eval,
            "abajo",
            duracion_minima=0.15
        )

        if estable:

            rep_valida = True

            estado_eval["fase"] = "abajo"

            mensaje = (
                "Repetición válida"
            )

        else:

            mensaje = (
                "Regresa lentamente a la posición inicial"
            )

    else:

        estado_eval[
            "fase_candidata"
        ] = None

        estado_eval[
            "fase_candidata_desde"
        ] = None

        mensaje = (
            "Eleva la pelvis con control"
        )

    return (
        rep_valida,
        estado_eval,
        mensaje
    )


def evaluar_abduccion_cadera(
    angulo,
    puntos,
    estado_eval
):

    rep_valida = False

    estado_eval[
        "intento_no_completado_evento"
    ] = False

    # ==============================================
    # ABDUCCIÓN: DESPLAZAMIENTO RELATIVO A LA CADERA
    # ==============================================

    cadera_x, cadera_y = puntos["cadera_norm"]
    tobillo_x, tobillo_y = puntos["tobillo_norm"]

    separacion_relativa = tobillo_x - cadera_x

    # Registrar la posición inicial de la pierna y la cadera.
    # El participante debe comenzar con la pierna al centro.
    if "_abduccion_base_relativa" not in estado_eval:
        estado_eval["_abduccion_base_relativa"] = separacion_relativa
        estado_eval["_abduccion_base_cadera_x"] = cadera_x

    # Movimiento del tobillo respecto de su propia cadera
    desplazamiento_abs = abs(
        separacion_relativa
        - estado_eval["_abduccion_base_relativa"]
    )

    # Detectar desplazamientos excesivos de la cadera
    desplazamiento_cadera = abs(
        cadera_x - estado_eval["_abduccion_base_cadera_x"]
    )

    # Ajustar sensibilidad según el tamaño visible de la pierna
    escala = max(0.25, abs(tobillo_y - cadera_y))

    umbral_abierta = max(0.055, 0.15 * escala)
    umbral_centro = max(0.025, 0.06 * escala)
    tolerancia_cadera = max(0.07, 0.16 * escala)

    # Verificar que la cadera permanezca relativamente estable
    cadera_estable = desplazamiento_cadera < tolerancia_cadera

    pierna_abierta = (
        desplazamiento_abs > umbral_abierta
        and cadera_estable
    )

    pierna_centro = (
        desplazamiento_abs < umbral_centro
        and cadera_estable
    )

    movimiento_parcial = (
        desplazamiento_abs > umbral_abierta * 0.5
        and cadera_estable
    )

    # Evitar confirmar movimientos intermitentes como continuos
    condiciones = {
        "inicio": pierna_centro,
        "centro": pierna_abierta,
        "abierta": pierna_centro,
    }

    if not condiciones.get(estado_eval["fase"], True):
        estado_eval["fase_candidata"] = None
        estado_eval["fase_candidata_desde"] = None


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
            "No se detecta correctamente la rodilla"
        )

    # ==============================================
    # LEVANTARSE Y SENTARSE: CONTROL DE CADERA
    # ==============================================

    cadera_y = puntos["cadera_norm"][1]
    tobillo_y = puntos["tobillo_norm"][1]

    # Referencia tomada al confirmar la posición sentada
    base_cadera = estado_eval.get("_sts_cadera_sentado")
    escala = estado_eval.get("_sts_escala_pierna", 0.25)

    # Umbrales iniciales según el tamaño visible de la pierna
    umbral_subida = max(0.055, 0.18 * escala)
    umbral_retorno = max(0.035, 0.10 * escala)

    # La cadera debe subir para reconocer que se levantó
    cadera_subio = (
        base_cadera is not None
        and base_cadera - cadera_y > umbral_subida
    )

    # Debe regresar cerca de la altura inicial
    cadera_volvio = (
        base_cadera is not None
        and abs(base_cadera - cadera_y) < umbral_retorno
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

                # Guardar la altura de la cadera sentado
                estado_eval["_sts_cadera_sentado"] = cadera_y

                # Escala corporal para ajustar sensibilidad
                estado_eval["_sts_escala_pierna"] = max(
                    0.25, abs(tobillo_y - cadera_y)
                )

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
        # Evitar confirmar una postura si dejó de cumplirse
        if not (de_pie and cadera_subio):
            estado_eval["fase_candidata"] = None
            estado_eval["fase_candidata_desde"] = None

        if de_pie and cadera_subio:

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

        # Exigir continuidad en el regreso al asiento
        if not (sentado and cadera_volvio):
            estado_eval["fase_candidata"] = None
            estado_eval["fase_candidata_desde"] = None

        if sentado and cadera_volvio:

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

def evaluar_marcha_sitio(angulo, puntos, estado_eval):
    """
    Marcha alternada: confirma subida y bajada
    de cada rodilla antes de sumar una repetición.
    """

    estado_eval["intento_no_completado_evento"] = False

    lado = puntos.get("lado")
    contraria = puntos.get("contraria")

    if lado not in ("LEFT", "RIGHT") or contraria is None:
        return False, estado_eval, "Mantén ambas piernas visibles"

    lado_opuesto = "LEFT" if lado == "RIGHT" else "RIGHT"

    piernas = {
        lado: puntos,
        lado_opuesto: contraria
    }

    ahora = time.monotonic()

    # Una interrupción prolongada cancela la
    # repetición incompleta, pero conserva
    # qué pierna hizo la última repetición válida.
    ultimo = estado_eval.get("_marcha_ultimo_frame")

    if ultimo is not None and ahora - ultimo > 0.7:
        estado_eval["fase"] = "inicio"
        estado_eval.pop("_marcha_base", None)
        estado_eval.pop("_marcha_pierna_activa", None)
        estado_eval["fase_candidata"] = None
        estado_eval["fase_candidata_desde"] = None

    estado_eval["_marcha_ultimo_frame"] = ahora

    # Medir la rodilla respecto de su propia cadera.
    # Así reducimos el efecto de subir o bajar
    # ligeramente todo el cuerpo.
    distancia = {
        l: p["rodilla_norm"][1] - p["cadera_norm"][1]
        for l, p in piernas.items()
    }

    # Confirmación temporal de cada fase.
    def confirmar(nombre, condicion, segundos):

        if not condicion:
            if estado_eval.get("fase_candidata") == nombre:
                estado_eval["fase_candidata"] = None
                estado_eval["fase_candidata_desde"] = None
            return False

        if estado_eval.get("fase_candidata") != nombre:
            estado_eval["fase_candidata"] = nombre
            estado_eval["fase_candidata_desde"] = ahora
            return False

        if (
            ahora - estado_eval["fase_candidata_desde"]
            >= segundos
        ):
            estado_eval["fase_candidata"] = None
            estado_eval["fase_candidata_desde"] = None
            return True

        return False

    # ==========================================
    # FASE 1: POSICIÓN INICIAL
    # ==========================================

    if estado_eval["fase"] == "inicio":

        preparado = all(
            0.10 < distancia[l] < 0.38
            for l in piernas
        )

        if confirmar("marcha_inicio", preparado, 0.30):
            estado_eval["_marcha_base"] = distancia.copy()
            estado_eval["fase"] = "abajo"

        return (
            False,
            estado_eval,
            "Comienza de pie con ambos pies en el suelo"
        )

    base = estado_eval.get("_marcha_base")

    if base is None:
        estado_eval["fase"] = "inicio"
        return False, estado_eval, "Colócate en posición inicial"

    # Sensibilidad proporcional al tamaño aparente
    # del muslo dentro de la imagen.
    escala = max(
        0.12,
        (base["LEFT"] + base["RIGHT"]) / 2
    )

    umbral_subida = max(0.045, escala * 0.30)
    umbral_bajada = max(0.022, escala * 0.12)

    elevacion = {
        l: base[l] - distancia[l]
        for l in piernas
    }

    ambos_abajo = all(
        elevacion[l] < umbral_bajada
        for l in piernas
    )

    # ==========================================
    # FASE 2: ELEVAR UNA RODILLA
    # ==========================================

    if estado_eval["fase"] == "abajo":

        ultimo_lado = estado_eval.get(
            "_marcha_ultima_pierna"
        )

        candidato = None

        for l in ("LEFT", "RIGHT"):

            otro = "RIGHT" if l == "LEFT" else "LEFT"

            if (
                elevacion[l] > umbral_subida
                and elevacion[otro] < umbral_subida * 0.45
            ):
                candidato = l
                break

        if candidato is None:

            estado_eval["fase_candidata"] = None
            estado_eval["fase_candidata_desde"] = None

            return (
                False,
                estado_eval,
                "Eleva una rodilla a la vez"
            )

        # No contar dos repeticiones seguidas
        # con la misma pierna.
        if candidato == ultimo_lado:

            estado_eval["fase_candidata"] = None
            estado_eval["fase_candidata_desde"] = None

            return (
                False,
                estado_eval,
                "Ahora eleva la otra pierna"
            )

        if confirmar(
            "marcha_arriba_" + candidato,
            True,
            0.18
        ):

            estado_eval["_marcha_pierna_activa"] = candidato
            estado_eval["fase"] = "arriba"

        return (
            False,
            estado_eval,
            "Mantén la rodilla elevada un momento"
        )

    # ==========================================
    # FASE 3: REGRESAR LA RODILLA AL SUELO
    # ==========================================

    if estado_eval["fase"] == "arriba":

        activa = estado_eval.get(
            "_marcha_pierna_activa"
        )

        if activa is None:
            estado_eval["fase"] = "abajo"
            return False, estado_eval, "Eleva una rodilla"

        if confirmar(
            "marcha_abajo",
            ambos_abajo,
            0.18
        ):

            estado_eval["fase"] = "abajo"

            # Recordar qué pierna completó la repetición
            estado_eval["_marcha_ultima_pierna"] = activa

            estado_eval.pop(
                "_marcha_pierna_activa",
                None
            )

            return (
                True,
                estado_eval,
                "Repetición válida: alterna de pierna"
            )

        return (
            False,
            estado_eval,
            "Baja la rodilla con control"
        )

    estado_eval["fase"] = "inicio"

    return (
        False,
        estado_eval,
        "Colócate frente a la cámara"
    )

def evaluar_movimiento(ejercicio, angulo, puntos, estado_eval):
    tipo = ejercicio.get("tipo_evaluacion", "extension_rodilla")

    if tipo == "extension_rodilla":
        return evaluar_extension_rodilla(angulo, estado_eval)

    if tipo == "elevacion_pierna_recta":
        return evaluar_elevacion_pierna_recta(angulo, puntos, estado_eval)

    if tipo == "mini_sentadilla":
        return evaluar_sentadilla(
            angulo,
            estado_eval
        )

    if tipo == "puente_gluteo":
        return evaluar_puente_gluteo(angulo, puntos, estado_eval)

    if tipo == "step_basico":
        return evaluar_step_basico(angulo, puntos, estado_eval)

    if tipo == "abduccion_cadera":
        return evaluar_abduccion_cadera(angulo, puntos, estado_eval)

    if tipo == "sit_to_stand":
        return evaluar_sit_to_stand(angulo, puntos, estado_eval)

    if tipo == "marcha_sitio":
        return evaluar_marcha_sitio(angulo, puntos, estado_eval)

    return evaluar_extension_rodilla(angulo, estado_eval)