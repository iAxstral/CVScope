from pydantic import BaseModel, ConfigDict, Field


class RolBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["Full Stack Developer"])
    requisitos: list[str] = Field(
        ...,
        min_length=1,
        description="Lista de requisitos mínimos que debe cumplir un candidato para este rol.",
        examples=[["JavaScript/TypeScript", "React", "Node.js"]],
    )
    clave: str | None = Field(
        default=None,
        max_length=30,
        description="Etiqueta corta del rol usada por el clasificador y los datasets "
                    "(fullstack, rrhh, ventas, marketing).",
        examples=["fullstack"],
    )
    umbral_apto: float = Field(
        default=0.66,
        ge=0.1,
        le=1.0,
        description="Fracción mínima de requisitos que debe cumplir un candidato para ser apto.",
        examples=[0.66],
    )


class RolCreate(RolBase):
    """Datos que se envían al crear un rol nuevo."""
    pass


class RolResponse(RolBase):
    """Lo que la API devuelve: incluye el id asignado."""
    id: int

    model_config = ConfigDict(from_attributes=True)