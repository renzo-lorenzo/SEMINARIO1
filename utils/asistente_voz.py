import time
import json
import streamlit as st
import streamlit.components.v1 as components


VOZ_DEFINITIVA = "Microsoft Camila Online"
VELOCIDAD_VOZ = 0.9
TONO_VOZ = 1.0


def inicializar_asistente_voz():
    """
    Inicializa las variables necesarias para el asistente de voz.
    """

    if "voz_activada" not in st.session_state:
        st.session_state.voz_activada = True

    if "ultima_clave_voz" not in st.session_state:
        st.session_state.ultima_clave_voz = ""

    if "ultimo_tiempo_voz" not in st.session_state:
        st.session_state.ultimo_tiempo_voz = 0


def mostrar_control_voz_global():
    """
    Muestra un control simple para activar o desactivar el asistente de voz.
    Debe llamarse desde app.py para que aparezca en todas las pantallas.
    """

    inicializar_asistente_voz()

    col_izquierda, col_derecha = st.columns(
        [0.82, 0.18]
    )

    with col_derecha:
        st.toggle(
            "🔊 Voz",
            key="voz_activada",
            help="Activa o desactiva las instrucciones por voz."
        )


def hablar(texto, clave=None, cooldown=5):
    """
    Reproduce una frase usando la voz del navegador.

    texto: frase que se leerá en voz alta.
    clave: identificador del mensaje para evitar repeticiones innecesarias.
    cooldown: segundos mínimos antes de repetir la misma indicación.
    """

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