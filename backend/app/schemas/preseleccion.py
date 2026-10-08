from pydantic import BaseModel, Field

from app.schemas.candidato import EstadoEvaluacion


class EvaluacionRequisito(BaseModel):
    requisito: str
    cumple: bool
    evidencia: str | None = Field(
        default=None, description="Fragmento de la hoja de vida que sustenta el veredicto."
    )
    nota: str


class EvaluarRequest(BaseModel):
    candidato_id: int | None = Field(
        default=None,
        description="Id de un candidato registrado; si se envía, se evalúa su hoja de vida y se guarda el resultado.",
    )
    hoja_de_vida_texto: str | None = Field(default=None, min_length=20)
    rol_id: int | None = Field(
        default=None,
        description="Rol contra el que se evalúa. Si se omite, se usa el rol del candidato "
                    "o el que prediga el clasificador.",
    )


class EvaluacionResponse(BaseModel):
    candidato_id: int | None = None
    rol_id: int
    rol_nombre: str
    rol_predicho: str | None = Field(
        default=None, description="Clave del rol predicha por el clasificador, si se usó."
    )
    score: float = Field(..., ge=0, le=100)
    estado: EstadoEvaluacion
    anios_experiencia: int
    evaluacion: list[EvaluacionRequisito]
    requisitos_cumplidos: list[str]
    requisitos_faltantes: list[str]
    explicacion: str


class Referencia(BaseModel):
    """Etiquetas reales del dataset, para comparar con lo que decidió el sistema."""
    apto: bool
    requisitos_cumplidos: list[str]
    puntaje_referencia: float | None = None
    posicion_referencia: int | None = None


class CandidatoRanking(BaseModel):
    id: str
    nombre: str
    email: str
    fuente: str = Field(..., description="'dataset' o 'registrado'")
    score: float
    estado: EstadoEvaluacion
    anios_experiencia: int
    requisitos_cumplidos: list[str]
    requisitos_faltantes: list[str]
    posicion_referencia: int | None = None


class RankingResponse(BaseModel):
    rol_id: int
    rol_nombre: str
    requisitos: list[str]
    total_evaluados: int
    total_aptos: int
    top: list[CandidatoRanking]
    coincidencias_referencia: int | None = Field(
        default=None,
        description="Cuántos del top devuelto están también en el top de referencia del dataset.",
    )


class DetalleHojaDeVida(EvaluacionResponse):
    id: str
    nombre: str
    email: str | None = None
    fuente: str
    hoja_de_vida_texto: str
    referencia: Referencia | None = None
