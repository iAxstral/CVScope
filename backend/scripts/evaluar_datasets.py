"""
Mide el evaluador de requisitos contra los dos datasets:

  - Selección: exactitud, precisión, recall y F1 de la decisión apto/no apto,
    y exactitud por requisito.
  - Ranking: precisión@5 (cuántos del top 5 real recupera el sistema) por rol.

Uso (desde backend/):
    python scripts/evaluar_datasets.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.datasets import cargar_ranking, cargar_seleccion, requisitos_por_clave  # noqa: E402
from app.services.evaluador_requisitos import evaluar_cv  # noqa: E402

TOP_N = 5


def evaluar_seleccion() -> None:
    filas = cargar_seleccion()
    vp = fp = fn = vn = 0
    req_ok = req_total = 0

    for fila in filas:
        requisitos = requisitos_por_clave(fila["rol"])
        resultado = evaluar_cv(fila["hoja_de_vida_texto"], requisitos)
        predicho = resultado["estado"] == "apto"
        real = fila["apto"]
        vp += predicho and real
        fp += predicho and not real
        fn += (not predicho) and real
        vn += (not predicho) and (not real)

        reales = set(fila["requisitos_cumplidos"])
        for item in resultado["evaluacion"]:
            req_total += 1
            req_ok += item["cumple"] == (item["requisito"] in reales)

    exactitud = (vp + vn) / len(filas)
    precision = vp / (vp + fp) if vp + fp else 0
    recall = vp / (vp + fn) if vp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

    print(f"== Dataset de selección ({len(filas)} hojas de vida)")
    print(f"   Apto/no apto  -> exactitud {exactitud:.3f} | precisión {precision:.3f} | recall {recall:.3f} | F1 {f1:.3f}")
    print(f"   Matriz        -> VP {vp}  FP {fp}  FN {fn}  VN {vn}")
    print(f"   Por requisito -> exactitud {req_ok / req_total:.3f} ({req_ok}/{req_total})")


def evaluar_ranking() -> None:
    filas = cargar_ranking()
    roles = sorted({f["rol"] for f in filas})
    print(f"\n== Dataset de ranking ({len(filas)} hojas de vida, top {TOP_N} por rol)")
    total = 0.0
    for rol in roles:
        del_rol = [f for f in filas if f["rol"] == rol]
        requisitos = requisitos_por_clave(rol)

        reales = sorted(
            (f for f in del_rol if f["posicion_referencia"]),
            key=lambda f: f["posicion_referencia"],
        )[:TOP_N]

        evaluados = []
        for f in del_rol:
            r = evaluar_cv(f["hoja_de_vida_texto"], requisitos)
            if r["estado"] == "apto":
                evaluados.append((r["score"], f["id"]))
        predichos = [cv_id for _, cv_id in sorted(evaluados, key=lambda t: (-t[0], t[1]))[:TOP_N]]

        aciertos = len({f["id"] for f in reales} & set(predichos))
        total += aciertos / TOP_N
        print(f"   {rol:<10} precisión@{TOP_N} = {aciertos}/{TOP_N}")
    print(f"   Promedio   precisión@{TOP_N} = {total / len(roles):.3f}")


if __name__ == "__main__":
    evaluar_seleccion()
    evaluar_ranking()
