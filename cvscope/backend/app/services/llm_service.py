"""
Servicio de integración con el LLM (Gemini 2.5 Flash vía endpoint
compatible con OpenAI). Aquí va la lógica de prompting para evaluar
candidatos frente a vacantes con explicabilidad.

Variables de entorno esperadas (definir en .env):
  OPENAI_API_KEY   -> tu API key de Google AI Studio
  OPENAI_BASE_URL  -> https://generativelanguage.googleapis.com/v1beta/openai/
  LLM_MODEL        -> gemini-2.5-flash
"""

import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")


def evaluar_compatibilidad(perfil_candidato: str, requisitos_vacante: str) -> dict:
    """
    Compara un perfil de candidato contra los requisitos de una vacante.

    Returns:
      dict con: puntaje (0-100), cumple (list[str]), no_cumple (list[str]),
      explicacion (str)
    """
    # TODO: diseñar el prompt para que el LLM devuelva un JSON estructurado
    # con el puntaje y la explicación, no solo texto libre.
    raise NotImplementedError("Pendiente de implementar")
