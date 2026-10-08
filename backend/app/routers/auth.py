from fastapi import APIRouter, Depends, HTTPException

from app.dependencias import usuario_actual
from app.models.store import usuario_store
from app.schemas.auth import LoginRequest, LoginResponse, UsuarioCreate, UsuarioResponse
from app.services.auth import crear_token, verificar_contrasena

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    usuario = usuario_store.get_by_email(data.email)
    # Mismo mensaje si el correo no existe o la contraseña falla: no revela qué cuentas hay
    if usuario is None or not verificar_contrasena(data.contrasena, usuario["hash_contrasena"]):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    return LoginResponse(token=crear_token(usuario["id"]), usuario=usuario)


@router.get("/yo", response_model=UsuarioResponse)
def yo(usuario: dict = Depends(usuario_actual)):
    return usuario


@router.post("/usuarios", response_model=UsuarioResponse, status_code=201)
def crear_usuario(data: UsuarioCreate, _: dict = Depends(usuario_actual)):
    """Solo un usuario con sesión iniciada puede crear otros usuarios."""
    if usuario_store.get_by_email(data.email):
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese correo")
    return usuario_store.create(data.email, data.nombre, data.contrasena)
