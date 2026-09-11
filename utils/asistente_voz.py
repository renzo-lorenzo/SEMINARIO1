import time
import json
import streamlit as st
import streamlit.components.v1 as components


VOZ_DEFINITIVA = "Microsoft Camila Online"
VELOCIDAD_VOZ = 0.85
TONO_VOZ = 1.0


def inicializar_asistente_voz():
    if "voz_activada" not in st.session_state:
        st.session_state.voz_activada = True

    if "ultima_clave_voz" not in st.session_state:
        st.session_state.ultima_clave_voz = ""

    if "ultimo_tiempo_voz" not in st.session_state:
        st.session_state.ultimo_tiempo_voz = 0

    if "voz_bienvenida_pendiente" not in st.session_state:
        st.session_state.voz_bienvenida_pendiente = False

    if "voz_fin_ejercicio_pendiente" not in st.session_state:
        st.session_state.voz_fin_ejercicio_pendiente = False


def detener_voz():
    components.html(
        """
        <script>
            if ("speechSynthesis" in window) {
                window.speechSynthesis.cancel();
            }
        </script>
        """,
        height=0
    )


def mostrar_control_voz_global():
    inicializar_asistente_voz()

    col_izquierda, col_derecha = st.columns(
        [0.84, 0.16]
    )

    with col_derecha:
        voz_activa = st.toggle(
            "🔊 Voz",
            key="voz_activada",
            help="Activa o desactiva las instrucciones por voz."
        )

    if not voz_activa:
        detener_voz()


def hablar(texto, clave=None, cooldown=5):
    inicializar_asistente_voz()

    if not st.session_state.get("voz_activada", True):
        return

    if not texto:
        return

    ahora = time.time()

    if clave is None:
        clave = texto

    misma_clave = (
        st.session_state.ultima_clave_voz == clave
    )

    tiempo_insuficiente = (
        ahora - st.session_state.ultimo_tiempo_voz < cooldown
    )

    if misma_clave and tiempo_insuficiente:
        return

    st.session_state.ultima_clave_voz = clave
    st.session_state.ultimo_tiempo_voz = ahora

    texto_js = json.dumps(texto)
    voz_preferida_js = json.dumps(VOZ_DEFINITIVA)
    velocidad_js = json.dumps(VELOCIDAD_VOZ)
    tono_js = json.dumps(TONO_VOZ)

    components.html(
        f"""
        <script>
            const texto = {texto_js};
            const vozPreferida = {voz_preferida_js};
            const velocidad = {velocidad_js};
            const tono = {tono_js};

            function seleccionarVoz(voces) {{
                if (vozPreferida && vozPreferida !== "Automática") {{
                    const nombreBuscado = vozPreferida.toLowerCase();

                    const vozExacta = voces.find(
                        voz => voz.name.toLowerCase().includes(nombreBuscado)
                    );

                    if (vozExacta) {{
                        return vozExacta;
                    }}
                }}

                const vozPeru = voces.find(
                    voz => voz.lang && voz.lang.toLowerCase() === "es-pe"
                );

                if (vozPeru) {{
                    return vozPeru;
                }}

                const vozLatam = voces.find(
                    voz => voz.lang && (
                        voz.lang.toLowerCase() === "es-419" ||
                        voz.lang.toLowerCase() === "es-mx" ||
                        voz.lang.toLowerCase() === "es-us"
                    )
                );

                if (vozLatam) {{
                    return vozLatam;
                }}

                const vozEspanol = voces.find(
                    voz => voz.lang && voz.lang.toLowerCase().startsWith("es")
                );

                return vozEspanol || null;
            }}

            function reproducir() {{
                if (!("speechSynthesis" in window)) {{
                    return;
                }}

                window.speechSynthesis.cancel();

                const mensaje = new SpeechSynthesisUtterance(texto);

                mensaje.lang = "es-PE";
                mensaje.rate = velocidad;
                mensaje.pitch = tono;
                mensaje.volume = 1.0;

                const voces = window.speechSynthesis.getVoices();
                const vozSeleccionada = seleccionarVoz(voces);

                if (vozSeleccionada) {{
                    mensaje.voice = vozSeleccionada;
                    mensaje.lang = vozSeleccionada.lang;
                }}

                window.speechSynthesis.speak(mensaje);
            }}

            if (window.speechSynthesis.getVoices().length === 0) {{
                window.speechSynthesis.onvoiceschanged = reproducir;
            }} else {{
                reproducir();
            }}
        </script>
        """,
        height=0
    )


def hablar_bienvenida_si_corresponde():
    inicializar_asistente_voz()

    if not st.session_state.get("voz_bienvenida_pendiente", False):
        return

    nombre = st.session_state.get("participant_name", "")

    if nombre:
        texto = (
            f"Hola, {nombre}. Tu sesión ha iniciado. "
            "Cuando estés listo, elige un ejercicio del mapa."
        )
    else:
        texto = (
            "Hola. Tu sesión ha iniciado. "
            "Cuando estés listo, elige un ejercicio del mapa."
        )

    hablar(
        texto,
        clave=f"bienvenida_{st.session_state.get('participant_id')}_{time.time()}",
        cooldown=0
    )

    st.session_state.voz_bienvenida_pendiente = False


def obtener_indicacion_posicion(ejercicio):

    indicacion_personalizada = ejercicio.get(
        "indicacion_voz_tutorial",
        ""
    )

    if indicacion_personalizada:
        return indicacion_personalizada

    tipo = ejercicio.get("tipo_evaluacion", "")

    indicaciones = {
        "extension_rodilla": (
            "Antes de comenzar, ubícate frente a la cámara y mantén el cuerpo visible."
        ),
        "elevacion_pierna_recta": (
            "Antes de comenzar, ubícate de forma segura y mantén la pierna visible."
        ),
        "mini_sentadilla": (
            "Antes de comenzar, ponte de pie frente a la cámara y realiza una flexión suave."
        ),
        "puente_gluteo": (
            "Antes de comenzar, acuéstate con cuidado y mantén la cadera visible para la cámara."
        ),
        "step_basico": (
            "Antes de comenzar, colócate frente al step y mantén el equilibrio."
        ),
        "abduccion_cadera": (
            "Antes de comenzar, ponte de pie con apoyo cercano y mantén el cuerpo visible."
        ),
        "sit_to_stand": (
            "Antes de comenzar, siéntate en una silla firme frente a la cámara."
        ),
        "marcha_sitio": (
            "Antes de comenzar, ponte de pie frente a la cámara y mantén el cuerpo visible."
        ),
    }

    return indicaciones.get(
        tipo,
        "Antes de comenzar, ubícate frente a la cámara y mantén el cuerpo visible."
    )


def hablar_indicacion_tutorial(ejercicio):
    texto = obtener_indicacion_posicion(ejercicio)

    hablar(
        texto,
        clave=f"tutorial_posicion_{ejercicio.get('id')}",
        cooldown=20
    )


def hablar_repeticion(repeticiones, total_repeticiones, ejercicio_id):
    """
    Emite una frase breve por cada repetición correcta.
    Siempre indica el avance: Repetición X de Y.
    """

    if repeticiones <= 0:
        return

    frases = [
        "Muy bien.",
        "Sigue así.",
        "Movimiento correcto.",
        "Buen ritmo.",
        "Excelente control.",
        "Continúa despacio.",
        "Vas muy bien.",
        "Mantén la postura.",
        "Buen trabajo.",
        "Sigue con calma."
    ]

    frase_extra = frases[
        (repeticiones - 1) % len(frases)
    ]

    if repeticiones >= total_repeticiones:
        texto = (
            f"Repetición {repeticiones} de {total_repeticiones}. "
            "Rutina completada."
        )
    else:
        texto = (
            f"Repetición {repeticiones} de {total_repeticiones}. "
            f"{frase_extra}"
        )

    hablar(
        texto,
        clave=f"rep_{ejercicio_id}_{repeticiones}",
        cooldown=0
    )


def hablar_fin_ejercicio_si_corresponde():
    inicializar_asistente_voz()

    if not st.session_state.get("voz_fin_ejercicio_pendiente", False):
        return

    puntos = st.session_state.get(
        "puntos_ganados_ultimo",
        0
    )

    texto = (
        f"Rutina completada. Ganaste {puntos} puntos. "
        "Puedes descansar unos segundos antes de continuar."
    )

    hablar(
        texto,
        clave=f"fin_ejercicio_{time.time()}",
        cooldown=0
    )

    st.session_state.voz_fin_ejercicio_pendiente = False