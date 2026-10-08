import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.red_competitiva.lvq import CapaLVQ

client = TestClient(app)


def _datos(rng, n=200):
    """Dos clases separadas en la primera dimensión, con ruido en el resto."""
    y = rng.integers(0, 2, n)
    x = rng.normal(0, 0.3, (n, 6))
    x[:, 0] += y * 2.0
    return x.astype(np.float32), y


def test_la_lvq_aprende_a_separar_dos_clases():
    rng = np.random.default_rng(0)
    x, y = _datos(rng)
    capa = CapaLVQ.entrenar(x, y, prototipos_por_clase=2, epocas=20, alfa_inicial=0.1)
    xt, yt = _datos(rng)
    assert np.mean(capa.predecir(xt) == yt) > 0.95


def test_regla_de_kohonen_acerca_y_aleja_a_la_ganadora():
    rng = np.random.default_rng(1)
    x, y = _datos(rng, 50)
    antes = CapaLVQ.entrenar(x, y, prototipos_por_clase=1, epocas=0)
    despues = CapaLVQ.entrenar(x, y, prototipos_por_clase=1, epocas=10, alfa_inicial=0.1)
    # Los prototipos se movieron hacia el centro de su clase
    for clase in (0, 1):
        centro = x[y == clase].mean(axis=0)
        k = int(np.flatnonzero(despues.clases == clase)[0])
        assert np.linalg.norm(despues.prototipos[k] - centro) < np.linalg.norm(antes.prototipos[k] - centro)


def test_competir_devuelve_ganadora_y_margen():
    capa = CapaLVQ(np.array([[0.0, 0.0], [1.0, 1.0]]), np.array([0, 1]), np.ones(2))
    r = capa.competir(np.array([0.9, 0.9]))
    assert r["neurona_ganadora"] == 1 and r["veredicto"] == "apto"
    assert 0 < r["margen"] <= 1
    assert capa.competir(np.array([0.5, 0.5]))["margen"] == pytest.approx(0, abs=1e-6)


def test_guardar_y_cargar(tmp_path):
    capa = CapaLVQ(np.ones((2, 3)), np.array([0, 1]), np.full(3, 2.0))
    capa.guardar(tmp_path / "lvq.npz", exactitud_prueba=0.9)
    cargada, meta = CapaLVQ.cargar(tmp_path / "lvq.npz")
    np.testing.assert_array_equal(cargada.pesos_rasgos, capa.pesos_rasgos)
    assert meta["exactitud_prueba"] == pytest.approx(0.9)


def test_api_entrega_el_veredicto_de_la_lvq():
    r = client.post("/preseleccion/evaluar", json={
        "hoja_de_vida_texto": "Perfil: 8 años de experiencia. TypeScript, React, NestJS y PostgreSQL.",
        "rol_id": 1,
    }).json()
    assert r["veredicto_lvq"] == "apto" and r["margen_lvq"] > 0
    torneo = client.post("/competencia/torneo", json={"rol_id": 2}).json()
    assert {p["veredicto_lvq"] for p in torneo["participantes"]} <= {"apto", "no_apto"}
    modelo = client.get("/competencia/modelo").json()
    assert len(modelo["lvq"]["prototipos"]) == 4
