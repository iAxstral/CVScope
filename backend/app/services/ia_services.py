import os
from functools import lru_cache

_RUTA_MODELO = os.path.join(os.path.dirname(__file__), "..", "ml_models", "clasificador_rol.pkl")


class ClasificadorNoDisponible(RuntimeError):
    """El modelo de embeddings o el clasificador no se pudieron cargar."""


@lru_cache
def _cargar_modelos():
    # Carga diferida: la API arranca aunque sentence-transformers no esté
    # instalado o no haya red para descargar el modelo de embeddings; solo
    # falla el endpoint que necesita el clasificador.
    try:
        import joblib
        from sentence_transformers import SentenceTransformer

        embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")
        clasificador_rol = joblib.load(_RUTA_MODELO)
    except Exception as exc:
        raise ClasificadorNoDisponible(
            f"No se pudo cargar el clasificador de rol: {exc}"
        ) from exc
    return embeddings_model, clasificador_rol


def categorizar_rol(cv_texto: str) -> str:
    """Recibe el texto plano de un CV y devuelve el rol predicho (fullstack, rrhh, ventas, marketing)."""
    embeddings_model, clasificador_rol = _cargar_modelos()
    vector = embeddings_model.encode([cv_texto])
    return str(clasificador_rol.predict(vector)[0])
