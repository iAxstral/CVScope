from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.store import candidato_store
from app.services.ia_services import categorizar_rol

router = APIRouter()


class CategorizarRequest(BaseModel):
    candidato_id: int | None = Field(
        default=None,
        description="Id de un candidato ya registrado; si se envía, se usa su hoja_de_vida_texto guardada.",
    )
    hoja_de_vida_texto: str | None = Field(
        default=None,
        min_length=20,
        description="Texto plano de una hoja de vida a categorizar directamente, sin necesidad de un candidato registrado.",
    )


class CategorizarResponse(BaseModel):
    candidato_id: int | None = None
    rol_predicho: str = Field(..., examples=["fullstack"])


@router.post("/categorizar", response_model=CategorizarResponse)
def categorizar_candidato(data: CategorizarRequest):
    """
    Paso 1: dado el texto de una hoja de vida (directo o de un candidato ya
    registrado), el clasificador determina a qué rol/categoría profesional
    pertenece (fullstack, rrhh, ventas, marketing, etc.).
    """
    if data.candidato_id is None and data.hoja_de_vida_texto is None:
        raise HTTPException(
            status_code=400,
            detail="Debe enviarse candidato_id o hoja_de_vida_texto",
        )

    if data.candidato_id is not None:
        candidato = candidato_store.get(data.candidato_id)
        if candidato is None:
            raise HTTPException(status_code=404, detail=f"Candidato {data.candidato_id} no encontrado")
        texto = candidato["hoja_de_vida_texto"]
    else:
        texto = data.hoja_de_vida_texto

    rol_predicho = categorizar_rol(texto)

    return CategorizarResponse(candidato_id=data.candidato_id, rol_predicho=rol_predicho)


@router.post("/evaluar")
def evaluar_candidato():
    """
    Paso 2: dado un candidato ya categorizado en un rol, evalúa si cumple
    los requisitos mínimos de ese rol (apto/no apto) y genera una
    explicación de qué requisitos cumple y cuáles no.
    """
    raise HTTPException(
        status_code=501,
        detail="Pendiente: requiere el clasificador de requisitos, aún no entrenado",
    )


@router.get("/ranking/{rol_id}")
def ranking_por_rol(rol_id: int):
    """
    Paso 3: entre los candidatos aptos de un mismo rol, genera un ranking
    ordenado de mejor a peor ajuste con el perfil buscado.
    """
    raise HTTPException(
        status_code=501,
        detail="Pendiente: requiere el clasificador de requisitos, aún no entrenado",
    )
