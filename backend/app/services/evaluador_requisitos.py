"""
Evaluador explicable de requisitos.

Dado el texto de una hoja de vida y la lista de requisitos de un rol, decide
qué requisitos cumple el candidato buscando evidencia textual (palabras clave
y sinónimos por requisito) y devuelve un puntaje 0-100, el veredicto
apto/no apto y, para cada requisito, el fragmento del CV que lo sustenta.

Es la línea base determinística del Paso 2 (evaluar) y del Paso 3 (ranking):
no requiere API key ni modelos descargados, y cada decisión se puede rastrear
hasta una frase concreta del CV. El LLM (llm_service) podrá reemplazarlo o
complementarlo más adelante manteniendo la misma estructura de respuesta.
"""

import re
import unicodedata

# Fracción mínima de requisitos que debe cumplir un candidato para ser "apto".
# Con 4 requisitos exige 3; con 3 requisitos exige 2.
UMBRAL_APTO = 0.66

# Peso del cumplimiento de requisitos y de la experiencia en el puntaje final.
PESO_REQUISITOS = 80
PESO_EXPERIENCIA = 20
ANIOS_EXPERIENCIA_TOPE = 12

# Palabras clave por requisito (en minúsculas y sin tildes). La clave es el
# texto exacto del requisito tal como está definido en app/models/store.py.
LEXICO_REQUISITOS: dict[str, list[str]] = {
    # Full Stack
    "JavaScript/TypeScript": ["javascript", "typescript", "es6", "ecmascript"],
    "React o similar": ["react", "next.js", "nextjs", "vue", "angular", "svelte"],
    "Node.js o backend equivalente": [
        "node.js", "nodejs", "express", "nestjs", "django", "fastapi",
        "spring boot", "apis rest", "api rest", "backend",
    ],
    "Bases de datos SQL/NoSQL": [
        "postgresql", "postgres", "mysql", "mongodb", "sql server", "redis",
        "bases de datos", "base de datos", "sqlite", "dynamodb",
    ],
    # Recursos Humanos
    "Gestión de procesos de selección": [
        "seleccion de personal", "procesos de seleccion", "reclutamiento",
        "entrevistas por competencias", "headhunting", "atraccion de talento",
    ],
    "Manejo de nómina": [
        "nomina", "seguridad social", "prestaciones sociales", "pila",
        "liquidacion de salarios",
    ],
    "Comunicación interpersonal": [
        "comunicacion asertiva", "relaciones interpersonales",
        "comunicacion interpersonal", "manejo de conflictos", "escucha activa",
    ],
    # Ventas
    "Experiencia en ventas B2B/B2C": [
        "ventas b2b", "ventas b2c", "venta consultiva", "ejecutivo comercial",
        "ejecutiva comercial", "cuotas de venta", "metas comerciales",
        "b2b", "b2c",
    ],
    "Manejo de CRM": ["crm", "salesforce", "hubspot", "zoho", "pipedrive"],
    "Negociación": ["negociacion", "cierre de negocios", "manejo de objeciones"],
    # Marketing digital
    "SEO/SEM": [
        "seo", "sem", "google ads", "posicionamiento en buscadores",
        "keyword research",
    ],
    "Gestión de redes sociales": [
        "redes sociales", "community manager", "social media", "instagram",
        "tiktok", "meta ads",
    ],
    "Analítica web (Google Analytics)": [
        "google analytics", "ga4", "analitica web", "looker studio",
        "tag manager",
    ],
}

# Si una de estas expresiones aparece justo antes de la palabra clave, la
# mención no cuenta como evidencia ("sin experiencia en nómina").
_NEGACIONES = ("sin experiencia en", "sin conocimientos de", "no he trabajado con", "no maneja")

_PATRON_ANIOS = re.compile(r"(\d{1,2})\s+anos?\s+de\s+experiencia")


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar de forma robusta."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return sin_tildes.lower()


def _palabras_clave(requisito: str) -> list[str]:
    if requisito in LEXICO_REQUISITOS:
        return LEXICO_REQUISITOS[requisito]
    # Requisitos creados por el usuario: se usan sus propias palabras
    # significativas (y las partes separadas por "/") como palabras clave.
    partes = re.split(r"[/,()]| o | y ", normalizar(requisito))
    return [p.strip() for p in partes if len(p.strip()) >= 3]


def _buscar(clave: str, texto_norm: str) -> re.Match | None:
    patron = r"(?<![a-z0-9])" + re.escape(clave) + r"(?![a-z0-9])"
    for match in re.finditer(patron, texto_norm):
        previo = texto_norm[max(0, match.start() - 30):match.start()]
        if not any(neg in previo for neg in _NEGACIONES):
            return match
    return None


def _fragmento(texto: str, inicio: int, fin: int, margen: int = 70) -> str:
    a = max(0, inicio - margen)
    b = min(len(texto), fin + margen)
    prefijo = "…" if a > 0 else ""
    sufijo = "…" if b < len(texto) else ""
    return prefijo + texto[a:b].strip().replace("\n", " ") + sufijo


def extraer_anios_experiencia(cv_texto: str) -> int:
    anios = [int(n) for n in _PATRON_ANIOS.findall(normalizar(cv_texto))]
    return max(anios) if anios else 0


def evaluar_cv(cv_texto: str, requisitos: list[str]) -> dict:
    """
    Evalúa una hoja de vida contra los requisitos de un rol.

    Returns:
      dict con: score (0-100), estado ("apto" | "no_apto"), anios_experiencia,
      evaluacion (list[{requisito, cumple, evidencia, nota}]),
      requisitos_cumplidos, requisitos_faltantes, explicacion
    """
    # normalizar() conserva la longitud del texto (solo quita marcas
    # diacríticas combinadas), así que los índices sirven en el original.
    texto_norm = normalizar(cv_texto)
    if len(texto_norm) != len(cv_texto):
        cv_texto = texto_norm

    evaluacion = []
    for requisito in requisitos:
        evidencia = None
        clave_encontrada = None
        for clave in _palabras_clave(requisito):
            match = _buscar(clave, texto_norm)
            if match:
                clave_encontrada = clave
                evidencia = _fragmento(cv_texto, match.start(), match.end())
                break

        if evidencia:
            nota = f"Se encontró evidencia de «{clave_encontrada}» en la hoja de vida."
        else:
            nota = "No se encontró mención de este requisito en la hoja de vida."

        evaluacion.append({
            "requisito": requisito,
            "cumple": evidencia is not None,
            "evidencia": evidencia,
            "nota": nota,
        })

    return resumir(evaluacion, extraer_anios_experiencia(cv_texto))


def resumir(evaluacion: list[dict], anios: int) -> dict:
    """
    Puntaje, veredicto y explicación a partir de la evaluación por requisito.
    Lo comparten el evaluador por palabras clave y el evaluador con LLM, así
    ambos motores califican con la misma regla.
    """
    requisitos = [e["requisito"] for e in evaluacion]
    cumplidos = [e["requisito"] for e in evaluacion if e["cumple"]]
    faltantes = [e["requisito"] for e in evaluacion if not e["cumple"]]
    fraccion = len(cumplidos) / len(requisitos) if requisitos else 0.0

    score = round(
        PESO_REQUISITOS * fraccion
        + PESO_EXPERIENCIA * min(anios, ANIOS_EXPERIENCIA_TOPE) / ANIOS_EXPERIENCIA_TOPE,
        1,
    )
    estado = "apto" if fraccion >= UMBRAL_APTO else "no_apto"

    explicacion = (
        f"Cumple {len(cumplidos)} de {len(requisitos)} requisitos"
        f" ({round(fraccion * 100)}%) y reporta {anios} año(s) de experiencia. "
    )
    if estado == "apto":
        explicacion += "Supera el umbral mínimo de requisitos, por lo que es apto para el rol."
    else:
        explicacion += (
            f"No alcanza el mínimo del {round(UMBRAL_APTO * 100)}% de requisitos, "
            "por lo que no es apto para el rol."
        )
    if faltantes:
        explicacion += " Le falta: " + ", ".join(faltantes) + "."

    return {
        "score": score,
        "estado": estado,
        "anios_experiencia": anios,
        "evaluacion": evaluacion,
        "requisitos_cumplidos": cumplidos,
        "requisitos_faltantes": faltantes,
        "explicacion": explicacion,
    }
