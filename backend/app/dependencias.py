from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.store import usuario_store
from app.services.auth import TokenInvalido, leer_token

_bearer = HTTPBearer(auto_error=False)


def usuario_actual(credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    """Exige un token válido en la cabecera Authorization: Bearer <token>."""
    if credenciales is None:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        usuario = usuario_store.get(leer_token(credenciales.credentials))
    except TokenInvalido as exc:
        raise HTTPException(status_code=401, detail=str(exc),
                            headers={"WWW-Authenticate": "Bearer"}) from exc
    if usuario is None:
        raise HTTPException(status_code=401, detail="El usuario ya no existe")
    return usuario
