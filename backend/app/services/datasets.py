"""
Acceso de solo lectura a los datasets de CVScope (backend/data/*.csv).

  - dataset_seleccion.csv: hojas de vida etiquetadas con rol y apto/no apto.
  - dataset_ranking.csv:   pool de candidatos por rol con puntaje de referencia
                           para obtener el top 5 de hojas de vida.

Ambos se generan con scripts/generar_datasets.py.
"""

import csv
from functools import lru_cache
from pathlib import Path

from app.models.store import rol_store

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
RUTA_SELECCION = DATA_DIR / "dataset_seleccion.csv"
RUTA_RANKING = DATA_DIR / "dataset_ranking.csv"


def _parsear(fila: dict) -> dict:
    fila = dict(fila)
    fila["apto"] = fila["apto"] == "1"
    fila["anios_experiencia"] = int(fila["anios_experiencia"])
    fila["requisitos_cumplidos"] = [r for r in fila["requisitos_cumplidos"].split("|") if r]
    if "puntaje_referencia" in fila:
        fila["puntaje_referencia"] = float(fila["puntaje_referencia"])
        pos = fila.get("posicion_referencia")
        fila["posicion_referencia"] = int(pos) if pos else None
    return fila


def _leer(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8", newline="") as f:
        return [_parsear(fila) for fila in csv.DictReader(f)]


@lru_cache
def cargar_seleccion() -> list[dict]:
    return _leer(RUTA_SELECCION)


@lru_cache
def cargar_ranking() -> list[dict]:
    return _leer(RUTA_RANKING)


def requisitos_por_clave(clave: str) -> list[str]:
    rol = rol_store.get_by_clave(clave)
    return rol["requisitos"] if rol else []
