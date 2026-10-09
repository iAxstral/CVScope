"""
Evaluador de requisitos con LLM (Gemini 2.5 Flash vía endpoint compatible
con OpenAI).

Devuelve exactamente la misma estructura que el evaluador por palabras clave
(app/services/evaluador_requisitos.py), así el frontend y el ranking no
cambian según el motor.

Garantías de explicabilidad y privacidad:
  - El CV se anonimiza antes de enviarlo (no salen datos personales).
  - El LLM debe citar textualmente la evidencia de cada requisito. Si la cita
    no aparece en el CV, el requisito se marca como NO cumplido: no se aceptan
    veredictos sin evidencia verificable (evita alucinaciones).
  - Puntaje y apto/no apto se calculan con la misma regla del evaluador base.

Variables de entorno (definir en backend/.env):
  OPENAI_API_KEY   -> API key de Google AI Studio
  OPENAI_BASE_URL  -> https://generativelanguage.googleapis.com/v1beta/openai/
  LLM_MODEL        -> gemini-2.5-flash
"""

import json
import os
import re

from app.services.anonimizador import anonimizar
from app.services.evaluador_requisitos import (
    UMBRAL_APTO,
    extraer_anios_experiencia,
    normalizar,
    resumir,
)

MODELO_POR_DEFECTO = "gemini-2.5-flash"
BASE_URL_POR_DEFECTO = "https://generativelanguage.googleapis.com/v1beta/openai/"


class LLMNoDisponible(RuntimeError):
    """No hay API key configurada o el servicio no respondió correctamente."""


PROMPT_SISTEMA = """Eres un analista de selección de personal. Evalúas si una hoja de vida
cumple cada requisito mínimo de un cargo. Reglas:
- Evalúa SOLO con lo que dice el texto; no supongas experiencia que no está escrita.
- Un requisito se cumple si el CV lo demuestra explícitamente o con una descripción
  equivalente (por ejemplo, "componentes reutilizables con Next.js" demuestra React).
- Para cada requisito cumplido copia en "evidencia" una cita LITERAL y breve del CV
  (máximo 200 caracteres) que lo demuestre. Si no se cumple, "evidencia" es null.
- "nota" explica en una frase, en español, por qué se cumple o no.
- Ignora por completo nombre, edad, género, ciudad u otros datos personales.
Responde únicamente con JSON con esta forma:
{"evaluacion": [{"requisito": str, "cumple": bool, "evidencia": str | null, "nota": str}]}"""


def _cliente():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("tu_api_key"):
        raise LLMNoDisponible(
            "No hay API key de Gemini configurada (OPENAI_API_KEY en backend/.env)"
        )
    from openai import OpenAI

    return OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL", BASE_URL_POR_DEFECTO))


def llm_disponible() -> bool:
    try:
        _cliente()
    except LLMNoDisponible:
        return False
    return True


def _mensajes(cv_texto: str, requisitos: list[str]) -> list[dict]:
    lista = "\n".join(f"- {r}" for r in requisitos)
    return [
        {"role": "system", "content": PROMPT_SISTEMA},
        {
            "role": "user",
            "content": f"Requisitos del cargo:\n{lista}\n\nHoja de vida:\n\"\"\"\n{cv_texto}\n\"\"\"",
        },
    ]


def _extraer_json(contenido: str) -> dict:
    # Algunos modelos envuelven el JSON en ```json ... ```
    limpio = re.sub(r"^```(?:json)?\s*|\s*```$", "", contenido.strip())
    return json.loads(limpio)


def _cita_verificable(evidencia: str | None, cv_texto: str) -> bool:
    if not evidencia:
        return False
    cita = re.sub(r"\s+", " ", normalizar(evidencia)).strip(" .…\"'")
    texto = re.sub(r"\s+", " ", normalizar(cv_texto))
    return len(cita) >= 3 and cita in texto


def _validar(respuesta: dict, requisitos: list[str], cv_texto: str) -> list[dict]:
    por_requisito = {
        item.get("requisito"): item
        for item in respuesta.get("evaluacion", [])
        if isinstance(item, dict)
    }
    evaluacion = []
    for requisito in requisitos:
        item = por_requisito.get(requisito, {})
        cumple = bool(item.get("cumple"))
        evidencia = item.get("evidencia") if cumple else None
        nota = str(item.get("nota") or "").strip() or "El modelo no explicó este requisito."
        if cumple and not _cita_verificable(evidencia, cv_texto):
            cumple, evidencia = False, None
            nota = "El LLM lo marcó como cumplido pero no citó evidencia literal del CV; no se acepta."
        elif not item:
            nota = "El LLM no evaluó este requisito."
        evaluacion.append({"requisito": requisito, "cumple": cumple, "evidencia": evidencia, "nota": nota})
    return evaluacion


def evaluar_compatibilidad(cv_texto: str, requisitos: list[str], umbral: float = UMBRAL_APTO) -> dict:
    """
    Evalúa una hoja de vida contra los requisitos de un rol usando el LLM.

    Returns:
      dict con: score (0-100), estado, anios_experiencia, evaluacion
      (list[{requisito, cumple, evidencia, nota}]), requisitos_cumplidos,
      requisitos_faltantes, explicacion
    """
    cliente = _cliente()
    texto = anonimizar(cv_texto)
    try:
        respuesta = cliente.chat.completions.create(
            model=os.getenv("LLM_MODEL", MODELO_POR_DEFECTO),
            messages=_mensajes(texto, requisitos),
            response_format={"type": "json_object"},
            temperature=0,
        )
        datos = _extraer_json(respuesta.choices[0].message.content or "")
    except LLMNoDisponible:
        raise
    except Exception as exc:  # red, cuota, JSON inválido...
        raise LLMNoDisponible(f"Gemini no devolvió una evaluación válida: {exc}") from exc

    resultado = resumir(_validar(datos, requisitos, texto), extraer_anios_experiencia(texto), umbral)
    resultado["explicacion"] = "Evaluado con Gemini. " + resultado["explicacion"]
    return resultado
