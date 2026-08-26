from fastapi import APIRouter

router = APIRouter()


@router.post("/categorizar")
def categorizar_candidato():
    """
    Paso 1: dado el texto de una hoja de vida, el LLM determina a qué
    rol/categoría profesional pertenece el candidato (Full Stack, RRHH,
    Ventas, Marketing Digital, etc.).
    (Pendiente: implementar llamada a app.services.llm_service)
    """
    return {"mensaje": "Categorización pendiente de implementar"}


@router.post("/evaluar")
def evaluar_candidato():
    """
    Paso 2: dado un candidato ya categorizado en un rol, evalúa si cumple
    los requisitos mínimos de ese rol (apto/no apto) y genera una
    explicación de qué requisitos cumple y cuáles no.
    (Pendiente: implementar llamada a app.services.llm_service)
    """
    return {"mensaje": "Evaluación pendiente de implementar"}


@router.get("/ranking/{rol_id}")
def ranking_por_rol(rol_id: int):
    """
    Paso 3: entre los candidatos aptos de un mismo rol, genera un ranking
    ordenado de mejor a peor ajuste con el perfil buscado.
    (Pendiente: implementar)
    """
    return {"mensaje": f"Ranking del rol {rol_id} pendiente de implementar"}
