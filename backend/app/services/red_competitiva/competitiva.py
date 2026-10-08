"""
Capa competitiva MAXNET (winner-take-all con inhibición lateral).

Es la capa recurrente de la red de Hamming, la red competitiva clásica
(Hagan, Neural Network Design, cap. 16; Lippmann, 1987):

  - Hay una neurona por hoja de vida que compite.
  - Cada neurona arranca con una activación positiva a_i(0) que viene de la
    capa de evaluación (la fuerza s_i que asigna la red siamesa):
        a_i(0) = exp(s_i - max_j s_j)            -> en (0, 1]
  - En cada iteración cada neurona se refuerza a sí misma (peso +1) e inhibe
    a las demás (peso -epsilon), con activación lineal positiva (poslin):
        a_i(t+1) = max(0, a_i(t) - epsilon * sum_{j != i} a_j(t))
    con 0 < epsilon < 1 / (S - 1), siendo S el número de neuronas.
  - Las neuronas débiles se apagan (llegan a 0) y la competencia termina
    cuando solo queda una activa: la ganadora.

Con S = 2 es un duelo entre dos hojas de vida. La probabilidad que se
reporta es softmax(s), que para un duelo coincide con sigmoide(s_A - s_B).
"""

import numpy as np

MAX_ITERACIONES = 1000


def epsilon_por_defecto(n_neuronas: int) -> float:
    """Inhibición lateral: la mitad del máximo que garantiza convergencia."""
    return 0.5 / max(n_neuronas - 1, 1)


def activaciones_iniciales(fuerzas: np.ndarray) -> np.ndarray:
    fuerzas = np.asarray(fuerzas, dtype=np.float64)
    return np.exp(fuerzas - fuerzas.max())


def probabilidades(fuerzas: np.ndarray) -> np.ndarray:
    """Probabilidad de que cada neurona gane la competencia (softmax)."""
    a = activaciones_iniciales(fuerzas)
    return a / a.sum()


def maxnet(fuerzas, epsilon: float | None = None, max_iteraciones: int = MAX_ITERACIONES) -> dict:
    """
    Ejecuta la competencia entre S neuronas.

    Returns:
      dict con: ganador (índice), iteraciones, epsilon, probabilidades,
      trayectoria (lista de activaciones por iteración, incluida la inicial).
    """
    fuerzas = np.asarray(fuerzas, dtype=np.float64)
    n = len(fuerzas)
    if n == 0:
        raise ValueError("MAXNET necesita al menos una neurona")
    epsilon = epsilon_por_defecto(n) if epsilon is None else epsilon
    if n > 1 and not 0 < epsilon < 1 / (n - 1):
        raise ValueError(f"epsilon debe estar en (0, {1 / (n - 1):.4f}) para {n} neuronas")

    a = activaciones_iniciales(fuerzas)
    trayectoria = [a.copy()]
    iteraciones = 0
    while np.count_nonzero(a) > 1 and iteraciones < max_iteraciones:
        activas = a[a > 0]
        if np.ptp(activas) <= 1e-12 * activas.max():
            # Empate exacto: la inhibición las apaga al mismo ritmo y ninguna
            # ganaría nunca; gana la primera sembrada.
            break
        siguiente = np.maximum(0.0, a - epsilon * (a.sum() - a))
        iteraciones += 1
        if not siguiente.any():
            # Las que quedaban se apagaron en el mismo paso: gana la más activa.
            break
        a = siguiente
        trayectoria.append(a.copy())

    return {
        "ganador": int(np.argmax(a)),
        "iteraciones": iteraciones,
        "epsilon": float(epsilon),
        "probabilidades": probabilidades(fuerzas),
        "trayectoria": trayectoria,
    }


def podio(fuerzas, top: int = 5) -> list[int]:
    """
    Top `top` por competencias sucesivas: la ganadora de cada MAXNET ocupa el
    siguiente puesto y se retira; las demás vuelven a competir.
    """
    restantes = list(range(len(fuerzas)))
    fuerzas = np.asarray(fuerzas, dtype=np.float64)
    puestos = []
    while restantes and len(puestos) < top:
        ganador = restantes[maxnet(fuerzas[restantes])["ganador"]]
        puestos.append(ganador)
        restantes.remove(ganador)
    return puestos
