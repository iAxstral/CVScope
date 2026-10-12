import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.evaluador_requisitos import evaluar_cv, quitar_evidencia, quitar_experiencia

client = TestClient(app)


@pytest.mark.parametrize("rol_id", [1, 2, 3, 4])
def test_la_explicacion_coincide_con_el_podio_y_cuadra_las_cuentas(rol_id):
    e = client.get(f"/competencia/explicar/{rol_id}").json()
    podio = client.post("/competencia/torneo", json={"rol_id": rol_id}).json()["podio"]
    assert [e["ganador"]["id"], e["segundo"]["id"]] == [podio[0]["id"], podio[1]["id"]]

    margen = e["ganador"]["fuerza"] - e["segundo"]["fuerza"]
    assert e["margen"]["fuerza"] == pytest.approx(margen)
    assert margen >= 0 and 0.5 <= e["margen"]["probabilidad_ganador"] <= 1

    # fuerza = suma de aportes de cada requisito + otras señales (para ambas)
    for lado in ("ganador", "segundo"):
        aportes = sum(r[lado]["contribucion"] for r in e["requisitos"])
        total = aportes + e[lado]["experiencia"] + e[lado]["otras_senales"]
        assert total == pytest.approx(e[lado]["fuerza"], abs=1e-4)
    # y por lo tanto el margen se reparte entre requisitos, experiencia y otras señales
    ventajas = (
        sum(r["ventaja"] for r in e["requisitos"]) + e["ventaja_experiencia"] + e["ventaja_otras_senales"]
    )
    assert ventajas == pytest.approx(margen, abs=1e-4)
    assert e["resumen"]


def test_un_requisito_sin_evidencia_no_aporta():
    e = client.get("/competencia/explicar/1").json()
    for r in e["requisitos"]:
        for lado in ("ganador", "segundo"):
            if not r[lado]["cumple"]:
                assert r[lado]["contribucion"] == 0 and r[lado]["evidencia"] is None


def test_explicar_un_rol_inexistente_es_404():
    assert client.get("/competencia/explicar/9999").status_code == 404


def test_quitar_evidencia_elimina_solo_ese_requisito():
    texto = "Desarrollador con 3 años de experiencia. Usa React y PostgreSQL; sin experiencia en Angular."
    requisitos = ["React o similar", "Bases de datos SQL/NoSQL"]
    sin_react = quitar_evidencia(texto, "React o similar")
    ev = {e["requisito"]: e["cumple"] for e in evaluar_cv(sin_react, requisitos)["evaluacion"]}
    assert ev == {"React o similar": False, "Bases de datos SQL/NoSQL": True}


def test_quitar_experiencia_borra_los_anios_declarados():
    sin = quitar_experiencia("Perfil con 5 años de experiencia en ventas.")
    assert "5" not in sin and "ventas" in sin
