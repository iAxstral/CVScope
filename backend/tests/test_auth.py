import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import (
    DURACION_TOKEN,
    TokenInvalido,
    crear_token,
    hash_contrasena,
    leer_token,
    verificar_contrasena,
)

pytestmark = pytest.mark.sin_sesion
client = TestClient(app)
ADMIN = {"email": "admin@cvscope.co", "contrasena": "cvscope2026"}


def _token():
    return client.post("/auth/login", json=ADMIN).json()["token"]


def test_hash_de_contrasena():
    guardado = hash_contrasena("secreta123")
    assert "secreta123" not in guardado and guardado.startswith("pbkdf2_sha256$")
    assert verificar_contrasena("secreta123", guardado)
    assert not verificar_contrasena("otra", guardado)
    assert hash_contrasena("secreta123") != guardado  # sal distinta cada vez


def test_token_expirado_y_alterado():
    token = crear_token(7)
    assert leer_token(token) == 7
    with pytest.raises(TokenInvalido):
        leer_token(token, ahora=time.time() + DURACION_TOKEN + 1)
    carga, firma = token.split(".")
    with pytest.raises(TokenInvalido):
        leer_token(f"{carga}x.{firma}")


def test_login():
    r = client.post("/auth/login", json=ADMIN)
    assert r.status_code == 200 and r.json()["usuario"]["email"] == "admin@cvscope.co"
    assert client.post("/auth/login", json={**ADMIN, "contrasena": "mala"}).status_code == 401
    assert client.post("/auth/login", json={"email": "nadie@x.co", "contrasena": "x"}).status_code == 401


def test_endpoints_protegidos():
    assert client.get("/").status_code == 200
    for ruta in ["/roles/", "/candidatos/", "/datasets/", "/preseleccion/motores", "/competencia/modelo"]:
        assert client.get(ruta).status_code == 401, ruta
    cabecera = {"Authorization": f"Bearer {_token()}"}
    assert client.get("/roles/", headers=cabecera).status_code == 200
    assert client.get("/auth/yo", headers=cabecera).json()["nombre"] == "Administrador"
    assert client.get("/roles/", headers={"Authorization": "Bearer basura"}).status_code == 401


def test_crear_usuario_requiere_sesion():
    nuevo = {"email": "reclutadora@cvscope.co", "nombre": "Reclutadora", "contrasena": "clave-segura-1"}
    assert client.post("/auth/usuarios", json=nuevo).status_code == 401
    cabecera = {"Authorization": f"Bearer {_token()}"}
    assert client.post("/auth/usuarios", json=nuevo, headers=cabecera).status_code == 201
    assert client.post("/auth/usuarios", json=nuevo, headers=cabecera).status_code == 409
    login = client.post("/auth/login", json={"email": nuevo["email"], "contrasena": nuevo["contrasena"]})
    assert login.status_code == 200
