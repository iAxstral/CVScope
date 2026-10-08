"""
Red neuronal comparadora (siamesa) implementada con NumPy.

Ambas hojas de vida pasan por la MISMA red (pesos compartidos), que produce
un puntaje escalar de "fuerza" s(x). La probabilidad de que A gane a B es:

    P(A > B) = sigmoide(s(A) - s(B))

Esto garantiza que el duelo sea consistente: P(A > B) = 1 - P(B > A), y que
una hoja de vida nunca "empate" consigo misma (P = 0.5).

Arquitectura de s(x):  entrada -> 64 (ReLU) -> 32 (ReLU) -> 1
Pérdida: entropía cruzada binaria sobre pares (enfoque tipo RankNet).
Optimizador: Adam con regularización L2.
"""

from pathlib import Path

import numpy as np

CAPAS_OCULTAS = (64, 32)


def _sigmoide(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


class RedCompetitiva:
    def __init__(self, dim_entrada: int, capas_ocultas=CAPAS_OCULTAS, semilla: int = 0):
        rng = np.random.default_rng(semilla)
        tamanos = [dim_entrada, *capas_ocultas, 1]
        self.pesos: list[np.ndarray] = []
        self.sesgos: list[np.ndarray] = []
        for entrada, salida in zip(tamanos, tamanos[1:]):
            # Inicialización He, adecuada para ReLU
            self.pesos.append(rng.normal(0, np.sqrt(2.0 / entrada), (entrada, salida)).astype(np.float32))
            self.sesgos.append(np.zeros(salida, dtype=np.float32))
        self._adam_t = 0
        self._adam_m = [np.zeros_like(p) for p in self.parametros()]
        self._adam_v = [np.zeros_like(p) for p in self.parametros()]

    # ------------------------------------------------------------------ uso

    def parametros(self) -> list[np.ndarray]:
        return [*self.pesos, *self.sesgos]

    def puntaje(self, x: np.ndarray) -> np.ndarray:
        """Fuerza s(x) de cada fila de x. Devuelve un arreglo 1D."""
        return self._adelante(np.atleast_2d(x))[0][:, 0]

    def probabilidad(self, x_a: np.ndarray, x_b: np.ndarray) -> np.ndarray:
        """P(A gana a B) para cada par de filas."""
        return _sigmoide(self.puntaje(x_a) - self.puntaje(x_b))

    # -------------------------------------------------------- entrenamiento

    def _adelante(self, x: np.ndarray):
        activaciones = [x]
        h = x
        ultima = len(self.pesos) - 1
        for i, (w, b) in enumerate(zip(self.pesos, self.sesgos)):
            z = h @ w + b
            h = z if i == ultima else np.maximum(z, 0)
            activaciones.append(h)
        return h, activaciones

    def _atras(self, activaciones, grad_salida: np.ndarray):
        """Gradientes de los parámetros dado dL/ds (forma (n, 1))."""
        grads_w = [None] * len(self.pesos)
        grads_b = [None] * len(self.sesgos)
        delta = grad_salida
        for i in range(len(self.pesos) - 1, -1, -1):
            grads_w[i] = activaciones[i].T @ delta
            grads_b[i] = delta.sum(axis=0)
            if i > 0:
                delta = (delta @ self.pesos[i].T) * (activaciones[i] > 0)
        return grads_w, grads_b

    def paso(self, x_a, x_b, y, tasa=1e-3, l2=1e-4) -> float:
        """
        Un paso de descenso de gradiente sobre un lote de duelos.
        y = 1 si A es mejor que B, 0 si B es mejor que A.
        Devuelve la pérdida media del lote.
        """
        n = len(y)
        s_a, act_a = self._adelante(x_a)
        s_b, act_b = self._adelante(x_b)
        p = _sigmoide(s_a[:, 0] - s_b[:, 0])
        eps = 1e-7
        perdida = -np.mean(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))

        # dL/d(s_a - s_b) = p - y ; s_a recibe +, s_b recibe -
        g = ((p - y) / n).astype(np.float32)[:, None]
        gw_a, gb_a = self._atras(act_a, g)
        gw_b, gb_b = self._atras(act_b, -g)
        grads = [wa + wb + l2 * w for wa, wb, w in zip(gw_a, gw_b, self.pesos)]
        grads += [ba + bb for ba, bb in zip(gb_a, gb_b)]
        self._adam(grads, tasa)
        return float(perdida)

    def _adam(self, grads, tasa, b1=0.9, b2=0.999, eps=1e-8):
        self._adam_t += 1
        for param, g, m, v in zip(self.parametros(), grads, self._adam_m, self._adam_v):
            m *= b1
            m += (1 - b1) * g
            v *= b2
            v += (1 - b2) * g * g
            m_hat = m / (1 - b1 ** self._adam_t)
            v_hat = v / (1 - b2 ** self._adam_t)
            param -= (tasa * m_hat / (np.sqrt(v_hat) + eps)).astype(param.dtype)

    # -------------------------------------------------------- persistencia

    def guardar(self, ruta: Path, **metadatos) -> None:
        arrays = {f"w{i}": w for i, w in enumerate(self.pesos)}
        arrays |= {f"b{i}": b for i, b in enumerate(self.sesgos)}
        arrays |= {f"meta_{k}": np.array(v) for k, v in metadatos.items()}
        np.savez_compressed(ruta, **arrays)

    @classmethod
    def cargar(cls, ruta: Path) -> tuple["RedCompetitiva", dict]:
        datos = np.load(ruta)
        n_capas = sum(1 for k in datos.files if k.startswith("w"))
        pesos = [datos[f"w{i}"] for i in range(n_capas)]
        red = cls(pesos[0].shape[0], tuple(w.shape[1] for w in pesos[:-1]))
        red.pesos = pesos
        red.sesgos = [datos[f"b{i}"] for i in range(n_capas)]
        metadatos = {k[len("meta_"):]: datos[k].item() for k in datos.files if k.startswith("meta_")}
        return red, metadatos
