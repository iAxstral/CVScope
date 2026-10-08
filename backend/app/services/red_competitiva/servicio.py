"""
Uso de la red competitiva entrenada desde la API.

Arquitectura (tipo red de Hamming):
  1. Entrada: vector de 1026 características de cada hoja de vida anonimizada.
  2. Capa de evaluación (feedforward, entrenada): red siamesa 1026-64-32-1 que
     le asigna a cada hoja de vida su fuerza s(x).
  3. Capa competitiva (recurrente, MAXNET): una neurona por hoja de vida; se
     inhiben entre sí hasta que solo queda una activa.
  4. Salida: la hoja de vida ganadora (one-hot) y la probabilidad de cada una.
"""

from functools import lru_cache
from pathlib import Path

from app.services.evaluador_requisitos import evaluar_cv
from app.services.red_competitiva.caracteristicas import DIM_ENTRADA, extraer
from app.services.red_competitiva.competitiva import maxnet, podio
from app.services.red_competitiva.modelo import RedCompetitiva
from app.services.red_competitiva.torneo import jugar_torneo

RUTA_MODELO = Path(__file__).resolve().parent.parent.parent / "ml_models" / "red_competitiva.npz"


class ModeloNoDisponible(RuntimeError):
    """No existe el modelo entrenado o no coincide con el extractor actual."""


@lru_cache
def cargar_modelo() -> tuple[RedCompetitiva, dict]:
    if not RUTA_MODELO.exists():
        raise ModeloNoDisponible(
            "No se encontró red_competitiva.npz; ejecute scripts/entrenar_red_competitiva.py"
        )
    red, meta = RedCompetitiva.cargar(RUTA_MODELO)
    if red.pesos[0].shape[0] != DIM_ENTRADA:
        raise ModeloNoDisponible(
            "El modelo fue entrenado con otro tamaño de entrada; vuelva a entrenarlo"
        )
    return red, meta


def preparar(cv: dict, requisitos: list[str]) -> dict:
    """Agrega a la hoja de vida su vector, su fuerza y el resumen de requisitos."""
    red, _ = cargar_modelo()
    x = extraer(cv["texto"], requisitos)
    evaluacion = evaluar_cv(cv["texto"], requisitos)
    return {
        **cv,
        "x": x,
        "fuerza": float(red.puntaje(x)[0]),
        "score_palabras_clave": evaluacion["score"],
        "anios_experiencia": evaluacion["anios_experiencia"],
        "requisitos_cumplidos": evaluacion["requisitos_cumplidos"],
        "requisitos_faltantes": evaluacion["requisitos_faltantes"],
    }


def _resumen_maxnet(resultado: dict) -> dict:
    return {
        "epsilon": resultado["epsilon"],
        "iteraciones": resultado["iteraciones"],
        "trayectoria": [[round(float(v), 6) for v in paso] for paso in resultado["trayectoria"]],
    }


def duelo(a: dict, b: dict) -> dict:
    """
    Duelo entre dos hojas de vida ya preparadas: MAXNET con 2 neuronas.
    Devuelve {"prob_a", "gana_a", "epsilon", "iteraciones", "trayectoria"}.
    """
    resultado = maxnet([a["fuerza"], b["fuerza"]])
    return {
        "prob_a": float(resultado["probabilidades"][0]),
        "gana_a": resultado["ganador"] == 0,
        **_resumen_maxnet(resultado),
    }


def explicar_duelo(a: dict, b: dict, resultado: dict) -> str:
    gana_a = resultado["gana_a"]
    prob = resultado["prob_a"] if gana_a else 1 - resultado["prob_a"]
    ganador, perdedor = (a, b) if gana_a else (b, a)
    iteraciones = resultado["iteraciones"]
    texto = (
        f"{ganador['nombre']} gana con una probabilidad de {prob:.1%}: en la capa competitiva "
        f"su neurona apagó a la de {perdedor['nombre']} tras {iteraciones} "
        f"iteración{'es' if iteraciones != 1 else ''} de inhibición lateral. "
        f"Cumple {len(ganador['requisitos_cumplidos'])} requisito(s) con evidencia y reporta "
        f"{ganador['anios_experiencia']} año(s) de experiencia, frente a "
        f"{len(perdedor['requisitos_cumplidos'])} requisito(s) y {perdedor['anios_experiencia']} "
        f"año(s) de {perdedor['nombre']}."
    )
    solo_ganador = set(ganador["requisitos_cumplidos"]) - set(perdedor["requisitos_cumplidos"])
    if solo_ganador:
        texto += " Solo el ganador muestra: " + ", ".join(sorted(solo_ganador)) + "."
    if set(ganador["requisitos_cumplidos"]) == set(perdedor["requisitos_cumplidos"]):
        texto += (
            " Ambas muestran los mismos requisitos, así que la red decide por la experiencia y"
            " por otras señales del texto; tome esta diferencia con cautela."
        )
    elif len(ganador["requisitos_cumplidos"]) < len(perdedor["requisitos_cumplidos"]):
        texto += (
            " La red lo prefiere aunque tenga menos requisitos detectados por palabras clave: "
            "reconoce en el texto señales que el evaluador no encuentra."
        )
    return texto


def torneo(cvs: list[dict], requisitos: list[str], top: int = 5, semilla: int | None = None) -> dict:
    """
    Dos formas de poner a competir a las hojas de vida:
      - Torneo: eliminación directa, cada duelo es una MAXNET de 2 neuronas.
      - Competencia abierta: una MAXNET con todas las neuronas a la vez; el
        podio se arma retirando a la ganadora y repitiendo.
    """
    participantes = [preparar(cv, requisitos) for cv in cvs]
    resultado = jugar_torneo(participantes, duelo, semilla)
    por_id = {p["id"]: p for p in participantes}
    for ronda in resultado["rondas"]:
        for d in ronda["duelos"]:
            d["explicacion"] = explicar_duelo(por_id[d["a"]], por_id[d["b"]], {
                "gana_a": d["ganador"] == d["a"], **d,
            })

    fuerzas = [p["fuerza"] for p in participantes]
    abierta = maxnet(fuerzas)
    return {
        "participantes": participantes,
        "podio": [participantes[i] for i in podio(fuerzas, top)],
        "competencia_abierta": {
            "ids": [p["id"] for p in participantes],
            "ganador": participantes[abierta["ganador"]]["id"],
            **_resumen_maxnet(abierta),
        },
        **resultado,
    }
