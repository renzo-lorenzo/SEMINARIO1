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
        "ultimo_tick": time.time(),
        "tiempo_estable": 0,
    }


def evaluar_extension_rodilla(angulo, estado_eval):
    """
    Ejercicio: Extensión de rodilla sentado.
    Movimiento esperado:
    rodilla flexionada -> rodilla extendida.
    """
    rep_valida = False

    if angulo is None:
        return rep_valida, estado_eval, "No se detecta correctamente la rodilla"

    if angulo < 120:
        estado_eval["fase"] = "flexionado"
        mensaje = "Buena flexión, ahora estira la pierna"
    elif angulo > 150 and estado_eval["fase"] == "flexionado":
        rep_valida = True
        estado_eval["fase"] = "extendido"
        mensaje = "Repetición válida: rodilla extendida"
    else:
        mensaje = "Realiza el movimiento de forma lenta y controlada"

    return rep_valida, estado_eval, mensaje


def evaluar_sentadilla(angulo, estado_eval, umbral_bajada=130, umbral_subida=150):
    """
    Ejercicios: mini sentadilla, sentadilla parcial, sentadilla controlada.
    Movimiento esperado:
    de pie -> baja flexionando rodilla -> vuelve a subir.
    """
    rep_valida = False

    if angulo is None:
        return rep_valida, estado_eval, "No se detecta correctamente la rodilla"

    if angulo < umbral_bajada:
        estado_eval["fase"] = "abajo"
        mensaje = "Buena bajada, ahora sube lentamente"
    elif angulo > umbral_subida and estado_eval["fase"] == "abajo":
        rep_valida = True
        estado_eval["fase"] = "arriba"
        mensaje = "Repetición válida: subiste con control"
    else:
        mensaje = "Flexiona y extiende la rodilla con control"

    return rep_valida, estado_eval, mensaje


def evaluar_elevacion_pierna_recta(angulo, puntos, estado_eval):
    """
    Ejercicio: Elevación de pierna recta.
    Movimiento esperado:
    la pierna sube manteniendo rodilla extendida.
    Se valida por altura del tobillo y rodilla extendida.
    """
    rep_valida = False

    if angulo is None:
        return rep_valida, estado_eval, "No se detecta correctamente la pierna"

    tobillo_y = puntos["tobillo_norm"][1]

    if estado_eval["base_tobillo_y"] is None:
        estado_eval["base_tobillo_y"] = tobillo_y

    diferencia_altura = estado_eval["base_tobillo_y"] - tobillo_y

    rodilla_extendida = angulo > 145
    pierna_elevada = diferencia_altura > 0.10
    pierna_abajo = diferencia_altura < 0.04

    if not rodilla_extendida:
        mensaje = "Mantén la rodilla más extendida"
    elif pierna_elevada and estado_eval["fase"] in ["inicio", "abajo"]:
        estado_eval["fase"] = "arriba"
        mensaje = "Pierna elevada, ahora baja lentamente"
    elif pierna_abajo and estado_eval["fase"] == "arriba":
        rep_valida = True
        estado_eval["fase"] = "abajo"
        mensaje = "Repetición válida: elevación completa"
    else:
        mensaje = "Eleva la pierna manteniéndola recta"

    return rep_valida, estado_eval, mensaje


def evaluar_zancada_asistida(angulo, estado_eval):
    """
    Ejercicio: Zancada asistida.
    Movimiento esperado:
    flexión controlada de rodilla y retorno a extensión.
    """
    return evaluar_sentadilla(
        angulo=angulo,
        estado_eval=estado_eval,
        umbral_bajada=125,
        umbral_subida=150
    )


def evaluar_step_up(angulo, puntos, estado_eval):
    """
    Ejercicio: Step-up bajo.
    Se combina flexión/extensión de rodilla con elevación del tobillo.
    """
    rep_valida = False

    if angulo is None:
        return rep_valida, estado_eval, "No se detecta correctamente la pierna"

    tobillo_y = puntos["tobillo_norm"][1]

    if estado_eval["base_tobillo_y"] is None:
        estado_eval["base_tobillo_y"] = tobillo_y

    diferencia_altura = estado_eval["base_tobillo_y"] - tobillo_y

    subio = diferencia_altura > 0.08 and angulo > 130
    bajo = diferencia_altura < 0.03

    if subio and estado_eval["fase"] in ["inicio", "abajo"]:
        estado_eval["fase"] = "arriba"
        mensaje = "Subida detectada, ahora baja con control"
    elif bajo and estado_eval["fase"] == "arriba":
        rep_valida = True
        estado_eval["fase"] = "abajo"
        mensaje = "Repetición válida: step completo"
    else:
        mensaje = "Sube y baja de forma controlada"

    return rep_valida, estado_eval, mensaje


def evaluar_equilibrio(angulo, puntos, estado_eval):
    """
    Ejercicio: Equilibrio con apoyo.
    No se evalúa por repeticiones clásicas.
    Se asigna una unidad de progreso por mantener estabilidad.
    """
    rep_valida = False

    if angulo is None:
        return rep_valida, estado_eval, "No se detecta correctamente la pierna"

    ahora = time.time()

    rodilla_estable = angulo > 145

    if rodilla_estable:
        if ahora - estado_eval["ultimo_tick"] >= 2:
            rep_valida = True
            estado_eval["ultimo_tick"] = ahora
            mensaje = "Postura estable mantenida"
        else:
            mensaje = "Mantén la postura estable"
    else:
        estado_eval["ultimo_tick"] = ahora
        mensaje = "Estira y estabiliza la pierna"

    return rep_valida, estado_eval, mensaje


def evaluar_desplazamiento_lateral(angulo, puntos, estado_eval):
    """
    Ejercicio: Desplazamiento lateral suave.
    Se valida por cambio horizontal del tobillo.
    """
    rep_valida = False

    tobillo_x = puntos["tobillo_norm"][0]

    if estado_eval["base_tobillo_x"] is None:
        estado_eval["base_tobillo_x"] = tobillo_x

    desplazamiento = tobillo_x - estado_eval["base_tobillo_x"]

    fue_lateral = abs(desplazamiento) > 0.08
    volvio_centro = abs(desplazamiento) < 0.03

    if fue_lateral and estado_eval["fase"] in ["inicio", "centro"]:
        estado_eval["fase"] = "lateral"
        mensaje = "Desplazamiento lateral detectado, vuelve al centro"
    elif volvio_centro and estado_eval["fase"] == "lateral":
        rep_valida = True
        estado_eval["fase"] = "centro"
        mensaje = "Repetición válida: desplazamiento completo"
    else:
        mensaje = "Realiza el desplazamiento lateral con control"

    return rep_valida, estado_eval, mensaje


def evaluar_movimiento(ejercicio, angulo, puntos, estado_eval):
    tipo = ejercicio.get("tipo_evaluacion", "extension_rodilla")

    if tipo == "extension_rodilla":
        return evaluar_extension_rodilla(angulo, estado_eval)

    if tipo == "elevacion_pierna_recta":
        return evaluar_elevacion_pierna_recta(angulo, puntos, estado_eval)

    if tipo == "mini_sentadilla":
        return evaluar_sentadilla(angulo, estado_eval, umbral_bajada=135, umbral_subida=150)

    if tipo == "sentadilla_parcial":
        return evaluar_sentadilla(angulo, estado_eval, umbral_bajada=125, umbral_subida=150)

    if tipo == "sentadilla_controlada":
        return evaluar_sentadilla(angulo, estado_eval, umbral_bajada=115, umbral_subida=150)

    if tipo == "zancada_asistida":
        return evaluar_zancada_asistida(angulo, estado_eval)

    if tipo == "equilibrio":
        return evaluar_equilibrio(angulo, puntos, estado_eval)

    if tipo == "step_up":
        return evaluar_step_up(angulo, puntos, estado_eval)

    if tipo == "desplazamiento_lateral":
        return evaluar_desplazamiento_lateral(angulo, puntos, estado_eval)

    return evaluar_extension_rodilla(angulo, estado_eval)