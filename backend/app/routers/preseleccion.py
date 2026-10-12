import os
from typing import Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.models.store import candidato_store, rol_store
from app.schemas.preseleccion import (
    DetalleHojaDeVida,
    EvaluacionResponse,
    EvaluarRequest,
    MotoresResponse,
    RankingResponse,
)
from app.services.evaluador_requisitos import evaluar_cv
from app.services.extractor_texto import (
    TAMANO_MAXIMO,
    ArchivoIlegible,
    FormatoNoSoportado,
    extraer_texto,
)
from app.services.hojas_de_vida import buscar, pool_del_rol
from app.services.red_competitiva import servicio as servicio_red
from app.services.red_competitiva.caracteristicas import extraer
from app.services.red_competitiva.competitiva import podio
from app.services.ia_services import ClasificadorNoDisponible, categorizar_rol
from app.services.llm_service import (
    MODELO_POR_DEFECTO,
    LLMNoDisponible,
    evaluar_compatibilidad,
    llm_disponible,
)

router = APIRouter()


class CategorizarRequest(BaseModel):
    candidato_id: int | None = Field(
        default=None,
        description="Id de un candidato ya registrado; si se envía, se usa su hoja_de_vida_texto guardada.",
    )
    hoja_de_vida_texto: str | None = Field(
        default=None,
        min_length=20,
        description="Texto plano de una hoja de vida a categorizar directamente, sin necesidad de un candidato registrado.",
    )


class CategorizarResponse(BaseModel):
    candidato_id: int | None = None
    rol_predicho: str = Field(..., examples=["fullstack"])


def _texto_de(candidato_id: int | None, hoja_de_vida_texto: str | None) -> str:
    if candidato_id is None and hoja_de_vida_texto is None:
        raise HTTPException(
            status_code=400,
            detail="Debe enviarse candidato_id o hoja_de_vida_texto",
        )
    if candidato_id is not None:
        candidato = candidato_store.get(candidato_id)
        if candidato is None:
            raise HTTPException(status_code=404, detail=f"Candidato {candidato_id} no encontrado")
        return candidato["hoja_de_vida_texto"]
    return hoja_de_vida_texto


def _categorizar(texto: str) -> str:
    try:
        return categorizar_rol(texto)
    except ClasificadorNoDisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _evaluar(texto: str, rol: dict, motor: str) -> dict:
    requisitos, umbral = rol["requisitos"], rol["umbral_apto"]
    if motor == "llm":
        try:
            return evaluar_compatibilidad(texto, requisitos, umbral)
        except LLMNoDisponible as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return evaluar_cv(texto, requisitos, umbral)


def _rol_o_404(rol_id: int) -> dict:
    rol = rol_store.get(rol_id)
    if rol is None:
        raise HTTPException(status_code=404, detail=f"Rol {rol_id} no encontrado")
    return rol


@router.post("/categorizar", response_model=CategorizarResponse)
def categorizar_candidato(data: CategorizarRequest):
    """
    Paso 1: dado el texto de una hoja de vida (directo o de un candidato ya
    registrado), el clasificador determina a qué rol/categoría profesional
    pertenece (fullstack, rrhh, ventas, marketing, etc.).
    """
    texto = _texto_de(data.candidato_id, data.hoja_de_vida_texto)
    return CategorizarResponse(candidato_id=data.candidato_id, rol_predicho=_categorizar(texto))


@router.post("/evaluar", response_model=EvaluacionResponse)
def evaluar_candidato(data: EvaluarRequest):
    """
    Paso 2 (selección): evalúa si una hoja de vida cumple los requisitos
    mínimos de un rol (apto/no apto) y explica qué requisitos cumple y cuáles
    no, citando el fragmento del CV que sustenta cada veredicto.

    Si no se indica el rol, se usa el del candidato registrado o el que
    prediga el clasificador (Paso 1).
    """
    texto = _texto_de(data.candidato_id, data.hoja_de_vida_texto)

    rol_id = data.rol_id
    if rol_id is None and data.candidato_id is not None:
        rol_id = candidato_store.get(data.candidato_id)["rol_id"]

    rol_predicho = None
    if rol_id is None:
        rol_predicho = _categorizar(texto)
        rol = rol_store.get_by_clave(rol_predicho)
        if rol is None:
            raise HTTPException(
                status_code=422,
                detail=f"El clasificador predijo '{rol_predicho}', que no corresponde a ningún rol registrado",
            )
    else:
        rol = _rol_o_404(rol_id)

    resultado = _evaluar(texto, rol, data.motor)
    lvq = servicio_red.clasificar_lvq(extraer(texto, rol["requisitos"]))

    if data.candidato_id is not None:
        candidato_store.update(
            data.candidato_id,
            rol_id=rol["id"],
            rol_nombre=rol["nombre"],
            estado=resultado["estado"],
            score=resultado["score"],
            requisitos_cumplidos=resultado["requisitos_cumplidos"],
            requisitos_faltantes=resultado["requisitos_faltantes"],
            explicacion=resultado["explicacion"],
        )

    return EvaluacionResponse(
        candidato_id=data.candidato_id,
        motor=data.motor,
        rol_id=rol["id"],
        rol_nombre=rol["nombre"],
        rol_predicho=rol_predicho,
        veredicto_lvq=lvq["veredicto"] if lvq else None,
        margen_lvq=round(lvq["margen"], 3) if lvq else None,
        **resultado,
    )


@router.get("/ranking/{rol_id}", response_model=RankingResponse)
def ranking_por_rol(
    rol_id: int,
    top: int = Query(default=5, ge=1, le=50),
    metodo: Literal["red", "palabras_clave"] = Query(default="red"),
):
    """
    Paso 3 (ranking): evalúa todas las hojas de vida del rol (dataset de
    ranking + candidatos registrados) y devuelve las `top` mejores.

    - metodo=red (por defecto): las ordena la red neuronal competitiva, igual
      que el podio de la página "Red competitiva".
    - metodo=palabras_clave: solo las aptas, ordenadas por el puntaje del
      evaluador por palabras clave.

    `top_otro_metodo` trae el top del otro método para compararlos.
    """
    rol = _rol_o_404(rol_id)
    pool = pool_del_rol(rol)

    evaluados = []
    for cv in pool:
        r = evaluar_cv(cv["texto"], rol["requisitos"], rol["umbral_apto"])
        evaluados.append({
            "id": cv["id"],
            "nombre": cv["nombre"],
            "email": cv["email"],
            "fuente": cv["fuente"],
            "posicion_referencia": cv["posicion_referencia"],
            "score": r["score"],
            "estado": r["estado"],
            "anios_experiencia": r["anios_experiencia"],
            "requisitos_cumplidos": r["requisitos_cumplidos"],
            "requisitos_faltantes": r["requisitos_faltantes"],
        })

    aptos = sorted(
        (e for e in evaluados if e["estado"] == "apto"),
        key=lambda e: (-e["score"], e["id"]),
    )
    top_palabras = aptos[:top]

    aviso = None
    top_red = None
    if evaluados:
        try:
            fuerzas = [servicio_red.preparar(cv, rol["requisitos"])["fuerza"] for cv in pool]
            for e, f in zip(evaluados, fuerzas):
                e["fuerza"] = round(f, 3)
            top_red = [evaluados[i] for i in podio(fuerzas, top)]
        except servicio_red.ModeloNoDisponible as exc:
            aviso = f"La red competitiva no está disponible ({exc}); se ordenó por palabras clave."

    if metodo == "red" and top_red is not None:
        seleccion, otro = top_red, top_palabras
    else:
        metodo = "palabras_clave"
        seleccion, otro = top_palabras, top_red or []

    coincidencias = None
    if any(e["fuente"] == "dataset" for e in evaluados):
        coincidencias = sum(
            1 for e in seleccion if e["posicion_referencia"] is not None and e["posicion_referencia"] <= top
        )

    return RankingResponse(
        rol_id=rol["id"],
        rol_nombre=rol["nombre"],
        requisitos=rol["requisitos"],
        metodo=metodo,
        total_evaluados=len(evaluados),
        total_aptos=len(aptos),
        top=seleccion,
        top_otro_metodo=[e["id"] for e in otro],
        coincidencias_referencia=coincidencias,
        aviso=aviso,
    )


@router.get("/hojas-de-vida/{cv_id}", response_model=DetalleHojaDeVida)
def detalle_hoja_de_vida(
    cv_id: str,
    rol_id: int | None = Query(default=None),
    motor: Literal["palabras_clave", "llm"] = Query(default="palabras_clave"),
):
    """
    Detalle explicable de una hoja de vida (del dataset o de un candidato
    registrado): veredicto por requisito con su evidencia y, si viene de un
    dataset, las etiquetas reales para compararlas.
    """
    cv = buscar(cv_id)
    if cv is None:
        raise HTTPException(status_code=404, detail=f"Hoja de vida {cv_id} no encontrada")
    rol = _rol_o_404(rol_id) if rol_id else cv["rol"]

    if rol is None:
        raise HTTPException(status_code=400, detail="La hoja de vida no tiene un rol asignado; envíe rol_id")

    return DetalleHojaDeVida(
        id=cv["id"],
        nombre=cv["nombre"],
        email=cv["email"],
        fuente=cv["fuente"],
        hoja_de_vida_texto=cv["texto"],
        rol_id=rol["id"],
        rol_nombre=rol["nombre"],
        referencia=cv["referencia"],
        motor=motor,
        **_evaluar(cv["texto"], rol, motor),
    )


@router.get("/motores", response_model=MotoresResponse)
def motores_disponibles():
    """Motores de evaluación disponibles (Gemini solo si hay API key)."""
    return MotoresResponse(llm=llm_disponible(), modelo_llm=os.getenv("LLM_MODEL", MODELO_POR_DEFECTO))


class TextoExtraido(BaseModel):
    nombre_archivo: str
    caracteres: int
    hoja_de_vida_texto: str


@router.post("/extraer-texto", response_model=TextoExtraido)
async def extraer_texto_de_archivo(archivo: UploadFile = File(...)):
    """Extrae el texto plano de una hoja de vida en PDF, DOCX o TXT."""
    # Se lee por partes y se corta apenas supera el límite, para no cargar en
    # memoria un archivo enorme antes de rechazarlo.
    partes, leido = [], 0
    while parte := await archivo.read(64 * 1024):
        leido += len(parte)
        if leido > TAMANO_MAXIMO:
            raise HTTPException(status_code=413, detail="El archivo supera el tamaño máximo de 5 MB")
        partes.append(parte)
    contenido = b"".join(partes)
    try:
        texto = extraer_texto(archivo.filename or "", contenido)
    except FormatoNoSoportado as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ArchivoIlegible as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TextoExtraido(
        nombre_archivo=archivo.filename or "", caracteres=len(texto), hoja_de_vida_texto=texto
    )
