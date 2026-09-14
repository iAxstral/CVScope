from pydantic import BaseModel, Field


class RolBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["Full Stack Developer"])
    requisitos: list[str] = Field(
        ...,
        min_length=1,
        description="Lista de requisitos mínimos que debe cumplir un candidato para este rol.",
        examples=[["JavaScript/TypeScript", "React", "Node.js"]],
    )


class RolCreate(RolBase):
    """Datos que se envían al crear un rol nuevo."""
    pass


class RolResponse(RolBase):
    """Lo que la API devuelve: incluye el id asignado."""
    id: int

    class Config:
        from_attributes = True