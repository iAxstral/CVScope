"""
Entrena el clasificador de rol (app/ml_models/clasificador_rol.pkl):
embeddings de all-MiniLM-L6-v2 + regresión logística.

Requiere sentence-transformers y acceso a Hugging Face para descargar el
modelo de embeddings la primera vez.

Fuentes de datos (--dataset):
  sintetico (por defecto)  hojas de vida sintéticas del repo (data/dataset_seleccion.csv)
  kaggle                   CSV del dataset "Resume Dataset" de Kaggle (descarga manual,
                           ver docs/clasificador_rol.md), filtrado a los 4 roles de CVScope
  combinado                las dos anteriores juntas; la división se estratifica por
                           (rol, fuente) y las métricas se reportan también por fuente

Uso (desde backend/):
    python scripts/entrenar_clasificador_rol.py
    python scripts/entrenar_clasificador_rol.py --dataset kaggle
    python scripts/entrenar_clasificador_rol.py --dataset kaggle --csv ruta/a/Resume.csv
    python scripts/entrenar_clasificador_rol.py --dataset combinado

Además del modelo, guarda las métricas de prueba y las versiones usadas en
app/ml_models/clasificador_rol_metricas.json.
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import joblib
import sklearn
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.datasets import cargar_seleccion  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
RUTA_MODELO = RAIZ / "app" / "ml_models" / "clasificador_rol.pkl"
CSV_KAGGLE = RAIZ / "data" / "kaggle" / "Resume.csv"

SEMILLA = 2026
PROPORCION_PRUEBA = 0.2
MODELO_EMBEDDINGS = "all-MiniLM-L6-v2"

# Categorías del dataset de Kaggle (en mayúsculas y con guiones) que se conservan
# y el rol de CVScope al que corresponden. Las demás categorías se descartan.
CATEGORIA_A_ROL = {
    "INFORMATION-TECHNOLOGY": "fullstack",
    "HR": "rrhh",
    "SALES": "ventas",
    "DIGITAL-MEDIA": "marketing",
}
COLUMNAS_TEXTO = ("Resume_str", "Resume")


def cargar_sintetico() -> tuple[list[str], list[str]]:
    filas = cargar_seleccion()
    return [f["hoja_de_vida_texto"] for f in filas], [f["rol"] for f in filas]


def cargar_kaggle(ruta: Path) -> tuple[list[str], list[str]]:
    if not ruta.exists():
        sys.exit(
            f"No se encontró {ruta}.\n"
            "Descarga el CSV a mano desde Kaggle (ver docs/clasificador_rol.md) "
            "y guárdalo ahí o indica la ruta con --csv."
        )
    csv.field_size_limit(sys.maxsize)  # las hojas de vida son textos largos
    with open(ruta, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        columnas = lector.fieldnames or []
        texto = next((c for c in COLUMNAS_TEXTO if c in columnas), None)
        if texto is None or "Category" not in columnas:
            sys.exit(f"El CSV debe tener las columnas Category y {' o '.join(COLUMNAS_TEXTO)}; trae {columnas}")
        filas = list(lector)

    total = len(filas)
    textos, roles, vistos = [], [], set()
    for fila in filas:
        categoria = fila["Category"].strip().upper().replace(" ", "-")
        cv = " ".join(fila[texto].split())
        # Se descarta lo que no es de los 4 roles, lo vacío y los CV repetidos
        if categoria not in CATEGORIA_A_ROL or len(cv) < 50 or cv in vistos:
            continue
        vistos.add(cv)
        textos.append(cv)
        roles.append(CATEGORIA_A_ROL[categoria])
    print(f"Kaggle: {total} hojas de vida; quedan {len(textos)} tras filtrar a los 4 roles y quitar duplicados.")
    return textos, roles


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=["sintetico", "kaggle", "combinado"], default="sintetico")
    ap.add_argument("--csv", type=Path, default=CSV_KAGGLE, help="CSV de Kaggle (con --dataset kaggle o combinado)")
    ap.add_argument("--salida", type=Path, default=RUTA_MODELO, help="Dónde guardar el modelo (.pkl)")
    args = ap.parse_args()

    textos, etiquetas, fuentes = [], [], []
    for fuente in (["kaggle", "sintetico"] if args.dataset == "combinado" else [args.dataset]):
        t, e = cargar_kaggle(args.csv) if fuente == "kaggle" else cargar_sintetico()
        textos += t
        etiquetas += e
        fuentes += [fuente] * len(t)
    print("Hojas de vida por rol:", dict(sorted(Counter(etiquetas).items())))

    # Con varias fuentes se estratifica por (rol, fuente): ambas quedan en entrenamiento y en prueba
    estratos = [f"{e}|{f}" for e, f in zip(etiquetas, fuentes)] if args.dataset == "combinado" else etiquetas
    x_train, x_test, y_train, y_test, _, f_test = train_test_split(
        textos, etiquetas, fuentes, test_size=PROPORCION_PRUEBA, stratify=estratos, random_state=SEMILLA
    )
    print(f"Entrenamiento: {len(x_train)} · prueba: {len(x_test)} (estratificado, semilla {SEMILLA})")

    embeddings = SentenceTransformer(MODELO_EMBEDDINGS)
    clasificador = LogisticRegression(max_iter=1000)
    clasificador.fit(embeddings.encode(x_train), y_train)

    predicciones = clasificador.predict(embeddings.encode(x_test))
    print(classification_report(y_test, predicciones))

    por_fuente = {}
    for fuente in sorted(set(fuentes)):
        idx = [i for i, f in enumerate(f_test) if f == fuente]
        reales, predichas = [y_test[i] for i in idx], [predicciones[i] for i in idx]
        por_fuente[fuente] = {
            "hojas_de_vida": {"total": fuentes.count(fuente), "prueba": len(idx)},
            "por_rol": dict(sorted(Counter(e for e, f in zip(etiquetas, fuentes) if f == fuente).items())),
            "exactitud": round(float(accuracy_score(reales, predichas)), 4),
            "f1_macro": round(float(f1_score(reales, predichas, average="macro")), 4),
        }
        print(f"{fuente}: exactitud {por_fuente[fuente]['exactitud']} · F1 macro "
              f"{por_fuente[fuente]['f1_macro']} ({len(idx)} de prueba)")

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clasificador, args.salida)
    print(f"Modelo guardado en {args.salida}")

    metricas = {
        "dataset": args.dataset,
        "hojas_de_vida": {"entrenamiento": len(x_train), "prueba": len(x_test)},
        "por_rol": dict(sorted(Counter(etiquetas).items())),
        "semilla": SEMILLA,
        "proporcion_prueba": PROPORCION_PRUEBA,
        "exactitud": round(float(accuracy_score(y_test, predicciones)), 4),
        "f1_macro": round(float(f1_score(y_test, predicciones, average="macro")), 4),
        "reporte": classification_report(y_test, predicciones, output_dict=True),
        "por_fuente": por_fuente,
        "versiones": {"scikit-learn": sklearn.__version__, "embeddings": MODELO_EMBEDDINGS},
    }
    ruta_metricas = args.salida.with_name("clasificador_rol_metricas.json")
    ruta_metricas.write_text(json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Métricas guardadas en {ruta_metricas}")


if __name__ == "__main__":
    main()
