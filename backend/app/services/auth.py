"""
Autenticación con la librería estándar (sin dependencias extra).

- Contraseñas: PBKDF2-SHA256 con sal aleatoria y 390.000 iteraciones.
- Sesión: token firmado con HMAC-SHA256 que contiene el id del usuario y la
  fecha de expiración. No se guarda en el servidor; se verifica la firma.

Variables de entorno:
  AUTH_SECRET      -> clave para firmar los tokens (obligatoria en producción;
                      si falta se genera una al arrancar y las sesiones se
                      pierden al reiniciar)
  ADMIN_EMAIL      -> usuario inicial (por defecto admin@cvscope.co)
  ADMIN_PASSWORD   -> su contraseña (por defecto cvscope2026)
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

ITERACIONES = 390_000
DURACION_TOKEN = 8 * 60 * 60  # 8 horas

_SECRETO = (os.getenv("AUTH_SECRET") or secrets.token_hex(32)).encode()


class TokenInvalido(ValueError):
    pass


def hash_contrasena(contrasena: str) -> str:
    sal = secrets.token_bytes(16)
    derivada = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), sal, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal.hex()}${derivada.hex()}"


def verificar_contrasena(contrasena: str, guardado: str) -> bool:
    try:
        algoritmo, iteraciones, sal, esperado = guardado.split("$")
    except ValueError:
        return False
    if algoritmo != "pbkdf2_sha256":
        return False
    derivada = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), bytes.fromhex(sal), int(iteraciones))
    return hmac.compare_digest(derivada.hex(), esperado)


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def _desde_b64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def crear_token(usuario_id: int, ahora: float | None = None) -> str:
    ahora = time.time() if ahora is None else ahora
    carga = _b64(json.dumps({"sub": usuario_id, "exp": int(ahora + DURACION_TOKEN)}).encode())
    firma = _b64(hmac.new(_SECRETO, carga.encode(), hashlib.sha256).digest())
    return f"{carga}.{firma}"


def leer_token(token: str, ahora: float | None = None) -> int:
    """Devuelve el id del usuario o lanza TokenInvalido."""
    try:
        carga, firma = token.split(".")
    except ValueError as exc:
        raise TokenInvalido("Token mal formado") from exc
    esperada = _b64(hmac.new(_SECRETO, carga.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(firma, esperada):
        raise TokenInvalido("Firma inválida")
    datos = json.loads(_desde_b64(carga))
    if datos["exp"] < (time.time() if ahora is None else ahora):
        raise TokenInvalido("La sesión expiró; vuelve a iniciar sesión")
    return int(datos["sub"])
