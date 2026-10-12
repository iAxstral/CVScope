"""
Uso de la red competitiva entrenada desde la API.

Arquitectura (tipo red de Hamming):
  1. Entrada: vector de 1026 características de cada hoja de vida anonimizada.
  2. Capa de evaluación (feedforward, entrenada): red siamesa 1026-64-32-1 que
     le asigna a cada hoja de vida su fuerza s(x).
  3. Capa competitiva (recurrente, MAXNET): una neurona por hoja de vida; se
     inhiben entre sí hasta que solo queda una activa.
  4. Salida: la hoja de vida ganadora (one-hot) y la probabilidad de cada una.

Además, una capa competitiva que aprende (LVQ, lvq.py) decide apto/no apto:
sus neuronas son prototipos y gana la más cercana a la hoja de vida.
"""

from functools import lru_cache
from pathlib import Path

from app.services.evaluador_requisitos import evaluar_cv, quitar_evidencia, quitar_experiencia
from app.services.red_competitiva.caracteristicas import DIM_ENTRADA, extraer
from app.services.red_competitiva.competitiva import maxnet, podio
from app.services.red_competitiva.lvq import CapaLVQ
from app.services.red_competitiva.modelo import RedCompetitiva
from app.services.red_competitiva.torneo import jugar_torneo

RUTA_MODELO = Path(__file__).resolve().parent.parent.parent / "ml_models" / "red_competitiva.npz"
RUTA_LVQ = RUTA_MODELO.with_name("lvq_seleccion.npz")


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


@lru_cache
def cargar_lvq() -> tuple[CapaLVQ, dict] | None:
    """La capa LVQ es opcional: si no está entrenada, no se reporta su veredicto."""
    if not RUTA_LVQ.exists():
        return None
    capa, meta = CapaLVQ.cargar(RUTA_LVQ)
    return (capa, meta) if capa.prototipos.shape[1] == DIM_ENTRADA else None


def clasificar_lvq(x) -> dict | None:
    """Veredicto apto/no apto de la capa competitiva LVQ para un vector x."""
    lvq = cargar_lvq()
    return lvq[0].competir(x) if lvq else None


def preparar(cv: dict, requisitos: list[str]) -> dict:
    """Agrega a la hoja de vida su vector, su fuerza y el resumen de requisitos."""
    red, _ = cargar_modelo()
    x = extraer(cv["texto"], requisitos)
    evaluacion = evaluar_cv(cv["texto"], requisitos)
    lvq = clasificar_lvq(x)
    return {
        **cv,
        "x": x,
        "fuerza": float(red.puntaje(x)[0]),
        "veredicto_lvq": lvq["veredicto"] if lvq else None,
        "margen_lvq": round(lvq["margen"], 3) if lvq else None,
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
        f"{'iteración' if iteraciones == 1 else 'iteraciones'} de inhibición lateral. "
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


def _contribuciones(cv: dict, requisitos: list[str]) -> dict:
    """
    Cuánto aporta cada requisito a la fuerza de una hoja de vida, por ablación:
    fuerza con el texto completo menos la fuerza sin las menciones que sirven
    de evidencia de ese requisito; igual para la experiencia declarada. Lo que
    no se explica por ninguno de los dos (el punto de partida de la red y las
    demás señales del texto) queda en `otras_senales`, de modo que
    fuerza = suma de aportes de requisitos + experiencia + otras_senales.
    """
    red, _ = cargar_modelo()
    evaluacion = {e["requisito"]: e for e in evaluar_cv(cv["texto"], requisitos)["evaluacion"]}
    detalle = []
    for requisito in requisitos:
        e = evaluacion[requisito]
        contribucion = 0.0
        if e["cumple"]:
            sin_evidencia = extraer(quitar_evidencia(cv["texto"], requisito), requisitos)
            contribucion = cv["fuerza"] - float(red.puntaje(sin_evidencia)[0])
        detalle.append({
            "requisito": requisito,
            "cumple": e["cumple"],
            "evidencia": e["evidencia"],
            "contribucion": contribucion,
        })
    sin_experiencia = extraer(quitar_experiencia(cv["texto"]), requisitos)
    experiencia = cv["fuerza"] - float(red.puntaje(sin_experiencia)[0]) if cv["anios_experiencia"] else 0.0
    return {
        "requisitos": detalle,
        "experiencia": experiencia,
        "otras_senales": cv["fuerza"] - sum(d["contribucion"] for d in detalle) - experiencia,
    }


_DATOS_PARTICIPANTE = ("id", "nombre", "fuente", "fuerza", "anios_experiencia")


def explicar_ranking(cvs: list[dict], requisitos: list[str]) -> dict:
    """
    Por qué ganó la primera hoja de vida de la competencia: fuerza de cada
    requisito, comparación contra la segunda y margen de la victoria.
    Necesita al menos dos hojas de vida.
    """
    participantes = [preparar(cv, requisitos) for cv in cvs]
    primero, segundo = (participantes[i] for i in podio([p["fuerza"] for p in participantes], 2))
    pg, ps = _contribuciones(primero, requisitos), _contribuciones(segundo, requisitos)
    resultado = duelo(primero, segundo)

    por_requisito = []
    for g, s in zip(pg["requisitos"], ps["requisitos"]):
        por_requisito.append({
            "requisito": g["requisito"],
            "ganador": {k: g[k] for k in ("cumple", "evidencia", "contribucion")},
            "segundo": {k: s[k] for k in ("cumple", "evidencia", "contribucion")},
            "ventaja": g["contribucion"] - s["contribucion"],
        })
    ventaja_experiencia = pg["experiencia"] - ps["experiencia"]
    ventaja_otras = pg["otras_senales"] - ps["otras_senales"]

    margen = primero["fuerza"] - segundo["fuerza"]
    iteraciones = resultado["iteraciones"]
    decisivo = max(por_requisito, key=lambda r: r["ventaja"], default=None)
    partes = [
        f"{primero['nombre']} gana a {segundo['nombre']} por un margen de {margen:.2f} puntos de fuerza "
        f"(probabilidad {resultado['prob_a']:.1%}); la competencia terminó en {iteraciones} "
        f"{'iteración' if iteraciones == 1 else 'iteraciones'} de inhibición lateral."
    ]
    if decisivo and decisivo["ventaja"] > 0.01:
        partes.append(f"El requisito que más la favorece es «{decisivo['requisito']}» ({decisivo['ventaja']:+.2f}).")
    ventaja_requisitos = sum(r["ventaja"] for r in por_requisito)
    partes.append(
        f"Frente a la segunda, los requisitos le suman {ventaja_requisitos:+.2f}, la experiencia "
        f"{ventaja_experiencia:+.2f} y el resto {ventaja_otras:+.2f} (interacciones entre señales y punto de partida de la red)."
    )
    return {
        "total_competidores": len(participantes),
        "ganador": {**{k: primero[k] for k in _DATOS_PARTICIPANTE},
                    "experiencia": pg["experiencia"], "otras_senales": pg["otras_senales"]},
        "segundo": {**{k: segundo[k] for k in _DATOS_PARTICIPANTE},
                    "experiencia": ps["experiencia"], "otras_senales": ps["otras_senales"]},
        "requisitos": por_requisito,
        "ventaja_experiencia": ventaja_experiencia,
        "ventaja_otras_senales": ventaja_otras,
        "margen": {
            "fuerza": margen,
            "probabilidad_ganador": resultado["prob_a"],
            "iteraciones": iteraciones,
            "epsilon": resultado["epsilon"],
        },
        "resumen": " ".join(partes),
    }
