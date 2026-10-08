"""
Uso de la red competitiva entrenada desde la API.
"""

from functools import lru_cache
from pathlib import Path

from app.services.evaluador_requisitos import evaluar_cv
from app.services.red_competitiva.caracteristicas import DIM_ENTRADA, extraer
from app.services.red_competitiva.modelo import RedCompetitiva
from app.services.red_competitiva.torneo import clasificar, jugar_torneo

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


def comparar(a: dict, b: dict) -> float:
    """P(a gana a b) para dos hojas de vida ya preparadas."""
    red, _ = cargar_modelo()
    return float(red.probabilidad(a["x"], b["x"])[0])


def explicar_duelo(a: dict, b: dict, prob_a: float) -> str:
    ganador, perdedor, prob = (a, b, prob_a) if prob_a >= 0.5 else (b, a, 1 - prob_a)
    texto = (
        f"{ganador['nombre']} gana con una probabilidad de {prob:.1%}. "
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
    participantes = [preparar(cv, requisitos) for cv in cvs]
    resultado = jugar_torneo(participantes, comparar, semilla)
    podio = clasificar(participantes, comparar, top, semilla)
    return {"participantes": participantes, "podio": podio, **resultado}
