from fastapi import APIRouter, HTTPException, Query

from app.schemas.candidato import CandidatoCreate, CandidatoResponse
from app.models.store import candidato_store, rol_store

router = APIRouter()


@router.get("/", response_model=list[CandidatoResponse])
def listar_candidatos(rol_id: int | None = Query(default=None)):
    if rol_id is not None:
        return candidato_store.list_by_rol(rol_id)
    return candidato_store.list_all()


@router.get("/{candidato_id}", response_model=CandidatoResponse)
def obtener_candidato(candidato_id: int):
    candidato = candidato_store.get(candidato_id)
    if candidato is None:
        raise HTTPException(status_code=404, detail=f"Candidato {candidato_id} no encontrado")
    return candidato


@router.post("/", response_model=CandidatoResponse, status_code=201)
def crear_candidato(data: CandidatoCreate):
    if data.rol_id is not None and rol_store.get(data.rol_id) is None:
        raise HTTPException(status_code=400, detail=f"El rol_id {data.rol_id} no existe")

    candidato = candidato_store.create(data)

    if candidato["rol_id"] is not None:
        rol = rol_store.get(candidato["rol_id"])
        candidato_store.update(candidato["id"], rol_nombre=rol["nombre"])

    return candidato_store.get(candidato["id"])