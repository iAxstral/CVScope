import random

from fastapi import APIRouter, HTTPException, Query

from app.services.datasets import cargar_ranking, cargar_seleccion

router = APIRouter()

DESCRIPCIONES = {
    "seleccion": "Hojas de vida etiquetadas con su rol y el veredicto apto/no apto. "
                 "Se usa para entrenar el clasificador de rol y validar la selección.",
    "ranking": "Pool de candidatos por rol con puntaje y posición de referencia. "
               "Se usa para obtener y validar el top 5 de hojas de vida por rol.",
}


def _resumen(nombre: str, filas: list[dict]) -> dict:
    por_rol: dict[str, dict] = {}
    for f in filas:
        stats = por_rol.setdefault(f["rol"], {"total": 0, "aptos": 0})
        stats["total"] += 1
        stats["aptos"] += f["apto"]
    return {
        "nombre": nombre,
        "archivo": f"data/dataset_{nombre}.csv",
        "descripcion": DESCRIPCIONES[nombre],
        "total": len(filas),
        "aptos": sum(f["apto"] for f in filas),
        "por_rol": por_rol,
    }


def _filtrar(filas: list[dict], rol: str | None, apto: bool | None, q: str | None) -> list[dict]:
    if rol:
        filas = [f for f in filas if f["rol"] == rol]
    if apto is not None:
        filas = [f for f in filas if f["apto"] == apto]
    if q:
        q = q.lower()
        filas = [f for f in filas if q in f["hoja_de_vida_texto"].lower() or q in f["id"]]
    return filas


@router.get("/")
def resumen_datasets():
    """Resumen de los dos datasets: totales y distribución por rol."""
    return [_resumen("seleccion", cargar_seleccion()), _resumen("ranking", cargar_ranking())]


@router.get("/seleccion")
def listar_seleccion(
    rol: str | None = None,
    apto: bool | None = None,
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
):
    filas = _filtrar(cargar_seleccion(), rol, apto, q)
    return {"total": len(filas), "items": filas[offset:offset + limit]}


@router.get("/seleccion/aleatorio")
def hoja_de_vida_aleatoria(rol: str | None = None):
    """Devuelve una hoja de vida al azar del dataset de selección (útil para demos)."""
    filas = _filtrar(cargar_seleccion(), rol, None, None)
    if not filas:
        raise HTTPException(status_code=404, detail="No hay hojas de vida para ese filtro")
    return random.choice(filas)


@router.get("/ranking")
def listar_ranking(
    rol: str | None = None,
    apto: bool | None = None,
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
):
    filas = _filtrar(cargar_ranking(), rol, apto, q)
    filas = sorted(filas, key=lambda f: (f["rol"], f["posicion_referencia"] or 999, f["id"]))
    return {"total": len(filas), "items": filas[offset:offset + limit]}
