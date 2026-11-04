
"""Elementos visuales de Activate: aviso animado de repetición válida.

La imagen de la cámara se mantiene en OpenCV (BGR). Esta función se ejecuta
DESPUÉS de MediaPipe, por lo que no altera la evaluación del movimiento.
"""

import math
import time
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


@lru_cache(maxsize=8)
def _fuente_grande(tamano):
    rutas = (
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    )
    for ruta in rutas:
        try:
            return ImageFont.truetype(ruta, tamano)
        except OSError:
            continue
    return ImageFont.load_default()


def _suavizar(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _entrada_rebote(x):
    """Crecimiento con un pequeño rebote, no un salto brusco."""
    x = max(0.0, min(1.0, x))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def _puntos_estrella(cx, cy, radio):
    puntos = []
    for i in range(10):
        angulo = -math.pi / 2 + i * math.pi / 5
        r = radio if i % 2 == 0 else radio * 0.46
        puntos.append((
            round(cx + r * math.cos(angulo)),
            round(cy + r * math.sin(angulo)),
        ))
    return puntos


def dibujar_feedback_repeticion(frame, hasta, duracion=1.8):
    """Dibuja entrada con rebote suave, pausa y salida deslizante.

    `hasta` debe establecerse como `time.time() + duracion` SOLO al validar
    una nueva repetición; no se modifica dentro de la función.
    """
    ahora = time.time()
    transcurrido = ahora - (hasta - duracion)
    if transcurrido < 0 or transcurrido >= duracion:
        return frame

    # Entrada más dinámica: 0.26 s con crecimiento y un rebote leve.
    entrada = _entrada_rebote(transcurrido / 0.26)
    opacidad_entrada = _suavizar(transcurrido / 0.14)

    # Salida visible, pero no brusca: últimos 0.38 segundos.
    tiempo_salida = 0.38
    opacidad_salida = _suavizar((duracion - transcurrido) / tiempo_salida)
    visibilidad = max(0.0, min(opacidad_entrada, opacidad_salida))
    if visibilidad <= 0:
        return frame

    salida = _suavizar(
        (transcurrido - (duracion - tiempo_salida)) / tiempo_salida
    )

    alto, ancho = frame.shape[:2]

    # Mantener el tamaño compacto y la paleta azul aprobada.
    escala = 0.75 + 0.25 * entrada
    ancho_tarjeta = max(120, round(min(350, ancho - 28) * escala))
    alto_tarjeta = max(35, round(65 * escala))
    centro_x = ancho // 2
    centro_y = round(alto * 0.25 + 15 * (1 - entrada) - 8 * salida)

    izquierda = centro_x - ancho_tarjeta // 2
    arriba = centro_y - alto_tarjeta // 2
    derecha = izquierda + ancho_tarjeta
    abajo = arriba + alto_tarjeta
    alfa = round(250 * visibilidad)

    capa = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(capa)

    dibujo.rounded_rectangle(
        (izquierda + 3, arriba + 5, derecha + 3, abajo + 5),
        radius=17,
        fill=(20, 48, 77, round(65 * visibilidad)),
    )

    dibujo.rounded_rectangle(
        (izquierda, arriba, derecha, abajo),
        radius=17,
        fill=(255, 255, 255, alfa),
        outline=(0, 164, 218, round(255 * visibilidad)),
        width=3,
    )

    for x in (izquierda + 23, derecha - 23):
        dibujo.polygon(
            _puntos_estrella(x, centro_y, max(7, round(11 * escala))),
            fill=(0, 142, 210, round(255 * visibilidad)),
        )

    dibujo.text(
        (centro_x, centro_y),
        "¡Repetición válida!",
        font=_fuente_grande(22 if ancho >= 480 else 19),
        fill=(17, 70, 121, round(255 * visibilidad)),
        anchor="mm",
    )

    fondo = Image.fromarray(
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    ).convert("RGBA")

    resultado = Image.alpha_composite(
        fondo, capa
    ).convert("RGB")

    return cv2.cvtColor(
        np.asarray(resultado),
        cv2.COLOR_RGB2BGR
    )
