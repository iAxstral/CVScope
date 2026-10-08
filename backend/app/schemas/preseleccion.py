from typing import Literal

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
    motor: Literal["palabras_clave", "llm"] = Field(
        default="palabras_clave",
        description="'palabras_clave' (determinístico, sin red) o 'llm' (Gemini, requiere API key).",
    )


class EvaluacionResponse(BaseModel):
    candidato_id: int | None = None
    motor: str = "palabras_clave"
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
    fuerza: float | None = Field(
        default=None, description="Fuerza que le asigna la red competitiva (si se usó)."
    )


class RankingResponse(BaseModel):
    rol_id: int
    rol_nombre: str
    requisitos: list[str]
    metodo: Literal["red", "palabras_clave"] = Field(
        ..., description="Con qué se ordenó el top: la red competitiva o las palabras clave."
    )
    total_evaluados: int
    total_aptos: int
    top: list[CandidatoRanking]
    top_otro_metodo: list[str] = Field(
        default_factory=list,
        description="Ids del top según el otro método, para comparar ambos rankings.",
    )
    aviso: str | None = None
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


class MotoresResponse(BaseModel):
    palabras_clave: bool = True
    llm: bool = Field(..., description="True si hay API key de Gemini configurada.")
    modelo_llm: str
