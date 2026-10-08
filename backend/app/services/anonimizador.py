"""
Anonimiza una hoja de vida antes de que la vea un modelo.

La red competitiva aprende de los n-gramas del texto y el LLM lee el CV
completo; si ven el nombre, la ciudad, la edad o el género del candidato
pueden aprender (o reproducir) sesgos que nada tienen que ver con el cargo.
Además, así no se envían datos personales a servicios externos.

Se eliminan o neutralizan:
  - correos, teléfonos, URLs y documentos de identidad
  - el nombre del candidato (si se conoce, y la primera frase cuando es un nombre)
  - ciudades colombianas
  - edad, fecha de nacimiento, estado civil, sexo/género
  - marcas de género en profesiones frecuentes (ingeniera/ingeniero -> ingenierx)

Los años de experiencia NO se tocan: son un criterio del cargo.
"""

import re

CIUDADES = [
    "Bogotá", "Bogota", "Medellín", "Medellin", "Cali", "Barranquilla", "Bucaramanga",
    "Pereira", "Manizales", "Cartagena", "Cúcuta", "Cucuta", "Ibagué", "Ibague",
    "Santa Marta", "Villavicencio", "Pasto", "Montería", "Monteria", "Neiva",
    "Armenia", "Popayán", "Popayan", "Tunja", "Sincelejo", "Valledupar", "Chía", "Chia",
]

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_URL = re.compile(r"(https?://\S+|www\.\S+|linkedin\.com/\S+)", re.IGNORECASE)
_TELEFONO = re.compile(r"(?<!\w)(\+?\d[\d\s().-]{6,}\d)(?!\w)")
_DOCUMENTO = re.compile(r"\b(c\.?c\.?|c[ée]dula|documento|ti|nit)\s*(n[°º.o]*)?\s*:?\s*[\d.]{6,}", re.IGNORECASE)
_CIUDAD = re.compile(r"\b(" + "|".join(re.escape(c) for c in CIUDADES) + r")\b", re.IGNORECASE)
_DATOS_PERSONALES = re.compile(
    r"(\b\d{1,2}\s+años\s+de\s+edad\b"
    r"|\bedad\s*:?\s*\d{1,2}(\s+años)?"
    r"|\bfecha\s+de\s+nacimiento\s*:?[^.;\n]*"
    r"|\bnacid[oa]\s+(el|en)\b[^.;\n]*"
    r"|\bestado\s+civil\s*:?\s*\w+"
    r"|\b(sexo|g[ée]nero)\s*:?\s*\w+)",
    re.IGNORECASE,
)

# raíz -> forma neutra. Se aplica a la forma masculina, femenina y plurales.
_PROFESIONES = {
    r"ingenier[oa]s?": "ingenierx",
    r"desarrollador(a|as|es)?": "desarrolladorx",
    r"coordinador(a|as|es)?": "coordinadorx",
    r"administrador(a|as|es)?": "administradorx",
    r"asesor(a|as|es)?": "asesorx",
    r"ejecutiv[oa]s?": "ejecutivx",
    r"licenciad[oa]s?": "licenciadx",
    r"psic[óo]log[oa]s?": "psicologx",
    r"tecn[óo]log[oa]s?": "tecnologx",
    r"diseñador(a|as|es)?": "diseñadorx",
    r"director(a|as|es)?": "directorx",
    r"jef[ea]s?": "jefx",
}
_PROFESION = re.compile(
    r"\b(" + "|".join(f"(?:{p})" for p in _PROFESIONES) + r")\b", re.IGNORECASE
)
_PROFESION_PATRONES = [(re.compile(rf"^{p}$", re.IGNORECASE), n) for p, n in _PROFESIONES.items()]

# Primera frase con forma de nombre propio: 2 a 5 palabras capitalizadas.
_NOMBRE_INICIAL = re.compile(
    r"^\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñü]+(?:\s+(?:de\s+|del\s+|la\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+){1,4})\s*[.\n]"
)

_ESPACIOS = re.compile(r"[ \t]{2,}")


def _neutralizar_profesion(match: re.Match) -> str:
    palabra = match.group(0)
    for patron, neutra in _PROFESION_PATRONES:
        if patron.match(palabra):
            return neutra
    return palabra


def anonimizar(texto: str, nombre: str | None = None) -> str:
    """Devuelve el texto sin datos personales ni marcas de género."""
    resultado = _NOMBRE_INICIAL.sub("[CANDIDATO]. ", texto, count=1)
    if nombre:
        for parte in sorted(set(nombre.split()), key=len, reverse=True):
            if len(parte) >= 3:
                resultado = re.sub(rf"\b{re.escape(parte)}\b", "[CANDIDATO]", resultado)
    resultado = _EMAIL.sub("[EMAIL]", resultado)
    resultado = _URL.sub("[URL]", resultado)
    resultado = _DOCUMENTO.sub("[DOCUMENTO]", resultado)
    resultado = _TELEFONO.sub("[TELEFONO]", resultado)
    resultado = _DATOS_PERSONALES.sub("[DATO PERSONAL]", resultado)
    resultado = _CIUDAD.sub("[CIUDAD]", resultado)
    resultado = _PROFESION.sub(_neutralizar_profesion, resultado)
    resultado = re.sub(r"(\[CANDIDATO\]\s*)+", "[CANDIDATO] ", resultado)
    resultado = re.sub(r"\]\s+([.,;:])", r"]\1", resultado)
    return _ESPACIOS.sub(" ", resultado).strip()
