from database.participant_repository import get_all_participants

from components.participant_card import mostrar_tarjeta_participante


def mostrar_lista_participantes(busqueda):

    participantes = get_all_participants()

    if busqueda.strip():

        participantes = [

            p for p in participantes

            if busqueda.lower()

            in f"{p['first_name']} {p['last_name']}".lower()

        ]

    if len(participantes) == 0:

        return False

    for participante in participantes:

        mostrar_tarjeta_participante(participante)

    return True