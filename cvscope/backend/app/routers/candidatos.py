from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def listar_candidatos():
    """Lista todos los candidatos registrados. (Pendiente: conectar con base de datos)"""
    return {"candidatos": []}


@router.post("/")
def crear_candidato():
    """Registra un nuevo candidato (hoja de vida / perfil). (Pendiente: implementar)"""
    return {"mensaje": "Candidato registrado (pendiente de implementar)"}
