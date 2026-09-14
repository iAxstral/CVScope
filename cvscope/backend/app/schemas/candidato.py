from pydantic import BaseModel, Field
from enum import Enum


class EstadoEvaluacion(str, Enum):
    PENDIENTE = "pendiente"
    APTO = "apto"
    NO_APTO = "no_apto"


class CandidatoBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150, examples=["Juan Pérez"])
    email: str = Field(..., examples=["juan.perez@email.com"])
    hoja_de_vida_texto: str = Field(
        ...,
        min_length=20,
        description="Texto plano extraído de la hoja de vida del candidato.",
    )


class CandidatoCreate(CandidatoBase):
    rol_id: int | None = Field(
        default=None,
        description="Si se conoce de antemano el rol, se puede asignar aquí. "
                    "Si se omite, el sistema lo categoriza automáticamente.",
    )


class CandidatoResponse(CandidatoBase):
    id: int
    rol_id: int | None = None
    rol_nombre: str | None = None
    estado: EstadoEvaluacion = EstadoEvaluacion.PENDIENTE
    score: float | None = Field(default=None, ge=0, le=100)
    requisitos_cumplidos: list[str] = Field(default_factory=list)
    requisitos_faltantes: list[str] = Field(default_factory=list)
    explicacion: str | None = None

    class Config:
        from_attributes = True