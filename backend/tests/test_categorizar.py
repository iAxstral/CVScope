import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import ia_services
from app.services.ia_services import ClasificadorNoDisponible

client = TestClient(app)

CV = "Desarrollador con 4 años de experiencia en React, FastAPI y PostgreSQL."


class _EmbeddingsFalsos:
    def __init__(self):
        self.recibidos = []

    def encode(self, textos):
        self.recibidos.extend(textos)
        return np.zeros((len(textos), 3))


class _ClasificadorFalso:
    def predict(self, vectores):
        return np.array(["fullstack"] * len(vectores))


@pytest.fixture
def clasificador_simulado(monkeypatch):
    embeddings = _EmbeddingsFalsos()
    monkeypatch.setattr(ia_services, "_cargar_modelos", lambda: (embeddings, _ClasificadorFalso()))
    return embeddings


@pytest.fixture
def clasificador_no_disponible(monkeypatch):
    def fallar():
        raise ClasificadorNoDisponible("No se pudo cargar el clasificador de rol: sin modelo")

    monkeypatch.setattr(ia_services, "_cargar_modelos", fallar)


def test_categorizar_texto_con_el_clasificador_simulado(clasificador_simulado):
    r = client.post("/preseleccion/categorizar", json={"hoja_de_vida_texto": CV})
    assert r.status_code == 200
    assert r.json() == {"candidato_id": None, "rol_predicho": "fullstack"}
    assert clasificador_simulado.recibidos == [CV]


def test_categorizar_un_candidato_registrado_usa_su_texto_guardado(clasificador_simulado):
    creado = client.post("/candidatos/", json={
        "nombre": "Ana Prueba", "email": "ana.categorizar@example.com", "hoja_de_vida_texto": CV,
    })
    assert creado.status_code == 201
    candidato_id = creado.json()["id"]

    r = client.post("/preseleccion/categorizar", json={"candidato_id": candidato_id})
    assert r.status_code == 200
    assert r.json() == {"candidato_id": candidato_id, "rol_predicho": "fullstack"}
    assert clasificador_simulado.recibidos == [CV]


def test_categorizar_responde_503_si_el_clasificador_no_esta_disponible(clasificador_no_disponible):
    r = client.post("/preseleccion/categorizar", json={"hoja_de_vida_texto": CV})
    assert r.status_code == 503
    assert "clasificador de rol" in r.json()["detail"]


def test_evaluar_sin_rol_tambien_responde_503_sin_clasificador(clasificador_no_disponible):
    r = client.post("/preseleccion/evaluar", json={"hoja_de_vida_texto": CV})
    assert r.status_code == 503


def test_categorizar_sin_texto_ni_candidato_es_400(clasificador_simulado):
    assert client.post("/preseleccion/categorizar", json={}).status_code == 400
    assert client.post("/preseleccion/categorizar", json={"candidato_id": 999999}).status_code == 404
