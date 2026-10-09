from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.db import engine
from app.main import app
from app.models.store import CandidatoStore, RolStore

client = TestClient(app)


def test_tablas_y_roles_iniciales():
    tablas = set(inspect(engine).get_table_names())
    assert {"roles", "candidatos"} <= tablas
    claves = {r["clave"] for r in RolStore().list_all()}
    assert {"fullstack", "rrhh", "ventas", "marketing"} <= claves


def test_candidato_y_su_evaluacion_quedan_guardados():
    creado = client.post("/candidatos/", json={
        "nombre": "Persona Persistente",
        "email": "p@cvscope.co",
        "hoja_de_vida_texto": "Perfil: 4 años de experiencia. Ventas B2B con HubSpot y negociación.",
        "rol_id": 3,
    }).json()
    client.post("/preseleccion/evaluar", json={"candidato_id": creado["id"]})

    # Un store nuevo abre sesiones nuevas: lo que lee viene de la base de datos
    guardado = CandidatoStore().get(creado["id"])
    assert guardado["estado"] == "apto"
    assert guardado["rol_nombre"] == "Ejecutivo de Ventas"
    assert guardado["requisitos_cumplidos"] == ["Experiencia en ventas B2B/B2C", "Manejo de CRM", "Negociación"]
    assert creado["id"] in [c["id"] for c in CandidatoStore().list_by_rol(3)]
