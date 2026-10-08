"""
Entrena la capa competitiva LVQ que decide apto / no apto
(app/ml_models/lvq_seleccion.npz).

  - Entrenamiento y validación: dataset de selección (80 % / 20 %, misma
    división por rol que la red competitiva).
  - Prueba: dataset de ranking, que la LVQ nunca ve.
  - Línea base: el evaluador por palabras clave con el umbral fijo del 66 %.

La configuración (peso 3 para los rasgos explícitos y 2 prototipos por clase)
se eligió comparando opciones en validación, no en prueba.

Uso (desde backend/):
    python scripts/entrenar_lvq.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.datasets import cargar_ranking, cargar_seleccion, requisitos_por_clave  # noqa: E402
from app.services.evaluador_requisitos import ANIOS_EXPERIENCIA_TOPE, evaluar_cv  # noqa: E402
from app.services.red_competitiva.caracteristicas import DIM_ENTRADA, extraer  # noqa: E402
from app.services.red_competitiva.lvq import CLASES, CapaLVQ  # noqa: E402

RUTA_MODELO = Path(__file__).resolve().parent.parent / "app" / "ml_models" / "lvq_seleccion.npz"
SEMILLA = 2026
PESO_RASGOS_EXPLICITOS = 3.0
PROTOTIPOS_POR_CLASE = 2
EPOCAS = 40
ALFA_INICIAL = 0.05


def preparar(filas: list[dict]):
    x = np.stack([extraer(f["hoja_de_vida_texto"], requisitos_por_clave(f["rol"])) for f in filas])
    y = np.array([int(f["apto"]) for f in filas])
    base = np.array([
        evaluar_cv(f["hoja_de_vida_texto"], requisitos_por_clave(f["rol"]))["estado"] == "apto"
        for f in filas
    ]).astype(int)
    roles = np.array([f["rol"] for f in filas])
    return x, y, base, roles


def dividir(roles: np.ndarray, rng: np.random.Generator):
    entrenamiento, validacion = [], []
    for rol in sorted(set(roles)):
        idx = rng.permutation(np.flatnonzero(roles == rol))
        corte = int(len(idx) * 0.2)
        validacion += list(idx[:corte])
        entrenamiento += list(idx[corte:])
    return np.array(entrenamiento), np.array(validacion)


def metricas(pred: np.ndarray, y: np.ndarray) -> dict:
    vp = int(np.sum((pred == 1) & (y == 1)))
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    precision = vp / (vp + fp) if vp + fp else 0.0
    recall = vp / (vp + fn) if vp + fn else 0.0
    return {
        "exactitud": float(np.mean(pred == y)),
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
    }


def main() -> None:
    rng = np.random.default_rng(SEMILLA)
    x, y, base, roles = preparar(cargar_seleccion())
    xt, yt, base_t, _ = preparar(cargar_ranking())
    entrenamiento, validacion = dividir(roles, rng)

    pesos = np.ones(DIM_ENTRADA, np.float32)
    pesos[:2] = PESO_RASGOS_EXPLICITOS
    capa = CapaLVQ.entrenar(
        x[entrenamiento], y[entrenamiento],
        prototipos_por_clase=PROTOTIPOS_POR_CLASE, epocas=EPOCAS,
        alfa_inicial=ALFA_INICIAL, pesos_rasgos=pesos, semilla=SEMILLA,
    )

    val_lvq, val_base = metricas(capa.predecir(x[validacion]), y[validacion]), metricas(base[validacion], y[validacion])
    test_lvq, test_base = metricas(capa.predecir(xt), yt), metricas(base_t, yt)

    print(f"Hojas de vida -> entrenamiento {len(entrenamiento)} | validación {len(validacion)} | prueba {len(yt)}")
    print("\n                      LVQ (aprende)   Palabras clave (umbral fijo 66 %)")
    for nombre, (lvq, b) in {"Validación": (val_lvq, val_base), "Prueba": (test_lvq, test_base)}.items():
        print(f"{nombre:<12} exactitud {lvq['exactitud']:>8.3f}   {b['exactitud']:>10.3f}")
        print(f"{'':<12} F1        {lvq['f1']:>8.3f}   {b['f1']:>10.3f}")

    print("\nPrototipos aprendidos (en unidades originales):")
    for k, (w, c) in enumerate(zip(capa.prototipos, capa.clases)):
        fraccion = w[0] / PESO_RASGOS_EXPLICITOS
        anios = w[1] / PESO_RASGOS_EXPLICITOS * ANIOS_EXPERIENCIA_TOPE
        print(f"  neurona {k} · {CLASES[c]:<8} fracción de requisitos {fraccion:.2f} · {anios:4.1f} años")

    capa.guardar(
        RUTA_MODELO,
        exactitud_prueba=test_lvq["exactitud"],
        f1_prueba=test_lvq["f1"],
        exactitud_prueba_base=test_base["exactitud"],
        f1_prueba_base=test_base["f1"],
        exactitud_validacion=val_lvq["exactitud"],
        exactitud_validacion_base=val_base["exactitud"],
    )
    print(f"\nModelo guardado en {RUTA_MODELO}")


if __name__ == "__main__":
    main()
