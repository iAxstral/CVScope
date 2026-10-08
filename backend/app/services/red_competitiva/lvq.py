"""
Capa competitiva que aprende: LVQ1 (Learning Vector Quantization, Kohonen).

A diferencia de MAXNET (pesos fijos), aquí los pesos SÍ se aprenden:

  - Cada neurona tiene un vector de pesos w_k (un "prototipo") y una clase
    (apto o no apto).
  - Ante una hoja de vida x, las neuronas compiten: gana la más cercana,
    k* = argmin_k ||x - w_k||  (winner-take-all).
  - Regla de aprendizaje de Kohonen, solo para la ganadora:
        si su clase es la correcta:   w_k* <- w_k* + alfa · (x - w_k*)   (se acerca)
        si no:                        w_k* <- w_k* - alfa · (x - w_k*)   (se aleja)
    con alfa decreciendo linealmente a lo largo del entrenamiento.

La clase de la neurona ganadora es el veredicto de selección (apto / no apto).
"""

from pathlib import Path

import numpy as np

CLASES = ("no_apto", "apto")


class CapaLVQ:
    def __init__(self, prototipos: np.ndarray, clases: np.ndarray, pesos_rasgos: np.ndarray):
        self.prototipos = prototipos.astype(np.float32)
        self.clases = clases.astype(np.int8)
        # Escala de cada característica antes de medir distancias (da más peso a
        # los rasgos explícitos frente a los 1024 n-gramas)
        self.pesos_rasgos = pesos_rasgos.astype(np.float32)

    # ------------------------------------------------------------------ uso

    def _escalar(self, x: np.ndarray) -> np.ndarray:
        return np.atleast_2d(x) * self.pesos_rasgos

    def distancias(self, x: np.ndarray) -> np.ndarray:
        """Distancia de cada fila de x a cada neurona: forma (n, K)."""
        diferencia = self._escalar(x)[:, None, :] - self.prototipos[None, :, :]
        return np.sqrt((diferencia ** 2).sum(axis=2))

    def competir(self, x: np.ndarray) -> dict:
        """
        Competencia para una hoja de vida. Devuelve la neurona ganadora, su
        clase y un margen de confianza (0 = empate entre clases, 1 = claro).
        """
        d = self.distancias(x)[0]
        ganadora = int(np.argmin(d))
        clase = int(self.clases[ganadora])
        mas_cercana_otra = float(d[self.clases != clase].min())
        margen = (mas_cercana_otra - d[ganadora]) / (mas_cercana_otra + d[ganadora] + 1e-9)
        return {
            "neurona_ganadora": ganadora,
            "veredicto": CLASES[clase],
            "distancia": float(d[ganadora]),
            "distancia_otra_clase": mas_cercana_otra,
            "margen": float(margen),
        }

    def predecir(self, x: np.ndarray) -> np.ndarray:
        """Clase (0 = no apto, 1 = apto) para cada fila de x."""
        return self.clases[np.argmin(self.distancias(x), axis=1)]

    # -------------------------------------------------------- entrenamiento

    @classmethod
    def entrenar(
        cls,
        x: np.ndarray,
        y: np.ndarray,
        prototipos_por_clase: int = 3,
        epocas: int = 40,
        alfa_inicial: float = 0.05,
        pesos_rasgos: np.ndarray | None = None,
        semilla: int = 2026,
    ) -> "CapaLVQ":
        rng = np.random.default_rng(semilla)
        pesos_rasgos = np.ones(x.shape[1], np.float32) if pesos_rasgos is None else pesos_rasgos
        xs = x * pesos_rasgos

        # Inicialización: muestras al azar de cada clase
        prototipos, clases = [], []
        for c in (0, 1):
            idx = rng.choice(np.flatnonzero(y == c), size=prototipos_por_clase, replace=False)
            prototipos.append(xs[idx])
            clases += [c] * prototipos_por_clase
        capa = cls(np.vstack(prototipos), np.array(clases), np.ones(x.shape[1], np.float32))

        total = epocas * len(xs)
        paso = 0
        for _ in range(epocas):
            for i in rng.permutation(len(xs)):
                alfa = alfa_inicial * (1 - paso / total)
                d = ((xs[i] - capa.prototipos) ** 2).sum(axis=1)
                k = int(np.argmin(d))  # neurona ganadora
                signo = 1.0 if capa.clases[k] == y[i] else -1.0
                capa.prototipos[k] += signo * alfa * (xs[i] - capa.prototipos[k])
                paso += 1

        capa.pesos_rasgos = pesos_rasgos.astype(np.float32)
        return capa

    # -------------------------------------------------------- persistencia

    def guardar(self, ruta: Path, **metadatos) -> None:
        np.savez_compressed(
            ruta,
            prototipos=self.prototipos,
            clases=self.clases,
            pesos_rasgos=self.pesos_rasgos,
            **{f"meta_{k}": np.array(v) for k, v in metadatos.items()},
        )

    @classmethod
    def cargar(cls, ruta: Path) -> tuple["CapaLVQ", dict]:
        datos = np.load(ruta)
        capa = cls(datos["prototipos"], datos["clases"], datos["pesos_rasgos"])
        meta = {k[len("meta_"):]: datos[k].item() for k in datos.files if k.startswith("meta_")}
        return capa, meta
