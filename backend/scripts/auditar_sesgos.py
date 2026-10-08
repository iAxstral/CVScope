"""
Auditoría de sesgos con contrafactuales.

A cada hoja de vida del dataset de ranking se le cambia SOLO un dato personal
(nombre, ciudad, género de la profesión o edad) y se mide cuánto cambia:
  - la fuerza que le asigna la red competitiva, y
  - el puntaje del evaluador por palabras clave.

Si el sistema es justo frente a esos datos, el cambio debe ser 0.

Uso (desde backend/):
    python scripts/auditar_sesgos.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.datasets import cargar_ranking, requisitos_por_clave  # noqa: E402
from app.services.evaluador_requisitos import evaluar_cv  # noqa: E402
from app.services.red_competitiva.servicio import cargar_modelo  # noqa: E402
from app.services.red_competitiva.caracteristicas import extraer  # noqa: E402


def _cambiar_nombre(texto: str) -> str:
    nombre = texto.split(".")[0]
    return texto.replace(nombre, "Wilson Mosquera Palacios", 1)


def _cambiar_ciudad(texto: str) -> str:
    for ciudad in ("Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Pereira",
                   "Manizales", "Cartagena"):
        texto = texto.replace(f" en {ciudad}.", " en Quibdó.")
    return texto


def _version_femenina(texto: str) -> str:
    return texto.replace("Profesional", "Ingeniera y profesional", 1)


def _version_masculina(texto: str) -> str:
    return texto.replace("Profesional", "Ingeniero y profesional", 1)


def _agregar_edad(texto: str) -> str:
    return texto.replace("Perfil:", "Edad: 58 años. Estado civil: casada. Perfil:", 1)


# (nombre, versión A, versión B): solo cambia el dato indicado entre A y B
CONTRAFACTUALES = [
    ("nombre", lambda t: t, _cambiar_nombre),
    ("ciudad", lambda t: t, _cambiar_ciudad),
    ("género", _version_masculina, _version_femenina),
    ("edad y estado civil", lambda t: t, _agregar_edad),
]


def main() -> None:
    red, _ = cargar_modelo()
    filas = cargar_ranking()
    print(f"Hojas de vida auditadas: {len(filas)}\n")
    print(f"{'Dato cambiado':<22}{'Δ fuerza red (máx)':>20}{'Δ puntaje base (máx)':>24}")
    for nombre, version_a, version_b in CONTRAFACTUALES:
        delta_red = delta_base = 0.0
        for fila in filas:
            requisitos = requisitos_por_clave(fila["rol"])
            texto = fila["hoja_de_vida_texto"]
            original, variante = version_a(texto), version_b(texto)
            assert original != variante, f"El contrafactual '{nombre}' no cambió {fila['id']}"
            f0 = float(red.puntaje(extraer(original, requisitos))[0])
            f1 = float(red.puntaje(extraer(variante, requisitos))[0])
            b0 = evaluar_cv(original, requisitos)["score"]
            b1 = evaluar_cv(variante, requisitos)["score"]
            delta_red = max(delta_red, abs(f1 - f0))
            delta_base = max(delta_base, abs(b1 - b0))
        print(f"{nombre:<22}{delta_red:>20.4f}{delta_base:>24.4f}")


if __name__ == "__main__":
    main()
