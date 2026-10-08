"""
Convierte una hoja de vida en un vector numérico que la red pueda comparar.

El vector tiene dos partes:
  - Rasgos explícitos: fracción de requisitos del rol con evidencia textual
    (evaluador de requisitos) y años de experiencia normalizados.
  - Bolsa de n-gramas (unigramas y bigramas) proyectada con "hashing trick" a
    un tamaño fijo. Permite que la red aprenda frases que indican un requisito
    aunque no usen las palabras clave del evaluador (p. ej. "componentes
    reutilizables" como señal de React).
"""

import re
import zlib

import numpy as np

from app.services.anonimizador import anonimizar
from app.services.evaluador_requisitos import (
    ANIOS_EXPERIENCIA_TOPE,
    evaluar_cv,
    normalizar,
)

DIM_HASH = 1024
N_RASGOS = 2
DIM_ENTRADA = N_RASGOS + DIM_HASH

_MARCADOR = re.compile(r"\[[A-Z ]+\]")
_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#.]*[a-z0-9+#]|[a-z0-9]")

# Palabras muy frecuentes que no aportan información para comparar CVs.
_STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "del", "con", "por", "para",
    "un", "una", "al", "se", "su", "sus", "mas", "como", "que", "o", "e",
}


def tokenizar(texto: str) -> list[str]:
    return [t for t in _TOKEN.findall(normalizar(texto)) if t not in _STOPWORDS]


def _indice(ngrama: str) -> int:
    # crc32 es determinístico entre ejecuciones (a diferencia de hash()).
    return zlib.crc32(ngrama.encode("utf-8")) % DIM_HASH


def vector_ngramas(texto: str) -> np.ndarray:
    tokens = tokenizar(texto)
    ngramas = tokens + [f"{a} {b}" for a, b in zip(tokens, tokens[1:])]
    vec = np.zeros(DIM_HASH, dtype=np.float32)
    for ng in ngramas:
        vec[_indice(ng)] += 1.0
    vec = np.log1p(vec)
    norma = np.linalg.norm(vec)
    return vec / norma if norma > 0 else vec


def extraer(cv_texto: str, requisitos: list[str]) -> np.ndarray:
    """
    Vector de características de una hoja de vida para un rol dado.

    El texto se anonimiza primero: la red nunca ve nombre, ciudad, edad ni
    marcas de género, así no puede aprender sesgos a partir de ellos.
    """
    # Los marcadores ([CANDIDATO], [DATO PERSONAL]...) también se quitan: si
    # quedaran como palabras, "el CV menciona la edad" sería una señal más.
    cv_texto = _MARCADOR.sub(" ", anonimizar(cv_texto))
    evaluacion = evaluar_cv(cv_texto, requisitos)
    fraccion = len(evaluacion["requisitos_cumplidos"]) / len(requisitos) if requisitos else 0.0
    anios = min(evaluacion["anios_experiencia"], ANIOS_EXPERIENCIA_TOPE) / ANIOS_EXPERIENCIA_TOPE
    rasgos = np.array([fraccion, anios], dtype=np.float32)
    return np.concatenate([rasgos, vector_ngramas(cv_texto)])


def extraer_lote(textos: list[str], requisitos: list[str]) -> np.ndarray:
    if not textos:
        return np.zeros((0, DIM_ENTRADA), dtype=np.float32)
    return np.stack([extraer(t, requisitos) for t in textos])
