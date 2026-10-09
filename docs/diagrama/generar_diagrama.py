"""
Genera el diagrama de la red neuronal competitiva de CVScope en dos formatos
a partir de una sola definición:

  red_competitiva.drawio  -> editable en draw.io / diagrams.net
  red_competitiva.svg     -> imagen que GitHub muestra directamente

Uso (desde la raíz del repo):
    python docs/diagrama/generar_diagrama.py

Para exportar a PNG, abrir el .drawio en diagrams.net (Archivo > Exportar
como > PNG) o capturar el .svg en un navegador.
"""

import math
from pathlib import Path
from xml.sax.saxutils import escape

SALIDA = Path(__file__).resolve().parent
ANCHO, ALTO = 1720, 1330

# Paleta de la aplicación (frontend/src/index.css)
NAVY = "#17244d"
PRIMARY = "#22346b"
PRIMARY_SOFT = "#e7ebf5"
ACCENT = "#e8a63d"
ACCENT_SOFT = "#fbf0da"
SUCCESS = "#2f9e64"
SUCCESS_SOFT = "#e7f6ee"
DANGER = "#d64550"
INK = "#17203a"
INK_SOFT = "#5c6b8a"
BORDER = "#dfe4ee"
SURFACE = "#ffffff"
SURFACE_ALT = "#f7f9fc"
FONDO = "#f1f4f8"

nodos: list[dict] = []
aristas: list[dict] = []


def caja(id_, x, y, w, h, texto, fondo=SURFACE, borde=BORDER, color=INK, tam=12,
         negrita=False, forma="rect", alinear="center", redondeo=8, titulo=False, discontinuo=False):
    nodos.append(dict(id=id_, x=x, y=y, w=w, h=h, texto=texto, fondo=fondo, borde=borde,
                      color=color, tam=tam, negrita=negrita, forma=forma, alinear=alinear,
                      redondeo=redondeo, titulo=titulo, discontinuo=discontinuo))


def texto(id_, x, y, w, h, contenido, color=INK_SOFT, tam=12, negrita=False, alinear="center"):
    caja(id_, x, y, w, h, contenido, fondo="none", borde="none", color=color, tam=tam,
         negrita=negrita, alinear=alinear)


def neurona(id_, cx, cy, d, etiqueta="", fondo=SURFACE, borde=PRIMARY, color=INK, tam=11):
    caja(id_, cx - d / 2, cy - d / 2, d, d, etiqueta, fondo=fondo, borde=borde, color=color,
         tam=tam, forma="ellipse")


def flecha(origen, destino, tipo="flujo", etiqueta="", puntos=None):
    aristas.append(dict(origen=origen, destino=destino, tipo=tipo, etiqueta=etiqueta,
                        puntos=puntos or []))


def ancla(id_, x, y):
    """Punto invisible para que una flecha llegue exactamente a (x, y)."""
    caja(id_, x - 1, y - 1, 2, 2, "", fondo="none", borde="none")


ESTILO_ARISTA = {
    "flujo": dict(color=PRIMARY, ancho=2, guiones=False, punta=True),
    "conexion": dict(color="#b8c2d6", ancho=1, guiones=False, punta=False),
    "inhibicion": dict(color=DANGER, ancho=1.6, guiones=True, punta=True),
    "excitacion": dict(color=SUCCESS, ancho=1.8, guiones=False, punta=True),
    "entrenamiento": dict(color=ACCENT, ancho=2, guiones=True, punta=True),
}


# ---------------------------------------------------------------------------
# Definición del diagrama
# ---------------------------------------------------------------------------

def ejemplo_duelo(s_a: float, s_b: float, epsilon: float = 0.5) -> list[tuple[float, float]]:
    """Trayectoria real de MAXNET con 2 neuronas (misma regla que el backend)."""
    m = max(s_a, s_b)
    a, b = math.exp(s_a - m), math.exp(s_b - m)
    pasos = [(a, b)]
    while a > 0 and b > 0:
        a, b = max(0.0, a - epsilon * b), max(0.0, b - epsilon * a)
        pasos.append((a, b))
    return pasos


def construir() -> None:
    texto("titulo", 30, 18, 1660, 34, "CVScope · Red neuronal competitiva (tipo Hamming)",
          color=INK, tam=24, negrita=True, alinear="left")
    texto("subtitulo", 30, 54, 1660, 26,
          "Cada hoja de vida es una neurona. Una capa de evaluación entrenada calcula su fuerza y una "
          "capa competitiva (MAXNET) las enfrenta por inhibición lateral hasta que solo una queda activa.",
          tam=13, alinear="left")

    # Bandas de las etapas
    columnas = [
        ("col_entrada", 30, 230, "1 · DATOS DE ENTRADA"),
        ("col_pre", 275, 270, "2 · PREPROCESAMIENTO"),
        ("col_eval", 560, 450, "3 · CAPA DE EVALUACIÓN (feedforward, entrenada)"),
        ("col_comp", 1025, 405, "4 · CAPA COMPETITIVA MAXNET (recurrente)"),
        ("col_salida", 1445, 245, "5 · SALIDA"),
    ]
    for id_, x, w, titulo in columnas:
        caja(id_, x, 100, w, 690, "", fondo=SURFACE_ALT, borde=BORDER, redondeo=14)
        caja(id_ + "_t", x, 100, w, 38, titulo, fondo=NAVY, borde=NAVY, color="#ffffff",
             tam=12, negrita=True, redondeo=14)

    # 1 · Entrada -----------------------------------------------------------
    for i, (y, etiqueta) in enumerate([(160, "Hoja de vida 1"), (235, "Hoja de vida 2"),
                                       (345, "Hoja de vida n")]):
        caja(f"cv{i}", 55, y, 180, 58, f"{etiqueta}\nPDF · DOCX · TXT", negrita=True,
             borde=PRIMARY, tam=12)
    texto("cv_puntos", 55, 298, 180, 40, "⋮", color=INK_SOFT, tam=22)
    caja("requisitos", 55, 440, 180, 150,
         "Requisitos del rol\nej. Full Stack:\n• JavaScript/TypeScript\n• React o similar\n"
         "• Node.js o backend\n• Bases de datos", fondo=ACCENT_SOFT, borde=ACCENT, tam=11,
         negrita=True, alinear="left")
    texto("entrada_nota", 45, 610, 200, 150,
          "Entran todas las hojas de vida que compiten por el mismo rol (n = 15 en el dataset de "
          "ranking) y los requisitos mínimos de ese rol.", tam=11)

    # 2 · Preprocesamiento --------------------------------------------------
    caja("anonimizar", 295, 160, 230, 96,
         "Anonimización\nquita nombre, ciudad, edad,\ngénero, correo y teléfono",
         borde=PRIMARY, negrita=True, tam=11)
    caja("extraer", 295, 300, 230, 80,
         "Extracción de características\nvector x por hoja de vida", borde=PRIMARY, negrita=True,
         tam=11)
    texto("vector_t", 295, 400, 230, 22, "x ∈ ℝ¹⁰²⁶", color=INK, tam=14, negrita=True)
    caja("x1", 305, 428, 210, 48, "x₁ = fracción de requisitos\ncumplidos (0 a 1)",
         fondo=PRIMARY_SOFT, borde=PRIMARY, tam=11, redondeo=4)
    caja("x2", 305, 476, 210, 48, "x₂ = años de experiencia / 12\n(tope 1)",
         fondo=PRIMARY_SOFT, borde=PRIMARY, tam=11, redondeo=4)
    caja("x3", 305, 524, 210, 62, "x₃ … x₁₀₂₆ = 1024 n-gramas\n(palabras y pares de palabras,\nhashing)",
         fondo=PRIMARY_SOFT, borde=PRIMARY, tam=11, redondeo=4)
    texto("pre_nota", 290, 600, 240, 150,
          "La red nunca ve datos personales: así no puede aprender sesgos por nombre, ciudad o "
          "género. Los n-gramas le permiten reconocer requisitos escritos sin palabras clave.",
          tam=11)

    # 3 · Capa de evaluación (red siamesa 1026-64-32-1) ----------------------
    capas = [
        (620, [175, 220, 265, 345], "Entrada\n1026"),
        (735, [190, 235, 280, 340], "Oculta 1\n64 · ReLU"),
        (850, [205, 250, 320], "Oculta 2\n32 · ReLU"),
    ]
    ids_capas = []
    for c, (cx, ys, etiqueta) in enumerate(capas):
        ids = []
        for k, cy in enumerate(ys):
            id_ = f"n{c}_{k}"
            neurona(id_, cx, cy, 28, fondo=PRIMARY_SOFT)
            ids.append(id_)
        texto(f"n{c}_p", cx - 20, (ys[-2] + ys[-1]) / 2 - 12, 40, 24, "⋮", tam=16)
        texto(f"n{c}_t", cx - 50, 372, 100, 36, etiqueta, color=INK, tam=11, negrita=True)
        ids_capas.append(ids)
    neurona("salida_s", 960, 262, 46, "s(x)", fondo=NAVY, borde=NAVY, color="#ffffff", tam=13)
    texto("salida_s_t", 896, 372, 58, 36, "Salida\nfuerza", color=INK, tam=11, negrita=True)
    for izq, der in zip(ids_capas, ids_capas[1:]):
        for a in izq:
            for b in der:
                flecha(a, b, "conexion")
    for a in ids_capas[-1]:
        flecha(a, "salida_s", "conexion")

    caja("siamesa", 585, 425, 330, 54,
         "Misma red y mismos pesos para todas las hojas de vida (red siamesa)",
         fondo=SURFACE, borde=PRIMARY, tam=11, negrita=True, discontinuo=True)
    caja("fuerzas", 585, 500, 400, 118,
         "Una fuerza por hoja de vida\nHoja de vida 1  →  s₁ = 23.4\nHoja de vida 2  →  s₂ = 23.2\n"
         "Hoja de vida n  →  sₙ = 9.8", fondo=SURFACE, borde=BORDER, tam=11, alinear="left",
         negrita=True)
    caja("activacion", 585, 640, 400, 70,
         "Activación inicial de cada neurona competitiva\naᵢ(0) = exp(sᵢ − max s)   ∈ (0, 1]",
         fondo=ACCENT_SOFT, borde=ACCENT, tam=12, negrita=True)

    # 4 · Capa competitiva MAXNET --------------------------------------------
    neurona("c1", 1120, 225, 72, "HV 1\na₁", fondo=SURFACE, borde=PRIMARY, tam=12)
    neurona("c2", 1330, 225, 72, "HV 2\na₂", fondo=SURFACE, borde=PRIMARY, tam=12)
    neurona("cn", 1225, 385, 72, "HV n\naₙ", fondo=SURFACE, borde=PRIMARY, tam=12)
    for a, b in [("c1", "c2"), ("c2", "c1"), ("c1", "cn"), ("cn", "c1"), ("c2", "cn"), ("cn", "c2")]:
        flecha(a, b, "inhibicion")
    texto("eps1", 1195, 196, 60, 20, "−ε", color=DANGER, tam=13, negrita=True)
    texto("eps2", 1100, 296, 50, 20, "−ε", color=DANGER, tam=13, negrita=True)
    texto("eps3", 1300, 296, 50, 20, "−ε", color=DANGER, tam=13, negrita=True)
    for id_ in ("c1", "c2", "cn"):
        flecha(id_, id_, "excitacion", "+1")
    caja("regla", 1045, 470, 365, 92,
         "Regla de competencia (cada iteración t)\naᵢ(t+1) = max(0, aᵢ(t) − ε · Σⱼ≠ᵢ aⱼ(t))\n"
         "con 0 < ε < 1/(S − 1)", fondo=SURFACE, borde=PRIMARY, tam=12, negrita=True)
    caja("wta", 1045, 575, 365, 46,
         "Se repite hasta que solo una neurona queda activa\n(winner-take-all)",
         fondo=SUCCESS_SOFT, borde=SUCCESS, color=INK, tam=11, negrita=True)
    pasos = ejemplo_duelo(23.4, 23.2)
    filas = "\n".join(f"t = {t}:   A = {a:.2f}   B = {b:.2f}" for t, (a, b) in enumerate(pasos))
    caja("ejemplo", 1045, 634, 365, 30 + 17 * len(pasos),
         f"Ejemplo: duelo de 2 neuronas (ε = 0.5)\n{filas}\n"
         f"→ gana A (P = {100 / (1 + math.exp(-(23.4 - 23.2))):.1f} %)",
         fondo=SURFACE, borde=BORDER, tam=11, alinear="left", negrita=True)

    # 5 · Salida -----------------------------------------------------------
    caja("onehot", 1470, 160, 195, 80, "Salida one-hot\n[0, 1, 0, …, 0]\nsolo la ganadora en 1",
         fondo=NAVY, borde=NAVY, color="#ffffff", tam=12, negrita=True)
    caja("ganadora", 1470, 268, 195, 62, "Hoja de vida ganadora\n(campeona del rol)",
         fondo=ACCENT, borde=ACCENT, color=NAVY, tam=12, negrita=True)
    caja("probs", 1470, 352, 195, 66, "Probabilidad de ganar\nPᵢ = softmax(s)ᵢ\nduelo: σ(s_A − s_B)",
         tam=11, negrita=True, borde=PRIMARY)
    caja("top5", 1470, 440, 195, 66, "Top 5\nse retira la ganadora\ny se repite la competencia",
         tam=11, negrita=True, borde=PRIMARY)
    caja("torneo", 1470, 528, 195, 82, "Torneo\nduelos de 2 neuronas;\nla ganadora pasa\na la siguiente ronda",
         tam=11, negrita=True, borde=PRIMARY)
    caja("explicacion", 1470, 632, 195, 82, "Explicación\nrequisitos con evidencia\ne iteraciones de\ninhibición",
         tam=11, negrita=True, borde=PRIMARY)

    # Flujo principal
    for i in range(3):
        flecha(f"cv{i}", "anonimizar")
    flecha("anonimizar", "extraer")
    flecha("requisitos", "x1", "flujo")
    flecha("extraer", "n0_3", etiqueta="x")
    ancla("regla_ancla", 1045, 516)
    flecha("activacion", "regla_ancla", "flujo", "aᵢ(0)", puntos=[(1015, 675), (1015, 516)])
    ancla("fuerzas_ancla", 960, 500)
    flecha("salida_s", "fuerzas_ancla")
    flecha("fuerzas", "activacion")
    flecha("c2", "onehot", "flujo", "ganadora")
    flecha("onehot", "ganadora")

    # Entrenamiento ----------------------------------------------------------
    caja("banda_ent", 30, 810, 1660, 170, "", fondo=ACCENT_SOFT, borde=ACCENT, redondeo=14)
    texto("ent_t", 50, 818, 900, 26, "ENTRENAMIENTO DE LA CAPA DE EVALUACIÓN (fuera de línea)",
          color=NAVY, tam=13, negrita=True, alinear="left")
    pasos_ent = [
        ("e1", "Dataset de selección\n240 hojas de vida\netiquetadas por rol"),
        ("e2", "4.512 duelos dentro de cada rol\ngana la de mayor puntaje\nde referencia (empate = 0.5)"),
        ("e3", "P(A gana a B) = σ(s(A) − s(B))\npérdida: entropía cruzada\npor pares"),
        ("e4", "Retropropagación\nAdam + L2 · 40 épocas"),
        ("e5", "Prueba (dataset de ranking)\nexactitud en duelos 0.959\nprecisión@5 0.80 (base 0.70)"),
    ]
    for k, (id_, contenido) in enumerate(pasos_ent):
        caja(id_, 55 + k * 330, 855, 290, 100, contenido, fondo=SURFACE, borde=ACCENT, tam=12,
             negrita=True)
        if k:
            flecha(pasos_ent[k - 1][0], id_, "entrenamiento")
    ancla("eval_ancla", 785, 790)
    flecha("e4", "eval_ancla", "entrenamiento", "actualiza los pesos de la capa 3",
           puntos=[(1190, 800), (785, 800)])

    # Capa competitiva que aprende (LVQ) ------------------------------------
    caja("banda_lvq", 30, 995, 1660, 235, "", fondo=SUCCESS_SOFT, borde=SUCCESS, redondeo=14)
    texto("lvq_t", 50, 1003, 1200, 26,
          "CAPA COMPETITIVA QUE APRENDE · LVQ (decide apto / no apto)",
          color=NAVY, tam=13, negrita=True, alinear="left")
    caja("l1", 55, 1040, 290, 86, "Entrada\nel mismo vector x ∈ ℝ¹⁰²⁶ del paso 2\n(rasgos explícitos con peso 3)",
         fondo=SURFACE, borde=SUCCESS, tam=12, negrita=True)
    caja("l2", 385, 1040, 290, 86, "4 neuronas prototipo\n2 «apto» y 2 «no apto»\ncada una con pesos w_k",
         fondo=SURFACE, borde=SUCCESS, tam=12, negrita=True)
    caja("l3", 715, 1040, 290, 86, "Competencia\ngana la neurona más cercana:\nk* = argmin ‖x − w_k‖",
         fondo=SURFACE, borde=SUCCESS, tam=12, negrita=True)
    caja("l5", 1045, 1040, 290, 86, "Salida\nla clase de la ganadora:\napto / no apto + margen",
         fondo=NAVY, borde=NAVY, color="#ffffff", tam=12, negrita=True)
    caja("l6", 1375, 1040, 290, 86,
         "Prototipos aprendidos\napto ≈ 0.8 de requisitos\nno apto ≈ 0.1 – 0.25 · exactitud 0.983",
         fondo=SURFACE, borde=BORDER, tam=12, negrita=True)
    caja("l4", 645, 1150, 430, 66,
         "Aprendizaje de Kohonen (al entrenar)\nacierta: w ← w + α(x − w)  ·  falla: w ← w − α(x − w)",
         fondo=SURFACE, borde=ACCENT, tam=11, negrita=True)
    flecha("l1", "l2")
    flecha("l2", "l3")
    flecha("l3", "l5")
    flecha("l3", "l4", "entrenamiento")
    ancla("l2_ancla", 530, 1126)
    flecha("l4", "l2_ancla", "entrenamiento", "ajusta los pesos", puntos=[(560, 1183)])

    # Leyenda ---------------------------------------------------------------
    texto("ley_t", 30, 1250, 120, 24, "Leyenda:", color=INK, tam=12, negrita=True, alinear="left")
    leyenda = [
        ("flujo", "Flujo de datos"),
        ("conexion", "Conexiones entre capas"),
        ("inhibicion", "Inhibición lateral (−ε)"),
        ("excitacion", "Autoexcitación (+1)"),
        ("entrenamiento", "Entrenamiento"),
    ]
    for k, (tipo, etiqueta) in enumerate(leyenda):
        x = 120 + k * 260
        caja(f"ley_{tipo}_a", x, 1256, 2, 12, "", fondo="none", borde="none")
        caja(f"ley_{tipo}_b", x + 60, 1256, 2, 12, "", fondo="none", borde="none")
        flecha(f"ley_{tipo}_a", f"ley_{tipo}_b", tipo)
        texto(f"ley_{tipo}_t", x + 70, 1250, 180, 24, etiqueta, tam=12, alinear="left")
    texto("fuente", 30, 1290, 1660, 22,
          "Código: backend/app/services/red_competitiva/ (caracteristicas.py, modelo.py, "
          "competitiva.py, lvq.py, torneo.py) · Diagrama generado con docs/diagrama/generar_diagrama.py",
          tam=11, alinear="left")


# ---------------------------------------------------------------------------
# Geometría compartida
# ---------------------------------------------------------------------------

def _nodo(id_):
    return next(n for n in nodos if n["id"] == id_)


def _centro(n):
    return n["x"] + n["w"] / 2, n["y"] + n["h"] / 2


def _borde(n, hacia):
    """Punto del perímetro de n en dirección al punto `hacia`."""
    cx, cy = _centro(n)
    dx, dy = hacia[0] - cx, hacia[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    if n["forma"] == "ellipse":
        rx, ry = n["w"] / 2, n["h"] / 2
        t = 1 / math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2)
    else:
        tx = (n["w"] / 2) / abs(dx) if dx else math.inf
        ty = (n["h"] / 2) / abs(dy) if dy else math.inf
        t = min(tx, ty)
    return cx + dx * t, cy + dy * t


def _recorrido(a):
    """Lista de puntos de la flecha: borde de origen, quiebres y borde de destino."""
    if not a["puntos"]:
        return list(_segmento(a))
    o, d = _nodo(a["origen"]), _nodo(a["destino"])
    inicio = _borde(o, a["puntos"][0])
    fin = _borde(d, a["puntos"][-1]) if d["w"] > 2 else _centro(d)
    return [inicio, *a["puntos"], fin]


def _segmento(a):
    o, d = _nodo(a["origen"]), _nodo(a["destino"])
    co, cd = _centro(o), _centro(d)
    if d["w"] <= 2:  # ancla: se llega a su centro exacto
        return _borde(o, cd), cd
    if a["tipo"] == "inhibicion":
        # Dos flechas por par: se desplazan a cada lado para que no se encimen
        nx, ny = cd[1] - co[1], -(cd[0] - co[0])
        largo = math.hypot(nx, ny) or 1
        co = (co[0] + 7 * nx / largo, co[1] + 7 * ny / largo)
        cd = (cd[0] + 7 * nx / largo, cd[1] + 7 * ny / largo)
        return _borde_desde(o, co, cd), _borde_desde(d, cd, co)
    return _borde(o, cd), _borde(d, co)


def _borde_desde(n, desde, hacia):
    cx, cy = _centro(n)
    ox, oy = desde[0] - cx, desde[1] - cy
    p = _borde({**n, "x": n["x"] + ox, "y": n["y"] + oy}, hacia)
    return p


# ---------------------------------------------------------------------------
# Salida SVG
# ---------------------------------------------------------------------------

def _ajustar(linea: str, tam: int, ancho: float) -> list[str]:
    """Parte una línea en varias para que quepa en `ancho` píxeles (aprox.)."""
    maximo = max(8, int(ancho / (tam * 0.56)))
    if len(linea) <= maximo:
        return [linea]
    partes, actual = [], ""
    for palabra in linea.split(" "):
        if actual and len(actual) + 1 + len(palabra) > maximo:
            partes.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    return partes + [actual]


def _svg_texto(n) -> str:
    lineas = []
    negritas = []
    for i, linea in enumerate(n["texto"].split("\n")):
        trozos = _ajustar(linea, n["tam"], n["w"] - 20)
        lineas += trozos
        negritas += [n["negrita"] and (i == 0 or n.get("titulo"))] * len(trozos)
    tam = n["tam"]
    alto_linea = tam * 1.35
    if n["alinear"] == "left":
        x, ancla = n["x"] + 10, "start"
    else:
        x, ancla = n["x"] + n["w"] / 2, "middle"
    y0 = n["y"] + n["h"] / 2 - alto_linea * (len(lineas) - 1) / 2
    partes = []
    for i, linea in enumerate(lineas):
        peso = "700" if negritas[i] else "400"
        partes.append(
            f'<text x="{x:.1f}" y="{y0 + i * alto_linea:.1f}" font-size="{tam}" '
            f'font-weight="{peso}" fill="{n["color"]}" text-anchor="{ancla}" '
            f'dominant-baseline="central">{escape(linea)}</text>'
        )
    return "".join(partes)


def svg() -> str:
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {ALTO}" '
        f'width="{ANCHO}" height="{ALTO}" font-family="Inter, Helvetica, Arial, sans-serif">',
        "<defs>",
    ]
    for tipo, e in ESTILO_ARISTA.items():
        out.append(
            f'<marker id="punta-{tipo}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
            f'fill="{e["color"]}"/></marker>'
        )
    out.append("</defs>")
    out.append(f'<rect width="{ANCHO}" height="{ALTO}" fill="{FONDO}"/>')

    def dibujar_nodo(n):
        if n["fondo"] != "none" or n["borde"] != "none":
            guiones = ' stroke-dasharray="6 4"' if n["discontinuo"] else ""
            borde = n["borde"] if n["borde"] != "none" else "none"
            fondo = n["fondo"] if n["fondo"] != "none" else "none"
            if n["forma"] == "ellipse":
                cx, cy = _centro(n)
                out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{n["w"] / 2}" ry="{n["h"] / 2}" '
                           f'fill="{fondo}" stroke="{borde}" stroke-width="1.5"{guiones}/>')
            else:
                out.append(f'<rect x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" '
                           f'rx="{n["redondeo"]}" fill="{fondo}" stroke="{borde}" '
                           f'stroke-width="1.5"{guiones}/>')
        if n["texto"]:
            out.append(_svg_texto(n))

    def dibujar_arista(a):
        e = ESTILO_ARISTA[a["tipo"]]
        guiones = ' stroke-dasharray="6 4"' if e["guiones"] else ""
        punta = f' marker-end="url(#punta-{a["tipo"]})"' if e["punta"] else ""
        if a["origen"] == a["destino"]:
            n = _nodo(a["origen"])
            cx, cy = _centro(n)
            r = n["w"] / 2
            x1, y1 = cx - r * 0.5, cy - r * 0.87
            x2, y2 = cx + r * 0.5, cy - r * 0.87
            out.append(f'<path d="M{x1:.1f},{y1:.1f} C{cx - r:.1f},{cy - r * 2:.1f} '
                       f'{cx + r:.1f},{cy - r * 2:.1f} {x2:.1f},{y2:.1f}" fill="none" '
                       f'stroke="{e["color"]}" stroke-width="{e["ancho"]}"{punta}/>')
            out.append(f'<text x="{cx}" y="{cy - r * 1.95:.1f}" font-size="12" font-weight="700" '
                       f'fill="{e["color"]}" text-anchor="middle">{escape(a["etiqueta"])}</text>')
            return
        puntos = _recorrido(a)
        trazo = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
        out.append(f'<polyline points="{trazo}" fill="none" stroke="{e["color"]}" '
                   f'stroke-width="{e["ancho"]}" stroke-linejoin="round"{guiones}{punta}/>')
        if a["etiqueta"]:
            # Etiqueta en el tramo más largo
            tramos = list(zip(puntos, puntos[1:]))
            (x1, y1), (x2, y2) = max(tramos, key=lambda t: math.dist(*t))
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ancho = 7 * len(a["etiqueta"]) + 12
            out.append(f'<rect x="{mx - ancho / 2:.1f}" y="{my - 10:.1f}" width="{ancho}" height="20" '
                       f'rx="4" fill="{FONDO}"/>')
            out.append(f'<text x="{mx:.1f}" y="{my:.1f}" font-size="11" font-weight="700" '
                       f'fill="{e["color"]}" text-anchor="middle" dominant-baseline="central">'
                       f'{escape(a["etiqueta"])}</text>')

    # Bandas y títulos primero, luego aristas, luego el resto de nodos
    fondos = [n for n in nodos if n["id"].startswith(("col_", "banda_"))]
    for n in fondos:
        dibujar_nodo(n)
    for a in aristas:
        if a["tipo"] in ("conexion",):
            dibujar_arista(a)
    for n in nodos:
        if n not in fondos:
            dibujar_nodo(n)
    for a in aristas:
        if a["tipo"] != "conexion":
            dibujar_arista(a)
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Salida draw.io
# ---------------------------------------------------------------------------

def _html(n) -> str:
    lineas = [escape(l) for l in n["texto"].split("\n")]
    if n["negrita"] and lineas:
        lineas[0] = f"<b>{lineas[0]}</b>"
    return "<br>".join(lineas)


def drawio() -> str:
    celdas = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for n in nodos:
        estilo = [
            "ellipse" if n["forma"] == "ellipse" else "rounded=1",
            "whiteSpace=wrap", "html=1",
            f"fillColor={n['fondo']}", f"strokeColor={n['borde']}",
            f"fontColor={n['color']}", f"fontSize={n['tam']}", "fontFamily=Helvetica",
            f"align={n['alinear']}", "verticalAlign=middle",
        ]
        if n["forma"] != "ellipse":
            estilo.append(f"arcSize={min(40, int(n['redondeo'] * 100 / max(min(n['w'], n['h']), 1)))}")
            estilo.append("absoluteArcSize=0")
        if n["alinear"] == "left":
            estilo.append("spacingLeft=8")
        if n["discontinuo"]:
            estilo.append("dashed=1")
        if n["negrita"] and len(n["texto"].split("\n")) == 1:
            estilo.append("fontStyle=1")
        celdas.append(
            f'<mxCell id="{n["id"]}" value="{escape(_html(n), {chr(34): "&quot;"})}" '
            f'style="{";".join(estilo)};" vertex="1" parent="1">'
            f'<mxGeometry x="{n["x"]:.1f}" y="{n["y"]:.1f}" width="{n["w"]:.1f}" '
            f'height="{n["h"]:.1f}" as="geometry"/></mxCell>'
        )
    for k, a in enumerate(aristas):
        e = ESTILO_ARISTA[a["tipo"]]
        estilo = [
            "html=1", f"strokeColor={e['color']}", f"strokeWidth={e['ancho']}",
            f"endArrow={'block' if e['punta'] else 'none'}", "endFill=1",
            f"fontColor={e['color']}", "fontStyle=1", "fontSize=11", "labelBackgroundColor=" + FONDO,
        ]
        if e["guiones"]:
            estilo.append("dashed=1")
        if a["origen"] == a["destino"]:
            estilo.append("edgeStyle=orthogonalEdgeStyle;loop=1")
            geometria = '<mxGeometry relative="1" as="geometry"/>'
        else:
            estilo.append("rounded=0")
            puntos = _recorrido(a)
            (x1, y1), (x2, y2) = puntos[0], puntos[-1]
            intermedios = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in puntos[1:-1])
            geometria = (
                f'<mxGeometry relative="1" as="geometry">'
                f'<mxPoint x="{x1:.1f}" y="{y1:.1f}" as="sourcePoint"/>'
                f'<mxPoint x="{x2:.1f}" y="{y2:.1f}" as="targetPoint"/>'
                + (f'<Array as="points">{intermedios}</Array>' if intermedios else "")
                + "</mxGeometry>"
            )
        celdas.append(
            f'<mxCell id="arista{k}" value="{escape(a["etiqueta"], {chr(34): "&quot;"})}" '
            f'style="{";".join(estilo)};" edge="1" parent="1" source="{a["origen"]}" '
            f'target="{a["destino"]}">{geometria}</mxCell>'
        )
    modelo = (
        f'<mxGraphModel dx="{ANCHO}" dy="{ALTO}" grid="1" gridSize="10" guides="1" tooltips="1" '
        f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{ANCHO}" '
        f'pageHeight="{ALTO}" background="{FONDO}" math="0" shadow="0"><root>'
        + "".join(celdas)
        + "</root></mxGraphModel>"
    )
    return (
        '<mxfile host="CVScope" type="device">'
        '<diagram id="red-competitiva" name="Red neuronal competitiva">'
        + modelo
        + "</diagram></mxfile>"
    )


def main() -> None:
    construir()
    (SALIDA / "red_competitiva.svg").write_text(svg(), encoding="utf-8")
    (SALIDA / "red_competitiva.drawio").write_text(drawio(), encoding="utf-8")
    print(f"{len(nodos)} nodos y {len(aristas)} aristas -> red_competitiva.svg y red_competitiva.drawio")


if __name__ == "__main__":
    main()
