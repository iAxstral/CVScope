import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.limitador import LimitadorDeIntentos, limitador_login
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


def test_el_limitador_bloquea_y_se_libera_con_el_tiempo():
    limitador = LimitadorDeIntentos(max_intentos=3, ventana=60)
    for t in (0, 1, 2):
        assert limitador.segundos_de_espera("ip", "a@x.co", ahora=t) == 0
        limitador.registrar_fallo("ip", "a@x.co", ahora=t)
    assert limitador.segundos_de_espera("ip", "A@x.co ", ahora=3) > 0  # mismo correo, sin importar el formato
    assert limitador.segundos_de_espera("ip", "b@x.co", ahora=3) == 0  # otro correo no se bloquea
    assert limitador.segundos_de_espera("otra-ip", "a@x.co", ahora=3) == 0
    assert limitador.segundos_de_espera("ip", "a@x.co", ahora=61) == 0  # pasó la ventana del primer fallo
    limitador.registrar_exito("ip", "a@x.co")
    assert limitador.segundos_de_espera("ip", "a@x.co", ahora=3) == 0


def test_login_responde_429_tras_demasiados_fallos():
    limitador_login.reiniciar()
    mala = {"email": "victima@cvscope.co", "contrasena": "mala"}
    for _ in range(limitador_login.max_intentos):
        assert client.post("/auth/login", json=mala).status_code == 401
    r = client.post("/auth/login", json=mala)
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0
    # Bloqueado ese correo, otro usuario sigue entrando
    assert client.post("/auth/login", json=ADMIN).status_code == 200
    limitador_login.reiniciar()


def test_un_login_correcto_reinicia_el_contador():
    limitador_login.reiniciar()
    for _ in range(limitador_login.max_intentos - 1):
        client.post("/auth/login", json={**ADMIN, "contrasena": "mala"})
    assert client.post("/auth/login", json=ADMIN).status_code == 200
    for _ in range(limitador_login.max_intentos - 1):
        assert client.post("/auth/login", json={**ADMIN, "contrasena": "mala"}).status_code == 401
    limitador_login.reiniciar()


def test_la_api_exige_auth_secret_y_contrasena_de_admin():
    entorno = {k: v for k, v in os.environ.items() if k not in ("AUTH_SECRET", "ADMIN_PASSWORD")}
    entorno["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/vacia.db"
    raiz = Path(__file__).resolve().parent.parent

    def arrancar(extra):
        return subprocess.run(
            [sys.executable, "-c", "import app.main"], cwd=raiz, env={**entorno, **extra},
            capture_output=True, text=True,
        )

    sin_secreto = arrancar({"ADMIN_PASSWORD": "x" * 10})
    assert sin_secreto.returncode != 0 and "AUTH_SECRET" in sin_secreto.stderr
    sin_clave = arrancar({"AUTH_SECRET": "s"})
    assert sin_clave.returncode != 0 and "ADMIN_PASSWORD" in sin_clave.stderr
    assert arrancar({"AUTH_SECRET": "s", "ADMIN_PASSWORD": "x" * 10}).returncode == 0
