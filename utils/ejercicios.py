def obtener_ejercicios():
    return [
        {
            "id": 1,
            "nombre": "Extensión de rodilla sentado",
            "nivel_dificultad": 1,
            "puntos_requeridos": 0,
            "descripcion": "Sentado en una silla, estira lentamente la pierna hacia adelante hasta que la rodilla quede casi recta y vuelve a la posición inicial.",
            "objetivo": "Mejorar la extensión de rodilla",
            "tipo_evaluacion": "extension_rodilla",
        },
        {
            "id": 2,
            "nombre": "Elevación de pierna recta",
            "nivel_dificultad": 1,
            "puntos_requeridos": 40,
            "descripcion": "Eleva la pierna manteniendo la rodilla extendida para fortalecer el cuádriceps.",
            "objetivo": "Fortalecer musculatura de soporte",
            "tipo_evaluacion": "elevacion_pierna_recta",
        },
        {
            "id": 3,
            "nombre": "Mini sentadillas",
            "nivel_dificultad": 1,
            "puntos_requeridos": 80,
            "descripcion": "Realiza una flexión parcial de rodilla y vuelve a la posición inicial de forma controlada.",
            "objetivo": "Practicar flexión controlada",
            "tipo_evaluacion": "mini_sentadilla",
        },
        {
            "id": 4,
            "nombre": "Sentadilla parcial",
            "nivel_dificultad": 2,
            "puntos_requeridos": 140,
            "descripcion": "Ejercicio de control postural con mayor rango de flexión.",
            "objetivo": "Mejorar control y estabilidad",
            "tipo_evaluacion": "sentadilla_parcial",
        },
        {
            "id": 5,
            "nombre": "Zancada asistida",
            "nivel_dificultad": 2,
            "puntos_requeridos": 200,
            "descripcion": "Movimiento funcional con apoyo para trabajar estabilidad.",
            "objetivo": "Fortalecer coordinación de pierna",
            "tipo_evaluacion": "zancada_asistida",
        },
        {
            "id": 6,
            "nombre": "Equilibrio con apoyo",
            "nivel_dificultad": 2,
            "puntos_requeridos": 260,
            "descripcion": "Mantén la postura estable con apoyo para mejorar control corporal.",
            "objetivo": "Reforzar estabilidad articular",
            "tipo_evaluacion": "equilibrio",
        },
        {
            "id": 7,
            "nombre": "Step-up bajo",
            "nivel_dificultad": 3,
            "puntos_requeridos": 340,
            "descripcion": "Sube de forma controlada a una superficie baja y vuelve a bajar.",
            "objetivo": "Trabajar fuerza funcional",
            "tipo_evaluacion": "step_up",
        },
        {
            "id": 8,
            "nombre": "Desplazamiento lateral suave",
            "nivel_dificultad": 3,
            "puntos_requeridos": 420,
            "descripcion": "Realiza un movimiento lateral controlado para trabajar movilidad y estabilidad.",
            "objetivo": "Mejorar movilidad funcional",
            "tipo_evaluacion": "desplazamiento_lateral",
        },
        {
            "id": 9,
            "nombre": "Sentadilla controlada",
            "nivel_dificultad": 3,
            "puntos_requeridos": 500,
            "descripcion": "Ejercicio funcional de mayor dificultad basado en flexión y extensión controlada de rodilla.",
            "objetivo": "Fortalecer patrón de movimiento",
            "tipo_evaluacion": "sentadilla_controlada",
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