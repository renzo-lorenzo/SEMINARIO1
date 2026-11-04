
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

def dibujar_overlay_calibracion(
    frame,
    progreso=0,
    titulo="Calibrando tu posición...",
    subtitulo="Preparando el reconocimiento corporal...",
    porcentaje_texto=None,
    pierna_texto=None
):
    """
    Dibuja una tarjeta centrada de calibración con barra de progreso.
    `progreso` debe estar entre 0 y 100.
    """

    progreso = max(0, min(100, int(progreso)))

    if porcentaje_texto is None:
        porcentaje_texto = f"{progreso}%"

    alto, ancho = frame.shape[:2]

    # Convertir frame a PIL
    fondo = Image.fromarray(
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    ).convert("RGBA")

    capa = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(capa)

    # Fuentes
    try:
        fuente_titulo = ImageFont.truetype("arialbd.ttf", 23)
        fuente_sub = ImageFont.truetype("arial.ttf", 15)
        fuente_label = ImageFont.truetype("arial.ttf", 14)
        fuente_pierna = ImageFont.truetype("arialbd.ttf", 17)
        fuente_pct = ImageFont.truetype("arialbd.ttf", 14)
    except:
        fuente_titulo = ImageFont.load_default()
        fuente_sub = ImageFont.load_default()
        fuente_label = ImageFont.load_default()
        fuente_pierna = ImageFont.load_default()
        fuente_pct = ImageFont.load_default()

    # Tarjeta más compacta
    card_w = min(430, int(ancho * 0.58))
    card_h = 168 if pierna_texto else 145

    x1 = (ancho - card_w) // 2
    y1 = (alto - card_h) // 2
    x2 = x1 + card_w
    y2 = y1 + card_h

    # Sombra suave
    dibujo.rounded_rectangle(
        (x1 + 5, y1 + 6, x2 + 5, y2 + 6),
        radius=22,
        fill=(20, 48, 77, 40)
    )

    # Tarjeta principal ligeramente transparente
    dibujo.rounded_rectangle(
        (x1, y1, x2, y2),
        radius=22,
        fill=(255, 255, 255, 212),
        outline=(89, 201, 255, 235),
        width=3
    )

    # Ícono simple
    icono_y = y1 + 22
    icono_x = ancho // 2

    dibujo.ellipse(
        (icono_x - 10, icono_y - 10, icono_x + 10, icono_y + 10),
        fill=(76, 186, 255, 235)
    )

    dibujo.ellipse(
        (icono_x - 4, icono_y - 4, icono_x + 4, icono_y + 4),
        fill=(255, 255, 255, 255)
    )

    # Título
    dibujo.text(
        (ancho // 2, y1 + 50),
        titulo,
        font=fuente_titulo,
        fill=(43, 74, 117, 255),
        anchor="mm"
    )

    # Subtítulo
    dibujo.text(
        (ancho // 2, y1 + 76),
        subtitulo,
        font=fuente_sub,
        fill=(76, 111, 149, 255),
        anchor="mm"
    )

    # Texto de pierna si ya fue determinada
    if pierna_texto:
        dibujo.text(
            (ancho // 2, y1 + 100),
            "Pierna a utilizar:",
            font=fuente_label,
            fill=(90, 115, 145, 255),
            anchor="mm"
        )

        dibujo.text(
            (ancho // 2, y1 + 120),
            pierna_texto,
            font=fuente_pierna,
            fill=(22, 64, 114, 255),
            anchor="mm"
        )

        by1 = y1 + 136
    else:
        by1 = y1 + 103

    by2 = by1 + 14
    barra_margin = 36
    bx1 = x1 + barra_margin
    bx2 = x2 - barra_margin

    # Fondo barra
    dibujo.rounded_rectangle(
        (bx1, by1, bx2, by2),
        radius=8,
        fill=(225, 236, 247, 245)
    )

    # Progreso barra
    ancho_progreso = int((bx2 - bx1) * (progreso / 100))
    if ancho_progreso > 0:
        dibujo.rounded_rectangle(
            (bx1, by1, bx1 + ancho_progreso, by2),
            radius=8,
            fill=(76, 186, 255, 255)
        )

    # Porcentaje
    dibujo.text(
        (ancho // 2, by2 + 14),
        porcentaje_texto,
        font=fuente_pct,
        fill=(76, 111, 149, 255),
        anchor="mm"
    )

    resultado = Image.alpha_composite(
        fondo, capa
    ).convert("RGB")

    return cv2.cvtColor(
        np.array(resultado),
        cv2.COLOR_RGB2BGR
    )