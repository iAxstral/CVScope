from fastapi import APIRouter, HTTPException

from app.models.store import rol_store
from app.schemas.competencia import (
    CompararRequest,
    CompararResponse,
    HojaDeVidaEntrada,
    ModeloInfo,
    TorneoRequest,
    TorneoResponse,
)
from app.services.hojas_de_vida import buscar, pool_del_rol
from app.services.red_competitiva import servicio
from app.services.red_competitiva.caracteristicas import DIM_ENTRADA
from app.services.red_competitiva.modelo import CAPAS_OCULTAS

router = APIRouter()


def _rol_o_404(rol_id: int) -> dict:
    rol = rol_store.get(rol_id)
    if rol is None:
        raise HTTPException(status_code=404, detail=f"Rol {rol_id} no encontrado")
    return rol


def _modelo():
    try:
        return servicio.cargar_modelo()
    except servicio.ModeloNoDisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _resolver(entrada: HojaDeVidaEntrada, etiqueta: str) -> dict:
    if entrada.cv_id:
        cv = buscar(entrada.cv_id)
        if cv is None:
            raise HTTPException(status_code=404, detail=f"Hoja de vida {entrada.cv_id} no encontrada")
        posicion = (cv["referencia"] or {}).get("posicion_referencia")
        return {**cv, "posicion_referencia": posicion}
    if entrada.hoja_de_vida_texto:
        return {
            "id": f"texto-{etiqueta}",
            "nombre": entrada.nombre or f"Hoja de vida {etiqueta.upper()}",
            "texto": entrada.hoja_de_vida_texto,
            "fuente": "texto",
            "posicion_referencia": None,
        }
    raise HTTPException(
        status_code=400, detail=f"La hoja de vida {etiqueta.upper()} necesita cv_id o hoja_de_vida_texto"
    )


@router.post("/comparar", response_model=CompararResponse)
def comparar(data: CompararRequest):
    """
    Duelo entre dos hojas de vida: la red estima la probabilidad de que A sea
    mejor que B para el rol y declara un ganador.
    """
    _modelo()
    rol = _rol_o_404(data.rol_id)
    a = servicio.preparar(_resolver(data.a, "a"), rol["requisitos"])
    b = servicio.preparar(_resolver(data.b, "b"), rol["requisitos"])
    prob_a = servicio.comparar(a, b)
    return CompararResponse(
        rol_id=rol["id"],
        rol_nombre=rol["nombre"],
        a=a,
        b=b,
        prob_a=prob_a,
        ganador="a" if prob_a >= 0.5 else "b",
        explicacion=servicio.explicar_duelo(a, b, prob_a),
    )


@router.post("/torneo", response_model=TorneoResponse)
def torneo(data: TorneoRequest):
    """
    Torneo de eliminación directa: las hojas de vida se enfrentan de a pares,
    la mejor de cada duelo avanza y se obtiene un campeón. El podio (top N)
    se arma con torneos sucesivos retirando al campeón de cada uno.
    """
    _modelo()
    rol = _rol_o_404(data.rol_id)

    if data.cv_ids:
        cvs = []
        for cv_id in dict.fromkeys(data.cv_ids):
            cv = buscar(cv_id)
            if cv is None:
                raise HTTPException(status_code=404, detail=f"Hoja de vida {cv_id} no encontrada")
            cvs.append({**cv, "posicion_referencia": (cv["referencia"] or {}).get("posicion_referencia")})
    else:
        cvs = pool_del_rol(rol)

    if len(cvs) < 2:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 2 hojas de vida para un torneo")

    resultado = servicio.torneo(cvs, rol["requisitos"], data.top, data.semilla)
    por_id = {p["id"]: p for p in resultado["participantes"]}
    for ronda in resultado["rondas"]:
        for duelo in ronda["duelos"]:
            duelo["explicacion"] = servicio.explicar_duelo(
                por_id[duelo["a"]], por_id[duelo["b"]], duelo["prob_a"]
            )

    coincidencias = None
    if any(p["posicion_referencia"] for p in resultado["participantes"]):
        coincidencias = sum(
            1 for p in resultado["podio"]
            if p["posicion_referencia"] is not None and p["posicion_referencia"] <= data.top
        )

    return TorneoResponse(
        rol_id=rol["id"],
        rol_nombre=rol["nombre"],
        participantes=sorted(resultado["participantes"], key=lambda p: -p["fuerza"]),
        rondas=resultado["rondas"],
        campeon=resultado["campeon"],
        podio=resultado["podio"],
        total_duelos=resultado["total_duelos"],
        coincidencias_referencia=coincidencias,
    )


@router.get("/modelo", response_model=ModeloInfo)
def info_modelo():
    """Arquitectura y métricas de prueba de la red competitiva entrenada."""
    _, meta = _modelo()
    capas = " -> ".join(str(n) for n in (DIM_ENTRADA, *CAPAS_OCULTAS, 1))
    return ModeloInfo(
        arquitectura=f"Red siamesa {capas} (ReLU); P(A>B) = sigmoide(s(A) - s(B))",
        dim_entrada=DIM_ENTRADA,
        metricas={k: float(v) for k, v in meta.items() if k not in ("dim_hash", "epocas")},
    )
