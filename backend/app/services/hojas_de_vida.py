"""
Punto único para obtener hojas de vida, vengan de los datasets o de los
candidatos registrados. Lo usan el ranking, el detalle y la red competitiva.

Identificadores:
  - "rk-..."  -> dataset de ranking
  - "sel-..." -> dataset de selección
  - "cand-N"  -> candidato registrado con id N
"""

from app.models.store import candidato_store, rol_store
from app.services.datasets import cargar_ranking, cargar_seleccion

PREFIJO_REGISTRADO = "cand-"


def pool_del_rol(rol: dict) -> list[dict]:
    """Hojas de vida que compiten en un rol: dataset de ranking + registrados."""
    pool = [
        {
            "id": f["id"],
            "nombre": f["nombre"],
            "email": f["email"],
            "texto": f["hoja_de_vida_texto"],
            "fuente": "dataset",
            "posicion_referencia": f["posicion_referencia"],
        }
        for f in cargar_ranking()
        if rol.get("clave") and f["rol"] == rol["clave"]
    ]
    pool += [
        {
            "id": f"{PREFIJO_REGISTRADO}{c['id']}",
            "nombre": c["nombre"],
            "email": c["email"],
            "texto": c["hoja_de_vida_texto"],
            "fuente": "registrado",
            "posicion_referencia": None,
        }
        for c in candidato_store.list_by_rol(rol["id"])
    ]
    return pool


def buscar(cv_id: str) -> dict | None:
    """
    Devuelve {id, nombre, email, texto, fuente, rol, referencia} o None.
    `rol` es el rol asociado (puede ser None) y `referencia` las etiquetas del
    dataset (None para candidatos registrados).
    """
    if cv_id.startswith(PREFIJO_REGISTRADO) and cv_id[len(PREFIJO_REGISTRADO):].isdigit():
        candidato = candidato_store.get(int(cv_id[len(PREFIJO_REGISTRADO):]))
        if candidato is None:
            return None
        return {
            "id": cv_id,
            "nombre": candidato["nombre"],
            "email": candidato["email"],
            "texto": candidato["hoja_de_vida_texto"],
            "fuente": "registrado",
            "rol": rol_store.get(candidato["rol_id"]) if candidato["rol_id"] else None,
            "referencia": None,
        }

    fila = next((f for f in cargar_ranking() + cargar_seleccion() if f["id"] == cv_id), None)
    if fila is None:
        return None
    texto = fila["hoja_de_vida_texto"]
    return {
        "id": cv_id,
        "nombre": fila.get("nombre") or texto.split(".")[0],
        "email": fila.get("email"),
        "texto": texto,
        "fuente": "dataset_ranking" if cv_id.startswith("rk-") else "dataset_seleccion",
        "rol": rol_store.get_by_clave(fila["rol"]),
        "referencia": {
            "apto": fila["apto"],
            "requisitos_cumplidos": fila["requisitos_cumplidos"],
            "puntaje_referencia": fila.get("puntaje_referencia"),
            "posicion_referencia": fila.get("posicion_referencia"),
        },
    }
