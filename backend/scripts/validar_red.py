"""
Validación estadística de la red competitiva frente a la línea base.

1. Validación cruzada de 5 particiones (dataset de selección): se entrena la
   red 5 veces, cada vez dejando fuera un 20 % distinto de las hojas de vida
   (estratificado por rol), y se mide la exactitud en los duelos de ese 20 %.
2. Bootstrap con 2.000 remuestreos del dataset de prueba (ranking) usando el
   modelo entrenado: intervalos de confianza del 95 % para la exactitud en
   duelos, la precisión@5 y la DIFERENCIA red − palabras clave. Si el
   intervalo de la diferencia no incluye el 0, la mejora es estadísticamente
   distinta de cero con esos datos.

Uso (desde backend/):
    python scripts/validar_red.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import entrenar_red_competitiva as ent  # noqa: E402

from app.services.datasets import cargar_ranking, cargar_seleccion  # noqa: E402
from app.services.red_competitiva.competitiva import podio  # noqa: E402
from app.services.red_competitiva.modelo import RedCompetitiva  # noqa: E402

PARTICIONES = 5
REMUESTREOS = 2000


def particiones(cvs: list[dict], rng: np.random.Generator) -> list[list[dict]]:
    grupos = [[] for _ in range(PARTICIONES)]
    for rol in sorted({c["rol"] for c in cvs}):
        del_rol = [c for c in cvs if c["rol"] == rol]
        for i, k in enumerate(rng.permutation(len(del_rol))):
            grupos[i % PARTICIONES].append(del_rol[k])
    return grupos


def validacion_cruzada() -> None:
    rng = np.random.default_rng(ent.SEMILLA)
    cvs = ent.preparar(cargar_seleccion())
    grupos = particiones(cvs, rng)
    red_acc, base_acc = [], []
    for k in range(PARTICIONES):
        prueba = grupos[k]
        entrenamiento = [c for j, g in enumerate(grupos) if j != k for c in g]
        red = ent.entrenar(ent.pares(entrenamiento, con_empates=True), rng, verbose=False)
        duelos = ent.pares(prueba)
        red_acc.append(ent.exactitud_red(red, duelos))
        base_acc.append(ent.exactitud_base(duelos))
        print(f"   partición {k + 1}: red {red_acc[-1]:.3f} · palabras clave {base_acc[-1]:.3f}")
    print(f"== Validación cruzada ({PARTICIONES} particiones, exactitud en duelos)")
    print(f"   Red competitiva: {np.mean(red_acc):.3f} ± {np.std(red_acc):.3f}")
    print(f"   Palabras clave:  {np.mean(base_acc):.3f} ± {np.std(base_acc):.3f}")


def _metricas(cvs: list[dict], fuerza) -> tuple[float, float]:
    """Exactitud en duelos y precisión@5 promedio por rol para una muestra."""
    duelos = ent.pares(cvs)
    aciertos = [((fuerza(a) > fuerza(b)) == (a["ref"] > b["ref"])) and fuerza(a) != fuerza(b)
                for a, b in duelos]
    p5 = []
    for rol in sorted({c["rol"] for c in cvs}):
        del_rol = [c for c in cvs if c["rol"] == rol]
        real = {id(c) for c in sorted(del_rol, key=lambda c: -c["ref"])[:ent.TOP]}
        elegidos = {id(del_rol[i]) for i in podio([fuerza(c) for c in del_rol], ent.TOP)}
        p5.append(len(real & elegidos) / ent.TOP)
    return float(np.mean(aciertos)), float(np.mean(p5))


def bootstrap() -> None:
    red, _ = RedCompetitiva.cargar(ent.RUTA_MODELO)
    cvs = ent.preparar(cargar_ranking())
    for c in cvs:
        c["fuerza"] = float(red.puntaje(c["x"])[0])

    def fuerza_red(c):
        return c["fuerza"]

    def fuerza_base(c):
        return c["base"]

    rng = np.random.default_rng(ent.SEMILLA)
    por_rol = {rol: [c for c in cvs if c["rol"] == rol] for rol in sorted({c["rol"] for c in cvs})}
    resultados = {"red": [], "base": []}
    for _ in range(REMUESTREOS):
        # Remuestreo con reemplazo dentro de cada rol (copias para distinguir repetidos)
        muestra = [dict(c) for del_rol in por_rol.values()
                   for c in (del_rol[i] for i in rng.integers(0, len(del_rol), len(del_rol)))]
        resultados["red"].append(_metricas(muestra, fuerza_red))
        resultados["base"].append(_metricas(muestra, fuerza_base))

    red_m, base_m = np.array(resultados["red"]), np.array(resultados["base"])
    observado_red, observado_base = _metricas(cvs, fuerza_red), _metricas(cvs, fuerza_base)

    def intervalo(valores):
        return np.percentile(valores, 2.5), np.percentile(valores, 97.5)

    print(f"\n== Bootstrap sobre la prueba ({REMUESTREOS} remuestreos, intervalos del 95 %)")
    for i, nombre in enumerate(["Exactitud en duelos", "Precisión@5"]):
        lo_r, hi_r = intervalo(red_m[:, i])
        lo_b, hi_b = intervalo(base_m[:, i])
        lo_d, hi_d = intervalo(red_m[:, i] - base_m[:, i])
        veredicto = "mejora significativa" if lo_d > 0 else "no se puede afirmar que mejore"
        print(f"   {nombre}")
        print(f"     Red:            {observado_red[i]:.3f}  [{lo_r:.3f}, {hi_r:.3f}]")
        print(f"     Palabras clave: {observado_base[i]:.3f}  [{lo_b:.3f}, {hi_b:.3f}]")
        print(f"     Diferencia:     {observado_red[i] - observado_base[i]:+.3f}  [{lo_d:+.3f}, {hi_d:+.3f}] -> {veredicto}")


if __name__ == "__main__":
    validacion_cruzada()
    bootstrap()
