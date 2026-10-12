"""
Genera el diagrama de la red neuronal competitiva de CVScope como tres láminas
con estilo de tablero (tarjetas, notas adhesivas y gráficas), a partir de una
sola definición:

  red_competitiva.drawio        -> editable en draw.io / diagrams.net (una página por lámina)
  lamina_1_vision_general.svg   -> de la hoja de vida a la ganadora
  lamina_2_maxnet.svg           -> cómo compiten las neuronas, con un duelo real
  lamina_3_entrenamiento.svg    -> cómo aprenden la capa de evaluación y la LVQ

Uso (desde la raíz del repo):
    python docs/diagrama/generar_diagrama.py          # .drawio y .svg
    python docs/diagrama/generar_diagrama.py --png    # además .png (usa Chrome o Edge)
"""

import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

SALIDA = Path(__file__).resolve().parent

# Paleta de la aplicación (frontend/src/index.css)
NAVY = "#17244d"
PRIMARY = "#22346b"
PRIMARY_SOFT = "#e7ebf5"
ACCENT = "#e8a63d"
SUCCESS = "#2f9e64"
SUCCESS_SOFT = "#e2f4ea"
DANGER = "#d64550"
DANGER_SOFT = "#fbe3e5"
INK = "#17203a"
INK_SOFT = "#5c6b8a"
BORDER = "#dfe4ee"
GRIS_BARRA = "#c9d0e2"
SURFACE = "#ffffff"
SURFACE_ALT = "#f7f9fc"
FONDO = "#f3f5f9"
PUNTOS = "#d5dbe7"
NOTA_AMARILLA = "#ffe9a6"
NOTA_VERDE = "#cdeedb"

SANS = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'IBM Plex Mono', Consolas, monospace"


def L(texto, tam=13, negrita=False, color=INK, mono=False):
    """Una línea de texto con su formato."""
    return (texto, tam, negrita, color, mono)


def parrafo(texto, tam=13, negrita=False, color=INK, mono=False):
    return [L(t, tam, negrita, color, mono) for t in texto.split("\n")]


# ---------------------------------------------------------------------------
# Modelo del tablero
# ---------------------------------------------------------------------------

class Lamina:
    def __init__(self, id_, nombre, archivo, ancho, alto):
        self.id, self.nombre, self.archivo = id_, nombre, archivo
        self.ancho, self.alto = ancho, alto
        self.elementos: list[dict] = []
        self._ids: dict[str, dict] = {}

    def caja(self, id_, x, y, w, h, lineas=(), *, fondo=SURFACE, borde="none", grosor=1.5,
             radio=12, forma="rect", sombra=False, alinear="center", vertical="middle",
             margen=12, rotacion=0, guiones=False, capa=2):
        n = dict(clase="nodo", id=id_, x=x, y=y, w=w, h=h, lineas=list(lineas), fondo=fondo,
                 borde=borde, grosor=grosor, radio=radio, forma=forma, sombra=sombra,
                 alinear=alinear, vertical=vertical, margen=margen, rotacion=rotacion,
                 guiones=guiones, capa=capa)
        self.elementos.append(n)
        self._ids[id_] = n

    def texto(self, id_, x, y, w, h, lineas, alinear="left", vertical="middle", capa=3):
        self.caja(id_, x, y, w, h, lineas, fondo="none", alinear=alinear, vertical=vertical,
                  margen=0, capa=capa)

    def flecha(self, origen, destino, *, color=NAVY, grosor=2, guiones=False, fin=True,
               inicio=False, puntos=(), etiqueta="", capa=1):
        self.elementos.append(dict(clase="arista", origen=origen, destino=destino, color=color,
                                   grosor=grosor, guiones=guiones, fin=fin, inicio=inicio,
                                   puntos=list(puntos), etiqueta=etiqueta, capa=capa))

    def linea(self, puntos, color=BORDER, grosor=1, guiones=False, capa=1):
        self.flecha(puntos[0], puntos[-1], color=color, grosor=grosor, guiones=guiones, fin=False,
                    puntos=puntos[1:-1], capa=capa)

    def bucle(self, nodo, angulo, etiqueta="+1", color=SUCCESS, grosor=2):
        """Autoconexión de una neurona hacia `angulo` grados (90 = arriba)."""
        self.elementos.append(dict(clase="bucle", nodo=nodo, angulo=angulo, etiqueta=etiqueta,
                                   color=color, grosor=grosor, capa=1))

    def nodo(self, id_):
        return self._ids[id_]

    def ordenados(self):
        return sorted(self.elementos, key=lambda e: e["capa"])  # sorted es estable


def _centro(n):
    return n["x"] + n["w"] / 2, n["y"] + n["h"] / 2


def _borde(n, hacia):
    """Punto del perímetro de n en dirección al punto `hacia`."""
    cx, cy = _centro(n)
    dx, dy = hacia[0] - cx, hacia[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    if n["forma"] == "ellipse":
        t = 1 / math.sqrt((dx / (n["w"] / 2)) ** 2 + (dy / (n["h"] / 2)) ** 2)
    else:
        tx = (n["w"] / 2) / abs(dx) if dx else math.inf
        ty = (n["h"] / 2) / abs(dy) if dy else math.inf
        t = min(tx, ty)
    return cx + dx * t, cy + dy * t


def _recorrido(lam, a):
    """Puntos de la arista: extremo de origen, quiebres y extremo de destino."""
    def punto(ref):
        return ref if isinstance(ref, tuple) else _centro(lam.nodo(ref))

    o, d = a["origen"], a["destino"]
    siguiente = a["puntos"][0] if a["puntos"] else punto(d)
    anterior = a["puntos"][-1] if a["puntos"] else punto(o)
    inicio = o if isinstance(o, tuple) else _borde(lam.nodo(o), siguiente)
    fin = d if isinstance(d, tuple) else _borde(lam.nodo(d), anterior)
    return [inicio, *a["puntos"], fin]


def _geometria_bucle(lam, b):
    n = lam.nodo(b["nodo"])
    cx, cy = _centro(n)
    r = n["w"] / 2

    def polar(grados, radio):
        t = math.radians(b["angulo"] + grados)
        return cx + radio * math.cos(t), cy - radio * math.sin(t)

    return (polar(-28, r), polar(-42, 2.3 * r), polar(42, 2.3 * r), polar(28, r),
            polar(0, 1.55 * r + 13))


# ---------------------------------------------------------------------------
# Láminas
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


def encabezado(lam, titulo, subtitulo):
    lam.texto("titulo", 60, 34, 1180, 46, [L(titulo, 30, True, NAVY)])
    lam.texto("subtitulo", 60, 84, 1480, 26, [L(subtitulo, 16, False, INK_SOFT)])
    lam.caja("marca", 1300, 42, 240, 32, [L("CVScope · " + lam.nombre, 12, True, "#ffffff")],
             fondo=NAVY, radio=16, capa=3)


def pie(lam, texto):
    lam.texto("pie", 60, lam.alto - 42, 1480, 22, [L(texto, 12, False, INK_SOFT)])


def tarjeta(lam, id_, x, y, w, h, titulo="", subtitulo=""):
    lam.caja(id_, x, y, w, h, fondo=SURFACE, borde=BORDER, radio=18, sombra=True, capa=0)
    if titulo:
        lam.texto(id_ + "_t", x + 30, y + 22, w - 60, 30, [L(titulo, 18, True, INK)])
    if subtitulo:
        lam.texto(id_ + "_s", x + 30, y + 52, w - 60, 22, [L(subtitulo, 13, False, INK_SOFT)])


def nota(lam, id_, x, y, w, h, color, titulo, cuerpo, rotacion):
    lam.caja(id_, x, y, w, h, [L(titulo, 15, True, INK), *parrafo(cuerpo, 13, False, INK)],
             fondo=color, radio=4, sombra=True, alinear="left", vertical="top", margen=16,
             rotacion=rotacion)


def lamina_vision_general():
    lam = Lamina("vision", "visión general", "lamina_1_vision_general", 1600, 740)
    encabezado(lam, "Cómo decide CVScope quién gana",
               "Una red neuronal competitiva: cada hoja de vida es una neurona y compiten "
               "hasta que solo una queda activa.")
    etapas = [
        ("Hojas de vida", "Todas las que compiten por el rol\n(PDF · DOCX · TXT)\ny los requisitos del rol"),
        ("Anonimizar y\nvectorizar", "Sin datos personales; cada hoja\nde vida se vuelve un vector\nx ∈ ℝ¹⁰²⁶"),
        ("Capa de\nevaluación", "Red feedforward entrenada\n1026 → 64 → 32 → 1\nque da la fuerza s(x)"),
        ("Competencia\nMAXNET", "Se inhiben entre sí (−ε)\nhasta que solo una\nqueda activa"),
        ("Ganadora", "Ganadora, top 5 y torneo,\ncon la probabilidad de ganar\ny la explicación del duelo"),
    ]
    Y, H, W, PASO = 160, 350, 250, 310
    xs = [55 + k * PASO for k in range(len(etapas))]
    for k, (titulo, texto_pie) in enumerate(etapas):
        x = xs[k]
        lam.caja(f"etapa{k}", x, Y, W, H, fondo=SURFACE, borde=BORDER, radio=18, sombra=True, capa=0)
        lam.caja(f"num{k}", x + 20, Y + 22, 40, 40, [L(str(k + 1), 18, True, "#ffffff")],
                 fondo=ACCENT if k == 4 else NAVY, forma="ellipse")
        lam.texto(f"tit{k}", x + 72, Y + 18, W - 85, 48, parrafo(titulo, 17, True, INK))
        lam.texto(f"pie{k}", x + 15, Y + 262, W - 30, 72, parrafo(texto_pie, 13, False, INK_SOFT),
                  alinear="center")
        if k:
            lam.flecha(f"etapa{k - 1}", f"etapa{k}", grosor=3)

    # 1 · Hojas de vida: una pila de documentos
    x = xs[0]
    for i in range(3):
        dx, dy = x + 62 + i * 22, Y + 92 + i * 18
        lam.caja(f"doc{i}", dx, dy, 86, 112, fondo=SURFACE, borde=PRIMARY, radio=8, sombra=True)
    for j, ancho in enumerate([40, 58, 50, 58, 34]):
        lam.caja(f"doc_l{j}", x + 120, Y + 146 + j * 16, ancho, 7,
                 fondo=PRIMARY if j == 0 else PRIMARY_SOFT, radio=3)

    # 2 · Anonimizar y vectorizar: documento con datos tachados -> vector
    x = xs[1]
    lam.caja("anon", x + 30, Y + 100, 76, 110, fondo=SURFACE, borde=PRIMARY, radio=8, sombra=True)
    filas = [(True, 44), (False, 52), (False, 40), (True, 30), (False, 50), (False, 36)]
    for j, (tachado, ancho) in enumerate(filas):
        lam.caja(f"anon_l{j}", x + 42, Y + 114 + j * 15, ancho, 9 if tachado else 7,
                 fondo=INK if tachado else PRIMARY_SOFT, radio=2)
    lam.flecha((x + 114, Y + 155), (x + 152, Y + 155), grosor=2)
    tonos = [PRIMARY, "#5a6aa0", PRIMARY_SOFT, "#9aa6c8", PRIMARY_SOFT, PRIMARY, "#c3cbe0", PRIMARY_SOFT]
    for i, tono in enumerate(tonos):
        lam.caja(f"vec{i}", x + 162, Y + 98 + i * 16, 28, 15, fondo=tono, borde=SURFACE, grosor=1, radio=2)
    lam.texto("vec_t", x + 162, Y + 74, 28, 20, [L("x", 14, True, PRIMARY, True)], alinear="center")

    # 3 · Capa de evaluación: red feedforward en miniatura
    x = xs[2]
    cy = Y + 165
    capas = []
    for c, (cx, cuantas) in enumerate([(x + 45, 4), (x + 100, 4), (x + 155, 3)]):
        ids = []
        for k in range(cuantas):
            id_ = f"ff{c}_{k}"
            yk = cy + (k - (cuantas - 1) / 2) * 32
            lam.caja(id_, cx - 10, yk - 10, 20, 20, fondo=PRIMARY_SOFT, borde=PRIMARY, forma="ellipse")
            ids.append(id_)
        capas.append(ids)
    lam.caja("ff_s", x + 193, cy - 17, 34, 34, [L("s", 15, True, "#ffffff")], fondo=NAVY,
             forma="ellipse")
    capas.append(["ff_s"])
    for izq, der in zip(capas, capas[1:]):
        for a in izq:
            for b in der:
                lam.flecha(a, b, color="#c5cde0", grosor=1, fin=False)

    # 4 · Competencia MAXNET: tres neuronas que se inhiben
    x = xs[3]
    lam.caja("m1", x + 53, Y + 93, 50, 50, [L("1", 16, True, "#ffffff")], fondo=NAVY,
             borde=NAVY, forma="ellipse")
    lam.caja("m2", x + 147, Y + 93, 50, 50, [L("2", 16, True, PRIMARY)], borde=PRIMARY,
             grosor=2, forma="ellipse")
    lam.caja("m3", x + 100, Y + 165, 50, 50, [L("3", 16, True, PRIMARY)], borde=PRIMARY,
             grosor=2, forma="ellipse")
    for a, b in [("m1", "m2"), ("m1", "m3"), ("m2", "m3")]:
        lam.flecha(a, b, color=DANGER, grosor=1.8, guiones=True, inicio=True)
    lam.bucle("m1", 150, "")
    lam.bucle("m2", 30, "")
    lam.bucle("m3", 270, "")

    # 5 · Ganadora: podio
    x = xs[4]
    lam.texto("estrella", x + 103, Y + 90, 44, 44, [L("★", 32, False, ACCENT)], alinear="center")
    lam.caja("podio2", x + 57, Y + 168, 44, 60, [L("2", 16, True, PRIMARY)], fondo=PRIMARY_SOFT, radio=6)
    lam.caja("podio1", x + 103, Y + 138, 44, 90, [L("1", 18, True, "#ffffff")], fondo=ACCENT, radio=6)
    lam.caja("podio3", x + 149, Y + 188, 44, 40, [L("3", 16, True, PRIMARY)], fondo=PRIMARY_SOFT, radio=6)
    lam.caja("piso", x + 45, Y + 230, 160, 3, fondo=BORDER, radio=1)

    # Notas adhesivas
    nota(lam, "nota_sesgos", 120, 560, 300, 92, NOTA_AMARILLA, "Sin sesgos",
         "La red nunca ve nombre, edad,\nciudad, estado civil ni género.", -2)
    nota(lam, "nota_duelos", 650, 560, 310, 92, NOTA_AMARILLA, "Aprende de 4.512 duelos",
         "exactitud en duelos 0.959\nprecisión@5 0.80 (palabras clave: 0.70)", 1.5)
    nota(lam, "nota_lvq", 1150, 560, 340, 92, NOTA_VERDE, "+ capa LVQ: apto / no apto",
         "4 neuronas prototipo compiten y gana\nla más cercana · exactitud 0.983", -1.5)

    pie(lam, "Código: backend/app/services/red_competitiva/  ·  Detalle en la lámina 2 (MAXNET) "
             "y la lámina 3 (entrenamiento y LVQ)")
    return lam


def lamina_maxnet():
    lam = Lamina("maxnet", "MAXNET", "lamina_2_maxnet", 1600, 780)
    encabezado(lam, "La competencia: capa MAXNET",
               "Una neurona por hoja de vida. En cada iteración se refuerza a sí misma (+1) e "
               "inhibe a las demás (−ε).")

    # Izquierda: tres neuronas compitiendo
    tarjeta(lam, "izq", 55, 150, 700, 560, "Tres hojas de vida compitiendo",
            "La más fuerte arranca en 1: aᵢ(0) = exp(sᵢ − max s)")
    neuronas = [("n1", 240, 345, "HV 1", "a₁"), ("n2", 570, 345, "HV 2", "a₂"),
                ("n3", 405, 505, "HV 3", "a₃")]
    for id_, cx, cy, nombre, act in neuronas:
        activa = id_ == "n1"
        color = "#ffffff" if activa else PRIMARY
        lam.caja(id_, cx - 50, cy - 50, 100, 100, [L(nombre, 17, True, color), L(act, 15, False, color)],
                 fondo=NAVY if activa else SURFACE, borde=NAVY if activa else PRIMARY, grosor=2.5,
                 forma="ellipse", sombra=True)
    for a, b in [("n1", "n2"), ("n1", "n3"), ("n2", "n3")]:
        lam.flecha(a, b, color=DANGER, grosor=2.2, guiones=True, inicio=True, etiqueta="−ε")
    lam.bucle("n1", 160)
    lam.bucle("n2", 20)
    lam.bucle("n3", 270)
    lam.caja("regla", 85, 625, 640, 66,
             [L("Regla en cada iteración", 13, True, PRIMARY),
              L("aᵢ(t+1) = max(0, aᵢ(t) − ε · Σⱼ≠ᵢ aⱼ(t))   ·   0 < ε < 1/(S − 1)", 15, False, INK, True)],
             fondo=PRIMARY_SOFT)

    # Derecha: un duelo real, iteración por iteración
    s_a, s_b, eps = 23.4, 23.2, 0.5
    pasos = ejemplo_duelo(s_a, s_b, eps)
    prob = 100 / (1 + math.exp(-(s_a - s_b)))
    tarjeta(lam, "der", 805, 150, 740, 560, "Ejemplo real: duelo de 2 hojas de vida",
            f"Fuerzas de la capa de evaluación: s_A = {s_a} · s_B = {s_b} · ε = {eps}")
    x0, x1, y0, y1 = 905, 1475, 290, 545
    ultimo = len(pasos) - 1

    def px(t):
        return x0 + t * (x1 - x0) / ultimo

    def py(a):
        return y1 - a * (y1 - y0)

    for a in (0, 0.5, 1):
        lam.linea([(x0, py(a)), (x1, py(a))], color="#b9c2d6" if a == 0 else BORDER)
        lam.texto(f"eje_y{a}", x0 - 54, py(a) - 10, 42, 20, [L(f"{a:.2f}", 12, False, INK_SOFT)],
                  alinear="right")
    for t in range(len(pasos)):
        lam.texto(f"eje_x{t}", px(t) - 30, y1 + 10, 60, 20, [L(f"t = {t}", 12, False, INK_SOFT)],
                  alinear="center")
    lam.texto("eje_y_t", x0 - 54, y0 - 52, 200, 20, [L("activación aᵢ(t)", 12, True, INK_SOFT)])
    lam.texto("eje_x_t", x1 - 160, y1 + 34, 160, 20, [L("iteración", 12, True, INK_SOFT)],
              alinear="right")

    for serie, color in ((0, NAVY), (1, DANGER)):
        puntos = [(px(t), py(p[serie])) for t, p in enumerate(pasos)]
        lam.linea(puntos, color=color, grosor=3)
        for t, (x, y) in enumerate(puntos):
            lam.caja(f"p{serie}_{t}", x - 7, y - 7, 14, 14, fondo=color, borde=SURFACE, grosor=2,
                     forma="ellipse")
            valor = pasos[t][serie]
            if serie == 0:
                texto_v = f"{valor:.2f} · gana A" if t == ultimo else f"{valor:.2f}"
                if t == 0:  # a la derecha, para no tocar el título del eje
                    lam.texto(f"v{serie}_{t}", x + 12, y - 26, 60, 20, [L(texto_v, 12, True, NAVY)])
                else:
                    lam.texto(f"v{serie}_{t}", x - 60, y - 32, 120, 20, [L(texto_v, 12, True, NAVY)],
                              alinear="center")
            elif t == ultimo:
                lam.texto(f"v{serie}_{t}", x - 122, y - 30, 110, 20,
                          [L(f"{valor:.2f} · se apaga", 12, True, DANGER)], alinear="right")
            elif valor < 0.1:  # pegada al eje: la etiqueta va arriba
                lam.texto(f"v{serie}_{t}", x - 30, y - 32, 60, 20, [L(f"{valor:.2f}", 12, True, DANGER)],
                          alinear="center")
            else:
                lam.texto(f"v{serie}_{t}", x - 30, y + 12, 60, 20, [L(f"{valor:.2f}", 12, True, DANGER)],
                          alinear="center")

    chips = [(835, 210, [L("●  A: s = 23.4", 13, True, NAVY)]),
             (1062, 210, [L("●  B: s = 23.2", 13, True, DANGER)]),
             (1289, 226, [L(f"P(A gana) = σ(0.2) = {prob:.1f} %", 13, True, INK)])]
    for k, (x, w, lineas) in enumerate(chips):
        lam.caja(f"chip{k}", x, 622, w, 44, lineas, fondo=SURFACE_ALT, borde=BORDER, radio=22)

    pie(lam, "Código: backend/app/services/red_competitiva/competitiva.py  ·  El ejemplo se calcula "
             "con la misma regla que usa el backend")
    return lam


def lamina_entrenamiento():
    lam = Lamina("entrenamiento", "aprendizaje", "lamina_3_entrenamiento", 1600, 800)
    encabezado(lam, "Cómo aprende la red",
               "La capa de evaluación aprende de duelos entre hojas de vida; la capa LVQ aprende "
               "prototipos de «apto» y «no apto».")

    # Izquierda: entrenamiento de la capa de evaluación
    tarjeta(lam, "izq", 55, 150, 700, 600, "Capa de evaluación · entrenamiento",
            "Fuera de línea, con retropropagación escrita desde cero en NumPy")
    pasos = [
        ("Dataset de selección", "240 hojas de vida etiquetadas por rol"),
        ("4.512 duelos dentro de cada rol", "gana la de mayor puntaje de referencia; empate = 0.5"),
        ("Pérdida por pares", "P(A gana a B) = σ(s(A) − s(B)) con entropía cruzada"),
        ("Retropropagación", "Adam + regularización L2 · 40 épocas"),
    ]
    ys = [235 + k * 70 for k in range(len(pasos))]
    lam.linea([(108, ys[0] + 26), (108, ys[-1] + 26)], color=ACCENT, grosor=2, guiones=True)
    for k, ((titulo, detalle), y) in enumerate(zip(pasos, ys)):
        lam.caja(f"paso{k}", 90, y + 8, 36, 36, [L(str(k + 1), 15, True, "#ffffff")], fondo=ACCENT,
                 forma="ellipse")
        lam.texto(f"paso{k}_t", 145, y, 580, 52, [L(titulo, 15, True, INK), L(detalle, 13, False, INK_SOFT)])

    lam.texto("prueba_t", 85, 520, 640, 24,
              [L("Prueba con el dataset de ranking (la red nunca lo vio)", 15, True, INK)])
    metricas = [("Exactitud en duelos", 0.959, 0.934, "{:.3f}"), ("Precisión@5", 0.80, 0.70, "{:.2f}")]
    escala = 380
    for i, (nombre, red, base, formato) in enumerate(metricas):
        y = 565 + i * 70
        lam.texto(f"met{i}", 85, y, 170, 44, [L(nombre, 13, True, INK)])
        lam.caja(f"met{i}_red", 265, y + 2, escala * red, 18, fondo=NAVY, radio=4)
        lam.texto(f"met{i}_red_v", 265 + escala * red + 8, y, 60, 22, [L(formato.format(red), 12, True, NAVY)])
        lam.caja(f"met{i}_base", 265, y + 24, escala * base, 18, fondo=GRIS_BARRA, radio=4)
        lam.texto(f"met{i}_base_v", 265 + escala * base + 8, y + 22, 60, 22,
                  [L(formato.format(base), 12, False, INK_SOFT)])
    lam.caja("ley_red", 265, 711, 12, 12, fondo=NAVY, radio=2)
    lam.texto("ley_red_t", 283, 705, 150, 24, [L("Red competitiva", 12, False, INK_SOFT)])
    lam.caja("ley_base", 430, 711, 12, 12, fondo=GRIS_BARRA, radio=2)
    lam.texto("ley_base_t", 448, 705, 260, 24, [L("Palabras clave (línea base)", 12, False, INK_SOFT)])

    # Derecha: LVQ
    tarjeta(lam, "der", 805, 150, 740, 600, "Capa LVQ · competitiva y entrenada",
            "Gana el prototipo más cercano: k* = argmin ‖x − w_k‖ (winner-take-all)")
    x0, x1, y0, y1 = 895, 1475, 270, 560

    def px(fraccion):
        return x0 + fraccion * (x1 - x0)

    def py(anios):
        return y1 - anios / 12 * (y1 - y0)

    for f in (0, 0.25, 0.5, 0.75, 1):
        lam.linea([(px(f), y0), (px(f), y1)], color="#b9c2d6" if f == 0 else BORDER)
        lam.texto(f"lx{f}", px(f) - 30, y1 + 10, 60, 20, [L(f"{f:.0%}".replace("%", " %"), 12, False, INK_SOFT)],
                  alinear="center")
    for a in (0, 4, 8, 12):
        lam.linea([(x0, py(a)), (x1, py(a))], color="#b9c2d6" if a == 0 else BORDER)
        lam.texto(f"ly{a}", x0 - 50, py(a) - 10, 40, 20, [L(str(a), 12, False, INK_SOFT)], alinear="right")
    lam.texto("lx_t", x1 - 320, y1 + 34, 320, 20, [L("fracción de requisitos con evidencia", 12, True, INK_SOFT)],
              alinear="right")
    lam.texto("ly_t", x0 - 50, y0 - 40, 220, 20, [L("años de experiencia", 12, True, INK_SOFT)])

    umbral = px(0.66)
    lam.linea([(umbral, y0), (umbral, y1)], color=ACCENT, grosor=2, guiones=True)
    lam.texto("umbral_t", umbral + 8, y1 - 28, 170, 20, [L("umbral manual 66 %", 12, True, ACCENT)])

    prototipos = [(0, False, 0.12, 3.5), (1, False, 0.25, 10.0), (2, True, 0.77, 10.7), (3, True, 0.82, 3.7)]
    for k, apto, fraccion, anios in prototipos:
        color = SUCCESS if apto else DANGER
        cx, cy = px(fraccion), py(anios)
        lam.caja(f"proto{k}", cx - 17, cy - 17, 34, 34, [L(str(k), 14, True, "#ffffff")], fondo=color,
                 borde=SURFACE, grosor=2, forma="ellipse", sombra=True)
        lam.texto(f"proto{k}_t", cx + 24, cy - 11, 140, 22, [L("apto" if apto else "no apto", 13, True, color)])

    lam.caja("kohonen_ok", 835, 620, 330, 52,
             [L("Acierta → el prototipo se acerca", 13, True, SUCCESS), L("w ← w + α(x − w)", 13, False, INK, True)],
             fondo=SUCCESS_SOFT)
    lam.caja("kohonen_mal", 1185, 620, 330, 52,
             [L("Falla → el prototipo se aleja", 13, True, DANGER), L("w ← w − α(x − w)", 13, False, INK, True)],
             fondo=DANGER_SOFT)
    lam.texto("lvq_res", 835, 688, 680, 44,
              [L("Exactitud 0.983 · F1 0.988", 14, True, INK),
               L("Nadie le dio el umbral del 66 %: la frontera la aprendió de los datos.", 13, False, INK_SOFT)])

    pie(lam, "Código: red_competitiva/modelo.py y lvq.py  ·  Scripts: entrenar_red_competitiva.py, "
             "entrenar_lvq.py, validar_red.py")
    return lam


# ---------------------------------------------------------------------------
# Salida SVG
# ---------------------------------------------------------------------------

def _svg_texto(n) -> str:
    if not n["lineas"]:
        return ""
    alturas = [tam * 1.32 for _, tam, *_ in n["lineas"]]
    total = sum(alturas)
    if n["vertical"] == "top":
        y = n["y"] + n["margen"]
    else:
        y = n["y"] + (n["h"] - total) / 2
    if n["alinear"] == "left":
        x, ancla = n["x"] + n["margen"], "start"
    elif n["alinear"] == "right":
        x, ancla = n["x"] + n["w"] - n["margen"], "end"
    else:
        x, ancla = n["x"] + n["w"] / 2, "middle"
    partes = []
    for (texto, tam, negrita, color, mono), alto in zip(n["lineas"], alturas):
        familia = f' font-family="{MONO}"' if mono else ""
        partes.append(
            f'<text x="{x:.1f}" y="{y + alto / 2:.1f}" font-size="{tam}" '
            f'font-weight="{700 if negrita else 400}" fill="{color}" text-anchor="{ancla}" '
            f'dominant-baseline="central"{familia}>{escape(texto)}</text>')
        y += alto
    return "".join(partes)


def _marcador(color):
    return "m" + color.lstrip("#")


def svg(lam) -> str:
    colores = {e["color"] for e in lam.elementos if e["clase"] != "nodo"}
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lam.ancho} {lam.alto}" '
        f'width="{lam.ancho}" height="{lam.alto}" font-family="{SANS}">',
        "<defs><style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700"
        "&amp;family=IBM+Plex+Mono&amp;display=swap');</style>",
        '<filter id="sombra" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" '
        f'dy="4" stdDeviation="6" flood-color="{NAVY}" flood-opacity="0.12"/></filter>',
        '<pattern id="puntos" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<circle cx="2" cy="2" r="1.3" fill="{PUNTOS}"/></pattern>',
    ]
    for color in sorted(colores):
        out.append(f'<marker id="{_marcador(color)}" viewBox="0 0 10 10" refX="8" refY="5" '
                   f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
                   f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>')
    out.append("</defs>")
    out.append(f'<rect width="{lam.ancho}" height="{lam.alto}" fill="{FONDO}"/>')
    out.append(f'<rect width="{lam.ancho}" height="{lam.alto}" fill="url(#puntos)"/>')

    for e in lam.ordenados():
        if e["clase"] == "nodo":
            out.append(_svg_nodo(e))
        elif e["clase"] == "arista":
            out.append(_svg_arista(lam, e))
        else:
            out.append(_svg_bucle(lam, e))
    out.append("</svg>")
    return "\n".join(o for o in out if o)


def _svg_nodo(n) -> str:
    partes = []
    if n["fondo"] != "none" or n["borde"] != "none":
        trazo = (f' stroke="{n["borde"]}" stroke-width="{n["grosor"]}"' if n["borde"] != "none" else "")
        if n["guiones"]:
            trazo += ' stroke-dasharray="6 4"'
        sombra = ' filter="url(#sombra)"' if n["sombra"] else ""
        if n["forma"] == "ellipse":
            cx, cy = _centro(n)
            partes.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{n["w"] / 2:.1f}" '
                          f'ry="{n["h"] / 2:.1f}" fill="{n["fondo"]}"{trazo}{sombra}/>')
        else:
            partes.append(f'<rect x="{n["x"]:.1f}" y="{n["y"]:.1f}" width="{n["w"]:.1f}" '
                          f'height="{n["h"]:.1f}" rx="{n["radio"]}" fill="{n["fondo"]}"{trazo}{sombra}/>')
    partes.append(_svg_texto(n))
    contenido = "".join(partes)
    if n["rotacion"]:
        cx, cy = _centro(n)
        return f'<g transform="rotate({n["rotacion"]} {cx:.1f} {cy:.1f})">{contenido}</g>'
    return contenido


def _svg_etiqueta(x, y, texto, color) -> str:
    ancho = 8 * len(texto) + 14
    return (f'<rect x="{x - ancho / 2:.1f}" y="{y - 11:.1f}" width="{ancho}" height="22" rx="11" '
            f'fill="{SURFACE}"/><text x="{x:.1f}" y="{y:.1f}" font-size="14" font-weight="700" '
            f'fill="{color}" text-anchor="middle" dominant-baseline="central">{escape(texto)}</text>')


def _svg_arista(lam, a) -> str:
    puntos = _recorrido(lam, a)
    trazo = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
    extra = ' stroke-dasharray="7 5"' if a["guiones"] else ""
    marcador = f"url(#{_marcador(a['color'])})"
    if a["fin"]:
        extra += f' marker-end="{marcador}"'
    if a["inicio"]:
        extra += f' marker-start="{marcador}"'
    out = (f'<polyline points="{trazo}" fill="none" stroke="{a["color"]}" stroke-width="{a["grosor"]}" '
           f'stroke-linejoin="round" stroke-linecap="round"{extra}/>')
    if a["etiqueta"]:
        tramos = list(zip(puntos, puntos[1:]))
        (xa, ya), (xb, yb) = max(tramos, key=lambda t: math.dist(*t))
        out += _svg_etiqueta((xa + xb) / 2, (ya + yb) / 2, a["etiqueta"], a["color"])
    return out


def _svg_bucle(lam, b) -> str:
    p0, c1, c2, p3, etiqueta = _geometria_bucle(lam, b)
    out = (f'<path d="M{p0[0]:.1f},{p0[1]:.1f} C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} '
           f'{p3[0]:.1f},{p3[1]:.1f}" fill="none" stroke="{b["color"]}" stroke-width="{b["grosor"]}" '
           f'marker-end="url(#{_marcador(b["color"])})"/>')
    if b["etiqueta"]:
        out += (f'<text x="{etiqueta[0]:.1f}" y="{etiqueta[1]:.1f}" font-size="14" font-weight="700" '
                f'fill="{b["color"]}" text-anchor="middle" dominant-baseline="central">'
                f'{escape(b["etiqueta"])}</text>')
    return out


# ---------------------------------------------------------------------------
# Salida draw.io
# ---------------------------------------------------------------------------

def _attr(texto: str) -> str:
    return escape(texto, {'"': "&quot;"})


def _html(n) -> str:
    lineas = []
    for texto, tam, negrita, color, mono in n["lineas"]:
        cara = "IBM Plex Mono" if mono else "Inter"
        linea = f'<font style="font-size:{tam}px" color="{color}" face="{cara}">{escape(texto)}</font>'
        lineas.append(f"<b>{linea}</b>" if negrita else linea)
    return "<br>".join(lineas)


def _celda_nodo(n) -> str:
    estilo = ["ellipse" if n["forma"] == "ellipse" else "rounded=1", "whiteSpace=wrap", "html=1",
              f"fillColor={n['fondo']}", f"strokeColor={n['borde']}", f"strokeWidth={n['grosor']}",
              "fontFamily=Inter", f"align={n['alinear']}", f"verticalAlign={n['vertical']}",
              f"spacing=0", f"spacingLeft={n['margen']}", f"spacingRight={n['margen']}",
              f"spacingTop={n['margen'] if n['vertical'] == 'top' else 0}"]
    if n["forma"] != "ellipse":
        estilo += ["absoluteArcSize=1", f"arcSize={n['radio'] * 2}"]
    if n["sombra"]:
        estilo.append("shadow=1")
    if n["guiones"]:
        estilo.append("dashed=1")
    if n["rotacion"]:
        estilo.append(f"rotation={n['rotacion']}")
    return (f'<mxCell id="{n["id"]}" value="{_attr(_html(n))}" style="{";".join(estilo)};" '
            f'vertex="1" parent="1"><mxGeometry x="{n["x"]:.1f}" y="{n["y"]:.1f}" '
            f'width="{n["w"]:.1f}" height="{n["h"]:.1f}" as="geometry"/></mxCell>')


def _celda_arista(lam, a, k) -> str:
    estilo = ["html=1", "rounded=0", "edgeStyle=none", f"strokeColor={a['color']}",
              f"strokeWidth={a['grosor']}", f"endArrow={'block' if a['fin'] else 'none'}", "endFill=1",
              f"startArrow={'block' if a['inicio'] else 'none'}", "startFill=1",
              f"fontColor={a['color']}", "fontStyle=1", "fontSize=14", f"labelBackgroundColor={SURFACE}"]
    if a["guiones"]:
        estilo.append("dashed=1")
    puntos = _recorrido(lam, a)
    enlaces = ""
    if not isinstance(a["origen"], tuple):
        enlaces += f' source="{a["origen"]}"'
    if not isinstance(a["destino"], tuple):
        enlaces += f' target="{a["destino"]}"'
    intermedios = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in puntos[1:-1])
    return (f'<mxCell id="arista{k}" value="{_attr(a["etiqueta"])}" style="{";".join(estilo)};" '
            f'edge="1" parent="1"{enlaces}><mxGeometry relative="1" as="geometry">'
            f'<mxPoint x="{puntos[0][0]:.1f}" y="{puntos[0][1]:.1f}" as="sourcePoint"/>'
            f'<mxPoint x="{puntos[-1][0]:.1f}" y="{puntos[-1][1]:.1f}" as="targetPoint"/>'
            + (f'<Array as="points">{intermedios}</Array>' if intermedios else "")
            + "</mxGeometry></mxCell>")


def _celda_bucle(lam, b, k) -> str:
    _, c1, c2, _, _ = _geometria_bucle(lam, b)
    estilo = ["html=1", "curved=1", f"strokeColor={b['color']}", f"strokeWidth={b['grosor']}",
              "endArrow=block", "endFill=1", f"fontColor={b['color']}", "fontStyle=1", "fontSize=14",
              "labelBackgroundColor=none"]
    return (f'<mxCell id="bucle{k}" value="{_attr(b["etiqueta"])}" style="{";".join(estilo)};" '
            f'edge="1" parent="1" source="{b["nodo"]}" target="{b["nodo"]}">'
            f'<mxGeometry relative="1" as="geometry"><Array as="points">'
            f'<mxPoint x="{c1[0]:.1f}" y="{c1[1]:.1f}"/><mxPoint x="{c2[0]:.1f}" y="{c2[1]:.1f}"/>'
            f"</Array></mxGeometry></mxCell>")


def drawio(laminas) -> str:
    paginas = []
    for lam in laminas:
        celdas = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
        for k, e in enumerate(lam.ordenados()):
            if e["clase"] == "nodo":
                celdas.append(_celda_nodo(e))
            elif e["clase"] == "arista":
                celdas.append(_celda_arista(lam, e, k))
            else:
                celdas.append(_celda_bucle(lam, e, k))
        paginas.append(
            f'<diagram id="{lam.id}" name="{_attr(lam.nombre.capitalize())}">'
            f'<mxGraphModel dx="{lam.ancho}" dy="{lam.alto}" grid="1" gridSize="12" guides="1" '
            f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{lam.ancho}" pageHeight="{lam.alto}" background="{FONDO}" math="0" '
            f'shadow="0"><root>' + "".join(celdas) + "</root></mxGraphModel></diagram>")
    return '<mxfile host="CVScope" type="device">' + "".join(paginas) + "</mxfile>"


# ---------------------------------------------------------------------------
# PNG (opcional): captura del .svg con Chrome o Edge sin interfaz
# ---------------------------------------------------------------------------

def _navegador() -> str | None:
    candidatos = [os.environ.get("CHROME"), shutil.which("chrome"), shutil.which("google-chrome"),
                  shutil.which("chromium"), shutil.which("msedge"),
                  r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                  r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    return next((c for c in candidatos if c and Path(c).exists()), None)


def png(lam) -> None:
    navegador = _navegador()
    if not navegador:
        sys.exit("No se encontró Chrome ni Edge; define la variable CHROME con su ruta.")
    origen = SALIDA / f"{lam.archivo}.svg"
    subprocess.run([navegador, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", f"--window-size={lam.ancho},{lam.alto}",
                    "--virtual-time-budget=5000", f"--screenshot={SALIDA / f'{lam.archivo}.png'}",
                    origen.as_uri()], check=True, capture_output=True)


def main() -> None:
    laminas = [lamina_vision_general(), lamina_maxnet(), lamina_entrenamiento()]
    for lam in laminas:
        (SALIDA / f"{lam.archivo}.svg").write_text(svg(lam), encoding="utf-8")
        if "--png" in sys.argv:
            png(lam)
    (SALIDA / "red_competitiva.drawio").write_text(drawio(laminas), encoding="utf-8")
    print(f"{len(laminas)} láminas -> red_competitiva.drawio y "
          + ", ".join(f"{lam.archivo}.svg" for lam in laminas)
          + (" (+ .png)" if "--png" in sys.argv else ""))


if __name__ == "__main__":
    main()
