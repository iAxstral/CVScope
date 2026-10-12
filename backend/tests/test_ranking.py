import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("rol_id", [1, 2, 3, 4])
def test_el_ranking_coincide_con_el_podio_de_la_red(rol_id):
    ranking = client.get(f"/preseleccion/ranking/{rol_id}").json()
    podio = client.post("/competencia/torneo", json={"rol_id": rol_id}).json()["podio"]
    assert ranking["metodo"] == "red"
    assert [c["id"] for c in ranking["top"]] == [c["id"] for c in podio]
    assert all(c["fuerza"] is not None for c in ranking["top"])


def test_ranking_por_palabras_clave_solo_trae_aptos():
    ranking = client.get("/preseleccion/ranking/1?metodo=palabras_clave").json()
    assert ranking["metodo"] == "palabras_clave"
    assert all(c["estado"] == "apto" for c in ranking["top"])
    scores = [c["score"] for c in ranking["top"]]
    assert scores == sorted(scores, reverse=True)
    assert len(ranking["top_otro_metodo"]) == 5
