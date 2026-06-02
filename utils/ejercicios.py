def obtener_ejercicios():
    return [
        {
            "id": 1,
            "nombre": "Flexión controlada de rodilla",
            "nivel_dificultad": 1,
            "puntos_requeridos": 0,
            "descripcion": "Ejercicio suave para iniciar movilidad.",
            "objetivo": "Mejorar movilidad inicial",
        },
        {
            "id": 2,
            "nombre": "Extensión suave de pierna",
            "nivel_dificultad": 1,
            "puntos_requeridos": 40,
            "descripcion": "Activación ligera del cuádriceps.",
            "objetivo": "Activar musculatura de soporte",
        },
        {
            "id": 3,
            "nombre": "Sentadilla asistida",
            "nivel_dificultad": 1,
            "puntos_requeridos": 80,
            "descripcion": "Flexión de rodilla con apoyo para mayor seguridad.",
            "objetivo": "Practicar flexión controlada",
        },
        {
            "id": 4,
            "nombre": "Sentadilla parcial",
            "nivel_dificultad": 2,
            "puntos_requeridos": 140,
            "descripcion": "Ejercicio de control postural con mayor rango de flexión.",
            "objetivo": "Mejorar control y estabilidad",
        },
        {
            "id": 5,
            "nombre": "Zancada asistida",
            "nivel_dificultad": 2,
            "puntos_requeridos": 200,
            "descripcion": "Movimiento funcional con apoyo para trabajar estabilidad.",
            "objetivo": "Fortalecer coordinación de pierna",
        },
        {
            "id": 6,
            "nombre": "Equilibrio con apoyo",
            "nivel_dificultad": 2,
            "puntos_requeridos": 260,
            "descripcion": "Ejercicio para mejorar estabilidad y control corporal.",
            "objetivo": "Reforzar estabilidad articular",
        },
        {
            "id": 7,
            "nombre": "Step-up bajo",
            "nivel_dificultad": 3,
            "puntos_requeridos": 340,
            "descripcion": "Subida controlada a una superficie baja.",
            "objetivo": "Trabajar fuerza funcional",
        },
        {
            "id": 8,
            "nombre": "Desplazamiento lateral suave",
            "nivel_dificultad": 3,
            "puntos_requeridos": 420,
            "descripcion": "Movimiento lateral controlado para fuerza y estabilidad.",
            "objetivo": "Mejorar movilidad funcional",
        },
        {
            "id": 9,
            "nombre": "Sentadilla controlada",
            "nivel_dificultad": 3,
            "puntos_requeridos": 500,
            "descripcion": "Ejercicio funcional de mayor dificultad.",
            "objetivo": "Fortalecer patrón de movimiento",
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