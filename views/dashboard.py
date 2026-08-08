from components.dashboard_header import mostrar_dashboard_header
from components.dashboard_start_button import mostrar_boton_comenzar
from components.dashboard_stats import mostrar_dashboard_stats
from components.dashboard_logout import mostrar_logout


def pantalla_dashboard():

    # ==========================================
    # ENCABEZADO
    # ==========================================

    mostrar_dashboard_header()

    # ==========================================
    # COMENZAR EJERCICIOS
    # ==========================================

    mostrar_boton_comenzar()

    # ==========================================
    # DETALLES Y PROGRESO
    # ==========================================

    mostrar_dashboard_stats()

    # ==========================================
    # CERRAR SESIÓN
    # ==========================================

    mostrar_logout()