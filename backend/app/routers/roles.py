from fastapi import APIRouter, HTTPException

from app.schemas.rol import RolCreate, RolResponse
from app.models.store import rol_store

router = APIRouter()


@router.get("/", response_model=list[RolResponse])
def listar_roles():
    return rol_store.list_all()


@router.get("/{rol_id}", response_model=RolResponse)
def obtener_rol(rol_id: int):
    rol = rol_store.get(rol_id)
    if rol is None:
        raise HTTPException(status_code=404, detail=f"Rol {rol_id} no encontrado")
    return rol


@router.post("/", response_model=RolResponse, status_code=201)
def crear_rol(data: RolCreate):
    return rol_store.create(data)