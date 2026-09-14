from sentence_transformers import SentenceTransformer
import joblib
import os

_RUTA_MODELO = os.path.join(os.path.dirname(__file__), "..", "ml_models", "clasificador_rol.pkl")

_embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")
_clasificador_rol = joblib.load(_RUTA_MODELO)

def categorizar_rol(cv_texto: str) -> str:
    """Recibe el texto plano de un CV y devuelve el rol predicho (fullstack, rrhh, ventas, marketing)."""
    vector = _embeddings_model.encode([cv_texto])
    rol_predicho = _clasificador_rol.predict(vector)[0]
    return rol_predicho