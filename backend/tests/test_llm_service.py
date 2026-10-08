import json
from types import SimpleNamespace

import pytest

from app.services import llm_service

REQUISITOS = ["JavaScript/TypeScript", "React o similar", "Node.js o backend equivalente"]
CV = (
    "Laura Gómez. Ingeniera en Cali. Perfil: 7 años de experiencia. "
    "Maquetación de interfaces dinámicas basadas en componentes reutilizables. "
    "Desarrollo de módulos en TypeScript con pruebas unitarias en Jest."
)


class ClienteFalso:
    def __init__(self, contenido):
        self.contenido = contenido
        self.mensajes = None
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._crear))

    def _crear(self, **kwargs):
        self.mensajes = kwargs["messages"]
        mensaje = SimpleNamespace(content=self.contenido)
        return SimpleNamespace(choices=[SimpleNamespace(message=mensaje)])


def _usar(monkeypatch, respuesta):
    cliente = ClienteFalso(respuesta if isinstance(respuesta, str) else json.dumps(respuesta))
    monkeypatch.setattr(llm_service, "_cliente", lambda: cliente)
    return cliente


def test_respuesta_valida_con_misma_estructura_que_el_evaluador(monkeypatch):
    _usar(monkeypatch, {"evaluacion": [
        {"requisito": "JavaScript/TypeScript", "cumple": True,
         "evidencia": "módulos en TypeScript con pruebas unitarias", "nota": "Usa TypeScript."},
        {"requisito": "React o similar", "cumple": True,
         "evidencia": "interfaces dinámicas basadas en componentes reutilizables", "nota": "Equivale a React."},
        {"requisito": "Node.js o backend equivalente", "cumple": False, "evidencia": None, "nota": "No menciona backend."},
    ]})
    r = llm_service.evaluar_compatibilidad(CV, REQUISITOS)
    assert set(r) == {"score", "estado", "anios_experiencia", "evaluacion",
                      "requisitos_cumplidos", "requisitos_faltantes", "explicacion"}
    assert r["requisitos_cumplidos"] == ["JavaScript/TypeScript", "React o similar"]
    assert r["estado"] == "apto" and r["anios_experiencia"] == 7


def test_rechaza_evidencia_que_no_esta_en_el_cv(monkeypatch):
    _usar(monkeypatch, {"evaluacion": [
        {"requisito": "Node.js o backend equivalente", "cumple": True,
         "evidencia": "5 años con Node.js y Express", "nota": "Inventado."},
    ]})
    r = llm_service.evaluar_compatibilidad(CV, REQUISITOS)
    item = next(e for e in r["evaluacion"] if e["requisito"].startswith("Node"))
    assert item["cumple"] is False and "no citó evidencia" in item["nota"]


def test_no_envia_datos_personales(monkeypatch):
    cliente = _usar(monkeypatch, {"evaluacion": []})
    llm_service.evaluar_compatibilidad(CV, REQUISITOS)
    enviado = cliente.mensajes[-1]["content"]
    assert "Laura" not in enviado and "Cali" not in enviado and "Ingeniera" not in enviado


def test_acepta_json_envuelto_en_bloque_de_codigo(monkeypatch):
    _usar(monkeypatch, '```json\n{"evaluacion": []}\n```')
    r = llm_service.evaluar_compatibilidad(CV, REQUISITOS)
    assert r["requisitos_faltantes"] == REQUISITOS


def test_json_invalido_es_error_controlado(monkeypatch):
    _usar(monkeypatch, "esto no es json")
    with pytest.raises(llm_service.LLMNoDisponible):
        llm_service.evaluar_compatibilidad(CV, REQUISITOS)


def test_sin_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert llm_service.llm_disponible() is False
    with pytest.raises(llm_service.LLMNoDisponible):
        llm_service.evaluar_compatibilidad(CV, REQUISITOS)
