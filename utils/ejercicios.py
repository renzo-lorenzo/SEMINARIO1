def obtener_ejercicios():
    return [
        {
            "id": 1,
            "nombre": "Extensión de rodilla sentado",
            "nivel_dificultad": 1,
            "puntos_requeridos": 0,
            "repeticiones_objetivo": 10,
            "descripcion": "Sentado en una silla, estira lentamente la pierna hacia adelante hasta que la rodilla quede casi recta y vuelve a la posición inicial.",
            "objetivo": "Mejorar movilidad y extensión de rodilla",
            "tipo_evaluacion": "extension_rodilla",
            "video": "imagenes/tutorial_extension_rodilla.mp4",
        },
        {
            "id": 2,
            "nombre": "Elevación de pierna recta",
            "nivel_dificultad": 1,
            "puntos_requeridos": 40,
            "repeticiones_objetivo": 10,
            "descripcion": "Eleva la pierna manteniendo la rodilla extendida y vuelve lentamente a la posición inicial.",
            "objetivo": "Fortalecer cuádriceps y control de pierna",
            "tipo_evaluacion": "elevacion_pierna_recta",
            "video": "imagenes/tutorial_elevacion_pierna.mp4",
        },
        {
            "id": 3,
            "nombre": "Mini sentadillas",
            "nivel_dificultad": 1,
            "puntos_requeridos": 80,
            "repeticiones_objetivo": 10,
            "descripcion": "Realiza una flexión parcial de rodilla y vuelve a la posición inicial de forma controlada.",
            "objetivo": "Trabajar flexión controlada y estabilidad inicial",
            "tipo_evaluacion": "mini_sentadilla",
            "video": "imagenes/tutorial_mini_sentadilla.mp4",
        },
        {
            "id": 4,
            "nombre": "Puente glúteo",
            "nivel_dificultad": 2,
            "puntos_requeridos": 140,
            "repeticiones_objetivo": 10,
            "descripcion": "Acostado boca arriba, eleva la pelvis de forma controlada y vuelve lentamente a la posición inicial.",
            "objetivo": "Fortalecer glúteos y musculatura de soporte",
            "tipo_evaluacion": "puente_gluteo",
            "video": "imagenes/tutorial_puente_gluteo.mp4",
        },
        {
            "id": 5,
            "nombre": "Step básico",
            "nivel_dificultad": 2,
            "puntos_requeridos": 200,
            "repeticiones_objetivo": 10,
            "descripcion": "Sube a una superficie baja de forma controlada y vuelve a bajar manteniendo estabilidad.",
            "objetivo": "Mejorar fuerza funcional y control de rodilla",
            "tipo_evaluacion": "step_basico",
            "video": "imagenes/tutorial_step_basico.mp4",
        },
        {
            "id": 6,
            "nombre": "Abducción de cadera de pie",
            "nivel_dificultad": 2,
            "puntos_requeridos": 260,
            "repeticiones_objetivo": 10,
            "descripcion": "De pie y con apoyo, separa lateralmente la pierna y vuelve lentamente a la posición inicial.",
            "objetivo": "Mejorar estabilidad lateral y control de cadera",
            "tipo_evaluacion": "abduccion_cadera",
            "video": "imagenes/tutorial_abduccion_cadera.mp4",
        },
        {
            "id": 7,
            "nombre": "Sit to Stand",
            "nivel_dificultad": 3,
            "puntos_requeridos": 340,
            "repeticiones_objetivo": 10,
            "descripcion": "Desde una silla, levántate hasta quedar de pie y vuelve a sentarte de forma controlada.",
            "objetivo": "Fortalecer patrón funcional de levantarse y sentarse",
            "tipo_evaluacion": "sit_to_stand",
            "video": "imagenes/tutorial_sit_to_stand.mp4",
        },
        {
            "id": 8,
            "nombre": "Elevación alternada de rodillas",
            "nivel_dificultad": 3,
            "puntos_requeridos": 420,
            "repeticiones_objetivo": 10,
            "descripcion": "Realiza una marcha en el sitio elevando una rodilla a la vez de forma alternada y controlada.",
            "objetivo": "Mejorar coordinación, movilidad y control funcional",
            "tipo_evaluacion": "marcha_sitio",
            "video": "imagenes/tutorial_marcha_sitio.mp4",
        },
    ]


def puntos_iniciales_por_experiencia(experiencia):
    if experiencia == "Principiante":
        return 0
    elif experiencia == "Intermedio":
        return 120
    elif experiencia == "Avanzado":
        return 280
    return 0


def obtener_nombre_nivel(nivel):
    nombres = {
        1: "Nivel 1: Movilidad inicial",
        2: "Nivel 2: Control y estabilidad",
        3: "Nivel 3: Fuerza funcional",
    }
    return nombres.get(nivel, "Nivel desconocido")


def ejercicio_desbloqueado(ejercicio, puntos_usuario):
    return puntos_usuario >= ejercicio["puntos_requeridos"]