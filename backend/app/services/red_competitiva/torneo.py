"""
Torneo de eliminación directa entre hojas de vida.

En cada duelo se comparan dos hojas de vida y la mejor pasa a la siguiente
ronda, hasta que queda un campeón. Si la cantidad de participantes no es una
potencia de 2, los primeros sembrados pasan la primera ronda sin jugar (bye).

El torneo no depende de la red: recibe una función `comparar(a, b)` que
devuelve la probabilidad de que `a` le gane a `b`.
"""

import random
from collections.abc import Callable

Comparador = Callable[[dict, dict], float]


def _nombre_ronda(n_en_juego: int, numero: int) -> str:
    return {2: "Final", 4: "Semifinal", 8: "Cuartos de final", 16: "Octavos de final"}.get(
        n_en_juego, f"Ronda {numero}"
    )


def _potencia_de_dos(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


def jugar_torneo(participantes: list[dict], comparar: Comparador, semilla: int | None = None) -> dict:
    """
    Juega un torneo completo.

    `participantes` es una lista de dicts con al menos la clave "id".
    Devuelve {"rondas": [...], "campeon": dict | None, "total_duelos": int}.
    Cada ronda: {"numero", "nombre", "duelos": [{"a", "b", "ganador", "prob_a"}], "pases": [id]}.
    """
    en_juego = list(participantes)
    if semilla is not None:
        random.Random(semilla).shuffle(en_juego)
    if not en_juego:
        return {"rondas": [], "campeon": None, "total_duelos": 0}

    rondas = []
    total_duelos = 0
    numero = 1
    # Los byes se dan en la primera ronda para que las siguientes queden parejas.
    byes = _potencia_de_dos(len(en_juego)) - len(en_juego)

    while len(en_juego) > 1:
        n_en_juego = _potencia_de_dos(len(en_juego))
        pases = en_juego[:byes]
        jugadores = en_juego[byes:]
        siguientes = list(pases)
        duelos = []
        for a, b in zip(jugadores[0::2], jugadores[1::2]):
            prob_a = float(comparar(a, b))
            # Empate exacto: avanza el mejor sembrado (a)
            ganador = a if prob_a >= 0.5 else b
            duelos.append({"a": a["id"], "b": b["id"], "ganador": ganador["id"], "prob_a": prob_a})
            siguientes.append(ganador)
        total_duelos += len(duelos)
        rondas.append({
            "numero": numero,
            "nombre": _nombre_ronda(n_en_juego, numero),
            "duelos": duelos,
            "pases": [p["id"] for p in pases],
        })
        en_juego = siguientes
        byes = 0
        numero += 1

    return {"rondas": rondas, "campeon": en_juego[0], "total_duelos": total_duelos}


def clasificar(
    participantes: list[dict], comparar: Comparador, top: int = 5, semilla: int | None = None
) -> list[dict]:
    """
    Top `top` por torneos sucesivos: el campeón de cada torneo ocupa el
    siguiente puesto y se retira; el resto vuelve a competir.
    """
    restantes = list(participantes)
    podio = []
    while restantes and len(podio) < top:
        campeon = jugar_torneo(restantes, comparar, semilla)["campeon"]
        podio.append(campeon)
        restantes = [p for p in restantes if p["id"] != campeon["id"]]
    return podio
