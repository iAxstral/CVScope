from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

CV_DOS_DE_TRES = "Perfil: 5 años de experiencia. Ventas B2B a empresas y negociación de contratos."


def _crear(umbral, clave):
    r = client.post("/roles/", json={
        "nombre": f"Ventas umbral {umbral}",
        "clave": clave,
        "requisitos": ["Experiencia en ventas B2B/B2C", "Manejo de CRM", "Negociación"],
        "umbral_apto": umbral,
    })
    assert r.status_code == 201
    return r.json()


def test_el_umbral_del_rol_decide_si_es_apto():
    estricto = _crear(1.0, "ventas-estricto")
    flexible = _crear(0.5, "ventas-flexible")
    assert estricto["umbral_apto"] == 1.0

    def estado(rol):
        return client.post("/preseleccion/evaluar", json={
            "hoja_de_vida_texto": CV_DOS_DE_TRES, "rol_id": rol["id"],
        }).json()["estado"]

    assert estado(estricto) == "no_apto"  # cumple 2 de 3 y exige 3 de 3
    assert estado(flexible) == "apto"     # cumple 2 de 3 y exige la mitad


def test_validaciones_al_crear_roles():
    assert client.post("/roles/", json={"nombre": "Repetido", "clave": "fullstack", "requisitos": ["X"]}).status_code == 409
    assert client.post("/roles/", json={"nombre": "Vacío", "requisitos": ["  "]}).status_code == 422
    assert client.post("/roles/", json={"nombre": "Umbral", "requisitos": ["X"], "umbral_apto": 1.5}).status_code == 422
