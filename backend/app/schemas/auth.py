from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., examples=["admin@cvscope.co"])
    contrasena: str = Field(..., min_length=1)


class UsuarioResponse(BaseModel):
    id: int
    email: str
    nombre: str


class LoginResponse(BaseModel):
    token: str
    usuario: UsuarioResponse


class UsuarioCreate(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    nombre: str = Field(..., min_length=2, max_length=150)
    contrasena: str = Field(..., min_length=8, description="Mínimo 8 caracteres.")
