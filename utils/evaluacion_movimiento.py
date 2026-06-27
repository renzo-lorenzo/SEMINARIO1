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
        "base_cadera_y": None,
        "base_rodilla_y": None,
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


def evaluar_step_basico(angulo, puntos, estado_eval):
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


def evaluar_puente_gluteo(angulo, puntos, estado_eval):
    """
    Ejercicio: Puente glúteo.
    Movimiento esperado:
    pelvis baja -> pelvis sube -> pelvis vuelve a bajar.
    Se usa la altura de la cadera como referencia.
    """
    rep_valida = False

    cadera_y = puntos["cadera_norm"][1]

    if estado_eval.get("base_cadera_y") is None:
        estado_eval["base_cadera_y"] = cadera_y

    diferencia_altura = estado_eval["base_cadera_y"] - cadera_y

    pelvis_arriba = diferencia_altura > 0.08
    pelvis_abajo = diferencia_altura < 0.03

    if pelvis_arriba and estado_eval["fase"] in ["inicio", "abajo"]:
        estado_eval["fase"] = "arriba"
        mensaje = "Puente detectado, baja lentamente"
    elif pelvis_abajo and estado_eval["fase"] == "arriba":
        rep_valida = True
        estado_eval["fase"] = "abajo"
        mensaje = "Repetición válida: puente completo"
    else:
        mensaje = "Eleva la pelvis y vuelve con control"

    return rep_valida, estado_eval, mensaje


def evaluar_abduccion_cadera(angulo, puntos, estado_eval):
    """
    Ejercicio: Abducción de cadera de pie.
    Movimiento esperado:
    pierna al centro -> pierna se separa lateralmente -> vuelve al centro.
    Se usa el desplazamiento horizontal del tobillo.
    """
    rep_valida = False

    tobillo_x = puntos["tobillo_norm"][0]

    if estado_eval["base_tobillo_x"] is None:
        estado_eval["base_tobillo_x"] = tobillo_x

    desplazamiento = tobillo_x - estado_eval["base_tobillo_x"]

    pierna_abierta = abs(desplazamiento) > 0.08
    pierna_centro = abs(desplazamiento) < 0.03

    if pierna_abierta and estado_eval["fase"] in ["inicio", "centro"]:
        estado_eval["fase"] = "abierta"
        mensaje = "Pierna separada, vuelve lentamente al centro"
    elif pierna_centro and estado_eval["fase"] == "abierta":
        rep_valida = True
        estado_eval["fase"] = "centro"
        mensaje = "Repetición válida: abducción completa"
    else:
        mensaje = "Separa la pierna lateralmente y vuelve al centro"

    return rep_valida, estado_eval, mensaje


def evaluar_sit_to_stand(angulo, estado_eval):
    """
    Ejercicio: Sit to Stand.
    Movimiento esperado:
    sentado/flexionado -> de pie/extendido -> vuelve a sentado.
    Se valida con el ángulo de rodilla.
    """
    rep_valida = False

    if angulo is None:
        return rep_valida, estado_eval, "No se detecta correctamente la rodilla"

    sentado = angulo < 120
    de_pie = angulo > 155

    if de_pie and estado_eval["fase"] in ["inicio", "sentado"]:
        estado_eval["fase"] = "de_pie"
        mensaje = "De pie detectado, vuelve a sentarte con control"
    elif sentado and estado_eval["fase"] == "de_pie":
        rep_valida = True
        estado_eval["fase"] = "sentado"
        mensaje = "Repetición válida: sentado y de pie completo"
    else:
        mensaje = "Levántate y siéntate de forma controlada"

    return rep_valida, estado_eval, mensaje


def evaluar_marcha_sitio(angulo, puntos, estado_eval):
    """
    Ejercicio: Elevación alternada de rodillas / Marcha en el sitio.
    Movimiento esperado:
    rodilla baja -> rodilla sube -> rodilla baja.
    Se usa la altura de la rodilla.
    """
    rep_valida = False

    rodilla_y = puntos["rodilla_norm"][1]

    if estado_eval.get("base_rodilla_y") is None:
        estado_eval["base_rodilla_y"] = rodilla_y

    diferencia_altura = estado_eval["base_rodilla_y"] - rodilla_y

    rodilla_arriba = diferencia_altura > 0.08
    rodilla_abajo = diferencia_altura < 0.03

    if rodilla_arriba and estado_eval["fase"] in ["inicio", "abajo"]:
        estado_eval["fase"] = "arriba"
        mensaje = "Rodilla elevada, baja con control"
    elif rodilla_abajo and estado_eval["fase"] == "arriba":
        rep_valida = True
        estado_eval["fase"] = "abajo"
        mensaje = "Repetición válida: marcha en el sitio"
    else:
        mensaje = "Eleva una rodilla y vuelve a la posición inicial"

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