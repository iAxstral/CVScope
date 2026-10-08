"""
Genera los dos datasets sintéticos de CVScope (semilla fija => reproducible):

  data/dataset_seleccion.csv
      Hojas de vida etiquetadas con su rol y con el veredicto apto/no apto.
      Sirve para el paso de SELECCIÓN: entrenar/evaluar el clasificador de rol
      (clasificador_rol.pkl) y validar la decisión apto/no apto.

  data/dataset_ranking.csv
      Un pool de candidatos por rol con un puntaje de referencia (ground truth)
      calculado a partir de los requisitos que cumple cada uno y sus años de
      experiencia. Sirve para el paso de RANKING: obtener las 5 mejores hojas
      de vida de cada rol y medir qué tan bien el sistema recupera ese top 5.

Uso (desde backend/):
    python scripts/generar_datasets.py
"""

import csv
import random
import unicodedata
from pathlib import Path

SEED = 2026
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

N_SELECCION_POR_ROL = 60
N_RANKING_POR_ROL = 15

# Debe coincidir con la fórmula de app/services/evaluador_requisitos.py
UMBRAL_APTO = 0.66
PESO_REQUISITOS = 80
PESO_EXPERIENCIA = 20
ANIOS_EXPERIENCIA_TOPE = 12

# Probabilidad de describir un requisito cumplido con una redacción poco
# común (sin palabras clave obvias) y de incluir una mención "trampa" de un
# requisito no cumplido. Introducen ruido realista en los datos.
P_REDACCION_IMPLICITA = 0.08
P_MENCION_TRAMPA = 0.06

ROLES = {
    "fullstack": {
        "titulo": ["Profesional en desarrollo Full Stack", "Profesional en ingeniería de software"],
        "estudios": ["Ingeniería de Sistemas", "Ingeniería de Software", "Ingeniería Electrónica", "Tecnología en Desarrollo de Software"],
        "requisitos": {
            "JavaScript/TypeScript": {
                "explicita": [
                    "Programo a diario en JavaScript y TypeScript con buenas prácticas de tipado.",
                    "Dominio de JavaScript moderno (ES6+) y TypeScript en proyectos productivos.",
                    "Desarrollo de módulos en TypeScript con pruebas unitarias en Jest.",
                ],
                "implicita": ["Escribo el código del lado del cliente con tipado estático y pruebas automatizadas."],
                "trampa": ["Actualmente sin experiencia en JavaScript, aunque planeo estudiarlo."],
            },
            "React o similar": {
                "explicita": [
                    "Construí interfaces con React y Next.js para un portal de clientes.",
                    "Desarrollo de SPAs con Vue.js y componentes reutilizables.",
                    "Mantenimiento de una aplicación web en Angular con más de 40 vistas.",
                ],
                "implicita": ["Maquetación de interfaces dinámicas basadas en componentes reutilizables."],
                "trampa": ["Sin conocimientos de React por el momento."],
            },
            "Node.js o backend equivalente": {
                "explicita": [
                    "Diseño de APIs REST con Node.js y Express.",
                    "Implementación de microservicios en NestJS desplegados en AWS.",
                    "Desarrollo de servicios en Python con FastAPI y Django.",
                ],
                "implicita": ["Construcción de los servicios del lado del servidor que exponen la lógica de negocio."],
                "trampa": ["No he trabajado con Node.js en proyectos reales."],
            },
            "Bases de datos SQL/NoSQL": {
                "explicita": [
                    "Modelado de datos en PostgreSQL y consultas optimizadas.",
                    "Uso de MongoDB y Redis para cachés y documentos.",
                    "Administración de esquemas en MySQL y migraciones.",
                ],
                "implicita": ["Diseño del modelo relacional y optimización de consultas con índices."],
                "trampa": ["Sin experiencia en bases de datos más allá de hojas de cálculo."],
            },
        },
        "relleno": [
            "Uso de Git y GitHub para control de versiones.",
            "Trabajo bajo metodologías ágiles (Scrum y Kanban).",
            "Contenedores con Docker y despliegues continuos.",
            "Participación en revisiones de código y pair programming.",
            "Inglés intermedio (B2) para lectura de documentación técnica.",
        ],
        "empresas": ["Globant", "Rappi", "Bancolombia", "una startup fintech", "una consultora de software", "Accenture"],
    },
    "rrhh": {
        "titulo": ["Profesional de Talento Humano", "Profesional en gestión humana"],
        "estudios": ["Psicología", "Administración de Empresas", "Trabajo Social", "Especialización en Gestión Humana"],
        "requisitos": {
            "Gestión de procesos de selección": {
                "explicita": [
                    "Lideré procesos de selección de personal para cargos operativos y administrativos.",
                    "Reclutamiento y entrevistas por competencias para más de 200 vacantes al año.",
                    "Estrategias de atracción de talento y headhunting para perfiles directivos.",
                ],
                "implicita": ["Filtré hojas de vida y apliqué pruebas psicotécnicas a aspirantes."],
                "trampa": ["Sin experiencia en reclutamiento; mi experiencia es en archivo documental."],
            },
            "Manejo de nómina": {
                "explicita": [
                    "Liquidación de nómina quincenal para 350 empleados.",
                    "Manejo de nómina, seguridad social y prestaciones sociales.",
                    "Elaboración de la planilla PILA y novedades de nómina.",
                ],
                "implicita": ["Cálculo de pagos quincenales, horas extra y aportes de los trabajadores."],
                "trampa": ["Sin experiencia en nómina, aunque conozco su importancia."],
            },
            "Comunicación interpersonal": {
                "explicita": [
                    "Comunicación asertiva con colaboradores y líderes de área.",
                    "Fuertes relaciones interpersonales y manejo de conflictos.",
                    "Escucha activa en procesos de acompañamiento a empleados.",
                ],
                "implicita": ["Facilité espacios de diálogo entre equipos y mediación entre compañeros."],
                "trampa": [],
            },
        },
        "relleno": [
            "Organización de jornadas de bienestar laboral.",
            "Manejo de Excel avanzado y tablas dinámicas.",
            "Apoyo en programas de capacitación y onboarding.",
            "Conocimiento del Código Sustantivo del Trabajo.",
            "Gestión de evaluaciones de desempeño anuales.",
        ],
        "empresas": ["Grupo Éxito", "una caja de compensación", "Alpina", "una empresa de servicios temporales", "Colsubsidio", "una clínica privada"],
    },
    "ventas": {
        "titulo": ["Profesional en ventas", "Profesional del área comercial"],
        "estudios": ["Administración de Empresas", "Mercadeo y Ventas", "Negocios Internacionales", "Tecnología en Gestión Comercial"],
        "requisitos": {
            "Experiencia en ventas B2B/B2C": {
                "explicita": [
                    "Ventas B2B a cuentas corporativas con cumplimiento de cuotas de venta del 115%.",
                    "Experiencia como ejecutivo comercial en ventas B2C de servicios financieros.",
                    "Venta consultiva de software a medianas empresas con metas comerciales mensuales.",
                ],
                "implicita": ["Atendí cartera de clientes empresariales y superé el presupuesto trimestral."],
                "trampa": [],
            },
            "Manejo de CRM": {
                "explicita": [
                    "Seguimiento del embudo comercial en Salesforce.",
                    "Gestión de oportunidades y contactos en HubSpot CRM.",
                    "Registro de actividades y pronósticos en Pipedrive.",
                ],
                "implicita": ["Mantuve actualizada la plataforma de seguimiento de clientes y oportunidades."],
                "trampa": ["No maneja CRM; llevaba los clientes en una libreta."],
            },
            "Negociación": {
                "explicita": [
                    "Negociación de contratos anuales con grandes superficies.",
                    "Cierre de negocios y manejo de objeciones con clientes clave.",
                    "Habilidades de negociación de precios y condiciones comerciales.",
                ],
                "implicita": ["Acordé descuentos y plazos de pago con distribuidores regionales."],
                "trampa": [],
            },
        },
        "relleno": [
            "Prospección telefónica y visitas en campo.",
            "Elaboración de cotizaciones y propuestas comerciales.",
            "Orientación al logro y trabajo bajo presión.",
            "Licencia de conducción y disponibilidad para viajar.",
            "Atención y fidelización de clientes.",
        ],
        "empresas": ["Claro", "Postobón", "una distribuidora de alimentos", "Seguros Bolívar", "un concesionario de vehículos", "Siemens"],
    },
    "marketing": {
        "titulo": ["Profesional en marketing digital", "Profesional en mercadeo digital"],
        "estudios": ["Mercadeo", "Publicidad", "Comunicación Social", "Diseño Gráfico"],
        "requisitos": {
            "SEO/SEM": {
                "explicita": [
                    "Estrategias SEO on-page y off-page que duplicaron el tráfico orgánico.",
                    "Gestión de campañas SEM en Google Ads con presupuesto mensual de USD 8.000.",
                    "Keyword research y optimización de contenidos para posicionamiento en buscadores.",
                ],
                "implicita": ["Logré que el sitio apareciera en los primeros resultados de búsqueda para términos clave."],
                "trampa": ["Sin conocimientos de SEO, me enfoco en diseño visual."],
            },
            "Gestión de redes sociales": {
                "explicita": [
                    "Community manager de marcas de consumo masivo en Instagram y TikTok.",
                    "Planeación de parrillas de contenido para redes sociales.",
                    "Pauta en Meta Ads y estrategia de social media.",
                ],
                "implicita": ["Administré las cuentas oficiales de la marca y respondí a la comunidad digital."],
                "trampa": [],
            },
            "Analítica web (Google Analytics)": {
                "explicita": [
                    "Medición de conversiones con Google Analytics 4 (GA4) y Tag Manager.",
                    "Tableros de resultados en Looker Studio para la gerencia.",
                    "Analítica web y reportes de embudo de conversión.",
                ],
                "implicita": ["Medí el comportamiento de los visitantes del sitio y reporté tasas de conversión."],
                "trampa": ["Sin experiencia en Google Analytics."],
            },
        },
        "relleno": [
            "Redacción de copies y piezas para email marketing.",
            "Manejo de Canva y Adobe Photoshop.",
            "Coordinación con agencias creativas.",
            "Gestión de influenciadores y alianzas de marca.",
            "Inglés intermedio para campañas regionales.",
        ],
        "empresas": ["una agencia digital", "Falabella", "Avianca", "una marca de cosméticos", "Juan Valdez", "una tienda e-commerce"],
    },
}

NOMBRES = [
    "Valentina", "Santiago", "Camila", "Sebastián", "Mariana", "Mateo", "Daniela", "Samuel",
    "Laura", "Nicolás", "Isabella", "Juan David", "Sofía", "Andrés", "Gabriela", "Felipe",
    "Natalia", "Alejandro", "Paula", "Diego", "Juliana", "Tomás", "Manuela", "Carlos",
    "Catalina", "Esteban", "Luisa", "Miguel Ángel", "Ana María", "Julián",
]
APELLIDOS = [
    "Rojas", "Gómez", "Rodríguez", "Martínez", "López", "García", "Hernández", "Díaz",
    "Moreno", "Ramírez", "Torres", "Vargas", "Castro", "Ortiz", "Jiménez", "Suárez",
    "Mejía", "Restrepo", "Cárdenas", "Pardo", "Salazar", "Ospina", "Quintero", "Herrera",
]
CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Pereira", "Manizales", "Cartagena"]


def _slug(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto)
    base = "".join(c for c in base if not unicodedata.combining(c))
    return base.lower().replace(" ", ".")


def _puntaje(n_cumplidos: int, n_requisitos: int, anios: int) -> float:
    fraccion = n_cumplidos / n_requisitos
    return round(
        PESO_REQUISITOS * fraccion
        + PESO_EXPERIENCIA * min(anios, ANIOS_EXPERIENCIA_TOPE) / ANIOS_EXPERIENCIA_TOPE,
        1,
    )


def _generar_cv(rng: random.Random, rol: str, cumplidos: set[str], anios: int) -> dict:
    cfg = ROLES[rol]
    nombre = f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}"
    email = f"{_slug(nombre.split()[0])}.{_slug(nombre.split()[-2])}{rng.randint(1, 99)}@email.com"
    titulo = rng.choice(cfg["titulo"])
    estudios = rng.choice(cfg["estudios"])
    ciudad = rng.choice(CIUDADES)

    logros = []
    for requisito, frases in cfg["requisitos"].items():
        if requisito in cumplidos:
            if frases["implicita"] and rng.random() < P_REDACCION_IMPLICITA:
                logros.append(rng.choice(frases["implicita"]))
            else:
                logros.append(rng.choice(frases["explicita"]))
        elif frases["trampa"] and rng.random() < P_MENCION_TRAMPA:
            logros.append(rng.choice(frases["trampa"]))

    logros += rng.sample(cfg["relleno"], k=2)
    rng.shuffle(logros)

    empresa_actual, empresa_previa = rng.sample(cfg["empresas"], k=2)
    corte = max(1, len(logros) // 2)
    exp_actual = " ".join(logros[:corte])
    exp_previa = " ".join(logros[corte:])

    texto = (
        f"{nombre}. {titulo} en {ciudad}. "
        f"Perfil: {anios} {'año' if anios == 1 else 'años'} de experiencia en el área. "
        f"Formación: {estudios}. "
        f"Experiencia reciente en {empresa_actual}: {exp_actual} "
    )
    if exp_previa:
        texto += f"Experiencia previa en {empresa_previa}: {exp_previa}"

    return {"nombre": nombre, "email": email, "hoja_de_vida_texto": texto.strip()}


def _elegir_cumplidos(rng: random.Random, requisitos: list[str], apto: bool) -> set[str]:
    n = len(requisitos)
    minimo_apto = next(k for k in range(n + 1) if k / n >= UMBRAL_APTO)
    if apto:
        k = rng.randint(minimo_apto, n)
    else:
        k = rng.randint(0, minimo_apto - 1)
    return set(rng.sample(requisitos, k=k))


def generar_seleccion(rng: random.Random) -> list[dict]:
    filas = []
    for rol, cfg in ROLES.items():
        requisitos = list(cfg["requisitos"])
        for i in range(N_SELECCION_POR_ROL):
            apto = rng.random() < 0.55
            cumplidos = _elegir_cumplidos(rng, requisitos, apto)
            anios = rng.randint(0, 15)
            cv = _generar_cv(rng, rol, cumplidos, anios)
            filas.append({
                "id": f"sel-{rol}-{i + 1:03d}",
                "rol": rol,
                "hoja_de_vida_texto": cv["hoja_de_vida_texto"],
                "anios_experiencia": anios,
                "requisitos_cumplidos": "|".join(r for r in requisitos if r in cumplidos),
                "apto": int(apto),
            })
    rng.shuffle(filas)
    return filas


def generar_ranking(rng: random.Random) -> list[dict]:
    filas = []
    for rol, cfg in ROLES.items():
        requisitos = list(cfg["requisitos"])
        for i in range(N_RANKING_POR_ROL):
            # ~2/3 aptos para que siempre haya un top 5 con competencia real
            apto = i < 10
            cumplidos = _elegir_cumplidos(rng, requisitos, apto)
            anios = rng.randint(1, 15)
            cv = _generar_cv(rng, rol, cumplidos, anios)
            filas.append({
                "id": f"rk-{rol}-{i + 1:02d}",
                "rol": rol,
                "nombre": cv["nombre"],
                "email": cv["email"],
                "hoja_de_vida_texto": cv["hoja_de_vida_texto"],
                "anios_experiencia": anios,
                "requisitos_cumplidos": "|".join(r for r in requisitos if r in cumplidos),
                "apto": int(apto),
                "puntaje_referencia": _puntaje(len(cumplidos), len(requisitos), anios),
            })
    # Posición de referencia dentro de cada rol (1 = mejor), solo entre aptos
    for rol in ROLES:
        aptos = sorted(
            (f for f in filas if f["rol"] == rol and f["apto"]),
            key=lambda f: (-f["puntaje_referencia"], f["id"]),
        )
        for pos, fila in enumerate(aptos, start=1):
            fila["posicion_referencia"] = pos
    for fila in filas:
        fila.setdefault("posicion_referencia", "")
    rng.shuffle(filas)
    return filas


def _escribir(ruta: Path, filas: list[dict]) -> None:
    with ruta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        writer.writeheader()
        writer.writerows(filas)


def main() -> None:
    rng = random.Random(SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    seleccion = generar_seleccion(rng)
    ranking = generar_ranking(rng)

    _escribir(DATA_DIR / "dataset_seleccion.csv", seleccion)
    _escribir(DATA_DIR / "dataset_ranking.csv", ranking)

    print(f"dataset_seleccion.csv: {len(seleccion)} hojas de vida")
    print(f"dataset_ranking.csv:   {len(ranking)} hojas de vida")


if __name__ == "__main__":
    main()
