def obtener_ejercicios():
    return [
        # NIVEL 1
        {
            "id": 1,
            "nombre": "Extensión de rodilla sentado",
            "nivel_dificultad": 1,
            "puntos_requeridos": 0,
            "descripcion": "Sentado en una silla, estira lentamente la pierna hacia adelante hasta que la rodilla quede casi recta y vuelve a la posición inicial.",
            "objetivo": "Mejorar movilidad y extensión de rodilla",
            "tipo_evaluacion": "extension_rodilla",
        },
        {
            "id": 2,
            "nombre": "Elevación de pierna recta",
            "nivel_dificultad": 1,
            "puntos_requeridos": 40,
            "descripcion": "Eleva la pierna manteniendo la rodilla extendida y vuelve lentamente a la posición inicial.",
            "objetivo": "Fortalecer cuádriceps y control de pierna",
            "tipo_evaluacion": "elevacion_pierna_recta",
        },
        {
            "id": 3,
            "nombre": "Mini sentadillas",
            "nivel_dificultad": 1,
            "puntos_requeridos": 80,
            "descripcion": "Realiza una flexión parcial de rodilla y vuelve a la posición inicial de forma controlada.",
            "objetivo": "Trabajar flexión controlada y estabilidad inicial",
            "tipo_evaluacion": "mini_sentadilla",
        },

        # NIVEL 2
        {
            "id": 4,
            "nombre": "Puente glúteo",
            "nivel_dificultad": 2,
            "puntos_requeridos": 140,
            "descripcion": "Acostado boca arriba, eleva la pelvis de forma controlada y vuelve lentamente a la posición inicial.",
            "objetivo": "Fortalecer glúteos y musculatura de soporte",
            "tipo_evaluacion": "puente_gluteo",
        },
        {
            "id": 5,
            "nombre": "Step básico",
            "nivel_dificultad": 2,
            "puntos_requeridos": 200,
            "descripcion": "Sube a una superficie baja de forma controlada y vuelve a bajar manteniendo estabilidad.",
            "objetivo": "Mejorar fuerza funcional y control de rodilla",
            "tipo_evaluacion": "step_basico",
        },
        {
            "id": 6,
            "nombre": "Abducción de cadera de pie",
            "nivel_dificultad": 2,
            "puntos_requeridos": 260,
            "descripcion": "De pie y con apoyo, separa lateralmente la pierna y vuelve lentamente a la posición inicial.",
            "objetivo": "Mejorar estabilidad lateral y control de cadera",
            "tipo_evaluacion": "abduccion_cadera",
        },

        # NIVEL 3
        {
            "id": 7,
            "nombre": "Sit to Stand",
            "nivel_dificultad": 3,
            "puntos_requeridos": 340,
            "descripcion": "Desde una silla, levántate hasta quedar de pie y vuelve a sentarte de forma controlada.",
            "objetivo": "Fortalecer patrón funcional de levantarse y sentarse",
            "tipo_evaluacion": "sit_to_stand",
        },
        {
            "id": 8,
            "nombre": "Elevación alternada de rodillas",
            "nivel_dificultad": 3,
            "puntos_requeridos": 420,
            "descripcion": "Realiza una marcha en el sitio elevando una rodilla a la vez de forma alternada y controlada.",
            "objetivo": "Mejorar coordinación, movilidad y control funcional",
            "tipo_evaluacion": "marcha_sitio",
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
        3: "Nivel 3: Fuerza funcional"
    }
    return nombres.get(nivel, "Nivel desconocido")


def ejercicio_desbloqueado(ejercicio, puntos_usuario):
    return puntos_usuario >= ejercicio["puntos_requeridos"]