"""
Entrena la red neuronal competitiva (app/ml_models/red_competitiva.npz).

  - Entrenamiento y validación: duelos entre hojas de vida del MISMO rol del
    dataset de selección. Gana la que tiene mayor puntaje de referencia
    (requisitos realmente cumplidos + experiencia, según las etiquetas).
  - Prueba: dataset de ranking, que la red nunca ve. Se mide la exactitud en
    duelos y la precisión@5 del torneo, comparadas con el evaluador por
    palabras clave (línea base).

Uso (desde backend/):
    python scripts/entrenar_red_competitiva.py
"""

import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.datasets import cargar_ranking, cargar_seleccion, requisitos_por_clave  # noqa: E402
from app.services.evaluador_requisitos import (  # noqa: E402
    ANIOS_EXPERIENCIA_TOPE,
    PESO_EXPERIENCIA,
    PESO_REQUISITOS,
    evaluar_cv,
)
from app.services.red_competitiva.caracteristicas import DIM_ENTRADA, DIM_HASH, extraer  # noqa: E402
from app.services.red_competitiva.modelo import RedCompetitiva  # noqa: E402
from app.services.red_competitiva.competitiva import podio  # noqa: E402

RUTA_MODELO = Path(__file__).resolve().parent.parent / "app" / "ml_models" / "red_competitiva.npz"
SEMILLA = 2026
EPOCAS = 40
TAMANO_LOTE = 128
TASA = 2e-3
L2 = 1e-4
FRACCION_VALIDACION = 0.2
TOP = 5


def puntaje_referencia(fila: dict) -> float:
    n_req = len(requisitos_por_clave(fila["rol"]))
    fraccion = len(fila["requisitos_cumplidos"]) / n_req
    anios = min(fila["anios_experiencia"], ANIOS_EXPERIENCIA_TOPE) / ANIOS_EXPERIENCIA_TOPE
    return PESO_REQUISITOS * fraccion + PESO_EXPERIENCIA * anios


def preparar(filas: list[dict]) -> list[dict]:
    return [
        {
            "id": f["id"],
            "rol": f["rol"],
            "x": extraer(f["hoja_de_vida_texto"], requisitos_por_clave(f["rol"])),
            "ref": puntaje_referencia(f),
            "base": evaluar_cv(f["hoja_de_vida_texto"], requisitos_por_clave(f["rol"]))["score"],
        }
        for f in filas
    ]


def pares(cvs: list[dict], con_empates: bool = False) -> list[tuple[dict, dict]]:
    """Todos los duelos posibles dentro de cada rol (los empates solo si se piden)."""
    resultado = []
    for rol in sorted({c["rol"] for c in cvs}):
        del_rol = [c for c in cvs if c["rol"] == rol]
        resultado += [
            (a, b) for a, b in itertools.combinations(del_rol, 2) if con_empates or a["ref"] != b["ref"]
        ]
    return resultado


def etiqueta_duelo(a: dict, b: dict) -> float:
    """1 si gana A, 0 si gana B y 0.5 si empatan: así la red aprende a dudar."""
    return 1.0 if a["ref"] > b["ref"] else 0.0 if a["ref"] < b["ref"] else 0.5


def dividir(cvs: list[dict], rng: np.random.Generator) -> tuple[list[dict], list[dict]]:
    entrenamiento, validacion = [], []
    for rol in sorted({c["rol"] for c in cvs}):
        del_rol = [c for c in cvs if c["rol"] == rol]
        orden = rng.permutation(len(del_rol))
        corte = int(len(del_rol) * FRACCION_VALIDACION)
        validacion += [del_rol[i] for i in orden[:corte]]
        entrenamiento += [del_rol[i] for i in orden[corte:]]
    return entrenamiento, validacion


def exactitud_red(red: RedCompetitiva, duelos) -> float:
    x_a = np.stack([a["x"] for a, _ in duelos])
    x_b = np.stack([b["x"] for _, b in duelos])
    y = np.array([a["ref"] > b["ref"] for a, b in duelos])
    return float(np.mean((red.probabilidad(x_a, x_b) >= 0.5) == y))


def exactitud_base(duelos) -> float:
    # La línea base "acierta" solo si su puntaje ordena estrictamente bien el par.
    return float(np.mean([(a["base"] > b["base"]) == (a["ref"] > b["ref"]) and a["base"] != b["base"]
                          for a, b in duelos]))


def precision_top(cvs: list[dict], fuerza) -> dict[str, int]:
    """Cuántos del top real recupera el podio de la capa competitiva (MAXNET)."""
    resultado = {}
    for rol in sorted({c["rol"] for c in cvs}):
        del_rol = [c for c in cvs if c["rol"] == rol]
        real = {c["id"] for c in sorted(del_rol, key=lambda c: (-c["ref"], c["id"]))[:TOP]}
        puestos = podio([fuerza(c) for c in del_rol], TOP)
        resultado[rol] = len(real & {del_rol[i]["id"] for i in puestos})
    return resultado


def entrenar(duelos, rng: np.random.Generator) -> RedCompetitiva:
    red = RedCompetitiva(DIM_ENTRADA, semilla=SEMILLA)
    x_a = np.stack([a["x"] for a, _ in duelos])
    x_b = np.stack([b["x"] for _, b in duelos])
    y = np.array([etiqueta_duelo(a, b) for a, b in duelos], dtype=np.float32)

    for epoca in range(1, EPOCAS + 1):
        orden = rng.permutation(len(y))
        # Se intercambia A/B al azar para que la red no aprenda el orden del par.
        invertir = rng.random(len(y)) < 0.5
        perdidas = []
        for inicio in range(0, len(y), TAMANO_LOTE):
            idx = orden[inicio:inicio + TAMANO_LOTE]
            inv = invertir[idx][:, None]
            a = np.where(inv, x_b[idx], x_a[idx])
            b = np.where(inv, x_a[idx], x_b[idx])
            etiqueta = np.where(invertir[idx], 1 - y[idx], y[idx])
            perdidas.append(red.paso(a, b, etiqueta, tasa=TASA, l2=L2))
        if epoca == 1 or epoca % 10 == 0:
            print(f"   época {epoca:>3}  pérdida {np.mean(perdidas):.4f}")
    return red


def main() -> None:
    rng = np.random.default_rng(SEMILLA)
    seleccion = preparar(cargar_seleccion())
    prueba = preparar(cargar_ranking())
    entrenamiento, validacion = dividir(seleccion, rng)

    duelos_ent = pares(entrenamiento, con_empates=True)
    duelos_val, duelos_prueba = pares(validacion), pares(prueba)
    empates_prueba = [(a, b) for a, b in pares(prueba, con_empates=True) if a["ref"] == b["ref"]]
    print(f"Duelos -> entrenamiento {len(duelos_ent)} | validación {len(duelos_val)} | prueba {len(duelos_prueba)}")

    red = entrenar(duelos_ent, rng)

    def fuerza_red(c):
        return float(red.puntaje(c["x"])[0])

    def fuerza_base(c):
        return c["base"]

    exact = {
        "val_red": exactitud_red(red, duelos_val),
        "val_base": exactitud_base(duelos_val),
        "prueba_red": exactitud_red(red, duelos_prueba),
        "prueba_base": exactitud_base(duelos_prueba),
    }
    if empates_prueba:
        x_a = np.stack([a["x"] for a, _ in empates_prueba])
        x_b = np.stack([b["x"] for _, b in empates_prueba])
        exact["confianza_empates"] = float(np.mean(np.abs(red.probabilidad(x_a, x_b) - 0.5) * 2))
    top_red = precision_top(prueba, fuerza_red)
    top_base = precision_top(prueba, fuerza_base)
    p5_red = sum(top_red.values()) / (TOP * len(top_red))
    p5_base = sum(top_base.values()) / (TOP * len(top_base))

    print("\n                         Red competitiva   Palabras clave")
    print(f"Exactitud duelos (val)   {exact['val_red']:>15.3f}   {exact['val_base']:>14.3f}")
    print(f"Exactitud duelos (test)  {exact['prueba_red']:>15.3f}   {exact['prueba_base']:>14.3f}")
    for rol in top_red:
        print(f"Top {TOP} {rol:<17} {top_red[rol]:>13}/{TOP}   {top_base[rol]:>12}/{TOP}")
    print(f"Precisión@{TOP} promedio     {p5_red:>15.3f}   {p5_base:>14.3f}")
    if "confianza_empates" in exact:
        print(f"Confianza media en {len(empates_prueba)} empates de prueba (0 = duda, 1 = segura): "
              f"{exact['confianza_empates']:.3f}")

    red.guardar(
        RUTA_MODELO,
        dim_hash=DIM_HASH,
        epocas=EPOCAS,
        exactitud_duelos_prueba=exact["prueba_red"],
        precision_top5_prueba=p5_red,
        exactitud_duelos_prueba_base=exact["prueba_base"],
        precision_top5_prueba_base=p5_base,
        confianza_empates_prueba=exact.get("confianza_empates", 0.0),
    )
    print(f"\nModelo guardado en {RUTA_MODELO}")


if __name__ == "__main__":
    main()
