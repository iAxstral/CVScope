from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def listar_vacantes():
    """Lista todas las vacantes registradas. (Pendiente: conectar con base de datos)"""
    return {"vacantes": []}


@router.post("/")
def crear_vacante():
    """Crea una nueva vacante con su descripción y requisitos. (Pendiente: implementar)"""
    return {"mensaje": "Vacante creada (pendiente de implementar)"}
