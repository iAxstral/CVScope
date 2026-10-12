from pydantic import BaseModel, Field


class HojaDeVidaEntrada(BaseModel):
    """Una hoja de vida para competir: por id (dataset o registrado) o por texto."""
    cv_id: str | None = Field(default=None, examples=["rk-fullstack-02"])
    hoja_de_vida_texto: str | None = Field(default=None, min_length=20)
    nombre: str | None = Field(default=None, description="Nombre a mostrar si se envía texto.")


class CompararRequest(BaseModel):
    rol_id: int
    a: HojaDeVidaEntrada
    b: HojaDeVidaEntrada


class Competidor(BaseModel):
    id: str
    nombre: str
    fuente: str
    fuerza: float = Field(..., description="Puntaje de la red: a mayor fuerza, mejor hoja de vida.")
    score_palabras_clave: float
    anios_experiencia: int
    requisitos_cumplidos: list[str]
    requisitos_faltantes: list[str]
    posicion_referencia: int | None = None
    veredicto_lvq: str | None = Field(
        default=None, description="Apto/no apto según la capa competitiva LVQ (aprendida)."
    )
    margen_lvq: float | None = Field(
        default=None, description="Confianza de la LVQ: 0 = empate entre clases, 1 = clara."
    )


class Maxnet(BaseModel):
    """Traza de la capa competitiva (inhibición lateral)."""
    epsilon: float = Field(..., description="Peso de inhibición lateral entre neuronas.")
    iteraciones: int
    trayectoria: list[list[float]] = Field(
        ..., description="Activación de cada neurona en cada iteración (la primera es la inicial)."
    )


class CompararResponse(BaseModel):
    rol_id: int
    rol_nombre: str
    a: Competidor
    b: Competidor
    prob_a: float = Field(..., ge=0, le=1, description="Probabilidad de que A gane a B.")
    ganador: str = Field(..., description="'a' o 'b'")
    explicacion: str
    maxnet: Maxnet


class TorneoRequest(BaseModel):
    rol_id: int
    cv_ids: list[str] | None = Field(
        default=None,
        description="Hojas de vida que compiten. Si se omite, compiten todas las del rol "
                    "(dataset de ranking + candidatos registrados).",
    )
    top: int = Field(default=5, ge=1, le=50)
    semilla: int | None = Field(
        default=None, description="Si se envía, sortea el cuadro; si no, se respeta el orden."
    )


class Duelo(Maxnet):
    a: str
    b: str
    ganador: str
    prob_a: float
    explicacion: str


class Ronda(BaseModel):
    numero: int
    nombre: str
    duelos: list[Duelo]
    pases: list[str] = Field(default_factory=list, description="Pasan sin jugar (bye).")


class CompetenciaAbierta(Maxnet):
    """MAXNET con todas las hojas de vida compitiendo a la vez."""
    ids: list[str] = Field(..., description="Orden de las neuronas en la trayectoria.")
    ganador: str


class TorneoResponse(BaseModel):
    rol_id: int
    rol_nombre: str
    participantes: list[Competidor]
    rondas: list[Ronda]
    campeon: Competidor
    podio: list[Competidor]
    competencia_abierta: CompetenciaAbierta
    total_duelos: int
    coincidencias_referencia: int | None = Field(
        default=None, description="Cuántos del podio están en el top de referencia del dataset."
    )


class PrototipoLVQ(BaseModel):
    neurona: int
    clase: str
    fraccion_requisitos: float
    anios_experiencia: float


class ModeloInfo(BaseModel):
    arquitectura: str
    dim_entrada: int
    metricas: dict[str, float]
    lvq: dict | None = Field(
        default=None, description="Métricas y prototipos de la capa competitiva LVQ."
    )
