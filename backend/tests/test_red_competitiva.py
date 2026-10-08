import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.red_competitiva.caracteristicas import DIM_ENTRADA, extraer, tokenizar
from app.services.red_competitiva.modelo import RedCompetitiva, _sigmoide
from app.services.red_competitiva.torneo import clasificar, jugar_torneo

client = TestClient(app)


def _por_fuerza(a, b):
    return 1.0 if a["f"] > b["f"] else 0.0


# ---------------------------------------------------------------- torneo

@pytest.mark.parametrize("n", [2, 3, 5, 8, 15])
def test_torneo_gana_el_mas_fuerte_con_n_menos_uno_duelos(n):
    participantes = [{"id": str(i), "f": (i * 7) % n} for i in range(n)]
    resultado = jugar_torneo(participantes, _por_fuerza, semilla=3)
    assert resultado["campeon"]["f"] == n - 1
    # En eliminación directa siempre hay n - 1 duelos (uno por eliminado)
    assert resultado["total_duelos"] == n - 1
    assert resultado["rondas"][-1]["nombre"] == "Final"


def test_torneo_da_byes_solo_en_la_primera_ronda():
    participantes = [{"id": str(i), "f": i} for i in range(5)]
    rondas = jugar_torneo(participantes, _por_fuerza)["rondas"]
    assert rondas[0]["pases"] == ["0", "1", "2"]
    assert all(not r["pases"] for r in rondas[1:])


def test_clasificar_devuelve_el_top_en_orden():
    participantes = [{"id": str(i), "f": f} for i, f in enumerate([4, 9, 1, 7, 5, 8])]
    podio = clasificar(participantes, _por_fuerza, top=3)
    assert [p["f"] for p in podio] == [9, 8, 7]


def test_torneo_vacio_y_de_uno():
    assert jugar_torneo([], _por_fuerza)["campeon"] is None
    unico = jugar_torneo([{"id": "x", "f": 1}], _por_fuerza)
    assert unico["campeon"]["id"] == "x" and unico["total_duelos"] == 0


# ----------------------------------------------------------------- modelo

def test_probabilidad_es_antisimetrica():
    rng = np.random.default_rng(0)
    red = RedCompetitiva(10, semilla=1)
    a, b = rng.normal(size=(4, 10)), rng.normal(size=(4, 10))
    np.testing.assert_allclose(red.probabilidad(a, b) + red.probabilidad(b, a), 1.0, atol=1e-6)
    np.testing.assert_allclose(red.probabilidad(a, a), 0.5, atol=1e-6)


def test_gradiente_coincide_con_diferencias_finitas():
    rng = np.random.default_rng(1)
    red = RedCompetitiva(6, (5, 4), semilla=3)
    red.pesos = [w.astype(np.float64) for w in red.pesos]
    red.sesgos = [b.astype(np.float64) for b in red.sesgos]
    xa, xb = rng.normal(size=(7, 6)), rng.normal(size=(7, 6))
    y = rng.integers(0, 2, 7).astype(float)

    def perdida():
        p = _sigmoide(red.puntaje(xa) - red.puntaje(xb))
        return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

    s_a, act_a = red._adelante(xa)
    s_b, act_b = red._adelante(xb)
    g = ((_sigmoide(s_a[:, 0] - s_b[:, 0]) - y) / 7)[:, None]
    analitico = red._atras(act_a, g)[0][0] + red._atras(act_b, -g)[0][0]

    numerico = np.zeros_like(analitico)
    eps = 1e-6
    for idx in np.ndindex(analitico.shape):
        red.pesos[0][idx] += eps
        arriba = perdida()
        red.pesos[0][idx] -= 2 * eps
        abajo = perdida()
        red.pesos[0][idx] += eps
        numerico[idx] = (arriba - abajo) / (2 * eps)
    np.testing.assert_allclose(analitico, numerico, rtol=1e-4, atol=1e-8)


def test_la_red_aprende_a_ordenar_por_una_variable():
    rng = np.random.default_rng(2)
    x = rng.normal(size=(200, 5)).astype(np.float32)
    i, j = rng.integers(0, 200, (2, 2000))
    y = (x[i, 0] > x[j, 0]).astype(np.float32)
    red = RedCompetitiva(5, (8,), semilla=0)
    for _ in range(300):
        red.paso(x[i], x[j], y, tasa=1e-2)
    assert np.mean((red.probabilidad(x[i], x[j]) >= 0.5) == y) > 0.95


def test_guardar_y_cargar(tmp_path):
    red = RedCompetitiva(4, (3,), semilla=5)
    ruta = tmp_path / "red.npz"
    red.guardar(ruta, precision=0.8)
    cargada, meta = RedCompetitiva.cargar(ruta)
    x = np.ones((2, 4), dtype=np.float32)
    np.testing.assert_allclose(cargada.puntaje(x), red.puntaje(x))
    assert meta["precision"] == pytest.approx(0.8)


# --------------------------------------------------------- características

def test_caracteristicas_tienen_tamano_fijo_y_rasgos():
    texto = "Perfil: 6 años de experiencia. TypeScript, React, NestJS y PostgreSQL."
    x = extraer(texto, ["JavaScript/TypeScript", "React o similar"])
    assert x.shape == (DIM_ENTRADA,)
    assert x[0] == pytest.approx(1.0)  # cumple los 2 requisitos
    assert x[1] == pytest.approx(0.5)  # 6 de 12 años
    assert tokenizar("Node.js y C++") == ["node.js", "c++"]


# -------------------------------------------------------------------- API

def test_api_torneo_por_defecto():
    r = client.post("/competencia/torneo", json={"rol_id": 1})
    assert r.status_code == 200
    datos = r.json()
    assert len(datos["podio"]) == 5
    assert datos["total_duelos"] == len(datos["participantes"]) - 1
    assert datos["campeon"]["id"] == datos["podio"][0]["id"]


def test_api_comparar_es_consistente_al_invertir():
    a, b = {"cv_id": "rk-ventas-01"}, {"cv_id": "rk-ventas-12"}
    ab = client.post("/competencia/comparar", json={"rol_id": 3, "a": a, "b": b}).json()
    ba = client.post("/competencia/comparar", json={"rol_id": 3, "a": b, "b": a}).json()
    assert ab["prob_a"] + ba["prob_a"] == pytest.approx(1.0, abs=1e-6)
    assert {ab["ganador"], ba["ganador"]} == {"a", "b"}


def test_api_errores():
    assert client.post("/competencia/torneo", json={"rol_id": 99}).status_code == 404
    assert client.post("/competencia/torneo", json={"rol_id": 1, "cv_ids": ["rk-fullstack-01"]}).status_code == 400
    assert client.post("/competencia/comparar", json={"rol_id": 1, "a": {}, "b": {}}).status_code == 400
