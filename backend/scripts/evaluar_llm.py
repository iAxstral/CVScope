"""
Compara el evaluador con Gemini contra el evaluador por palabras clave en una
muestra del dataset de selección (requiere OPENAI_API_KEY en backend/.env).

Uso (desde backend/):
    python scripts/evaluar_llm.py            # 40 hojas de vida
    python scripts/evaluar_llm.py --n 120
"""

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.services.datasets import cargar_seleccion, requisitos_por_clave  # noqa: E402
from app.services.evaluador_requisitos import evaluar_cv  # noqa: E402
from app.services.llm_service import LLMNoDisponible, evaluar_compatibilidad, llm_disponible  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=40, help="Cantidad de hojas de vida a evaluar")
    parser.add_argument("--pausa", type=float, default=1.0, help="Segundos entre llamadas (cuota)")
    args = parser.parse_args()

    if not llm_disponible():
        sys.exit("No hay API key de Gemini: define OPENAI_API_KEY en backend/.env")

    filas = cargar_seleccion()
    muestra = random.Random(2026).sample(filas, min(args.n, len(filas)))
    aciertos = {"llm": 0, "palabras_clave": 0}
    req_ok = {"llm": 0, "palabras_clave": 0}
    req_total = errores = 0

    for i, fila in enumerate(muestra, start=1):
        requisitos = requisitos_por_clave(fila["rol"])
        try:
            llm = evaluar_compatibilidad(fila["hoja_de_vida_texto"], requisitos)
        except LLMNoDisponible as exc:
            errores += 1
            print(f"[{i}/{len(muestra)}] {fila['id']}: error -> {exc}")
            continue
        base = evaluar_cv(fila["hoja_de_vida_texto"], requisitos)
        reales = set(fila["requisitos_cumplidos"])
        for motor, r in (("llm", llm), ("palabras_clave", base)):
            aciertos[motor] += (r["estado"] == "apto") == fila["apto"]
            req_ok[motor] += sum(e["cumple"] == (e["requisito"] in reales) for e in r["evaluacion"])
        req_total += len(requisitos)
        print(f"[{i}/{len(muestra)}] {fila['id']}: llm={llm['estado']} base={base['estado']} real={'apto' if fila['apto'] else 'no_apto'}")
        time.sleep(args.pausa)

    n = len(muestra) - errores
    if not n:
        sys.exit("Ninguna evaluación terminó correctamente")
    print(f"\nHojas de vida evaluadas: {n} (errores: {errores})")
    print("                        Gemini   Palabras clave")
    print(f"Exactitud apto/no apto  {aciertos['llm'] / n:>6.3f}   {aciertos['palabras_clave'] / n:>14.3f}")
    print(f"Exactitud por requisito {req_ok['llm'] / req_total:>6.3f}   {req_ok['palabras_clave'] / req_total:>14.3f}")


if __name__ == "__main__":
    main()
