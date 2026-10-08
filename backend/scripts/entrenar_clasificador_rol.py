"""
Entrena el clasificador de rol (app/ml_models/clasificador_rol.pkl) con el
dataset de selección: embeddings de all-MiniLM-L6-v2 + regresión logística.

Requiere sentence-transformers y acceso a Hugging Face para descargar el
modelo de embeddings la primera vez.

Uso (desde backend/):
    python scripts/entrenar_clasificador_rol.py
"""

import sys
from pathlib import Path

import joblib
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.datasets import cargar_seleccion  # noqa: E402

RUTA_MODELO = Path(__file__).resolve().parent.parent / "app" / "ml_models" / "clasificador_rol.pkl"


def main() -> None:
    filas = cargar_seleccion()
    textos = [f["hoja_de_vida_texto"] for f in filas]
    etiquetas = [f["rol"] for f in filas]

    x_train, x_test, y_train, y_test = train_test_split(
        textos, etiquetas, test_size=0.2, stratify=etiquetas, random_state=2026
    )

    embeddings = SentenceTransformer("all-MiniLM-L6-v2")
    clasificador = LogisticRegression(max_iter=1000)
    clasificador.fit(embeddings.encode(x_train), y_train)

    predicciones = clasificador.predict(embeddings.encode(x_test))
    print(classification_report(y_test, predicciones))

    joblib.dump(clasificador, RUTA_MODELO)
    print(f"Modelo guardado en {RUTA_MODELO}")


if __name__ == "__main__":
    main()
