"""
Límite de intentos fallidos de inicio de sesión (contra fuerza bruta).

Se cuentan los fallos por (dirección IP, correo) en una ventana deslizante;
al llegar al máximo, el login responde 429 hasta que pasa la ventana. Un
inicio de sesión correcto borra el contador. Vive en memoria del proceso: con
varias réplicas de la API cada una lleva su propia cuenta.

Variables de entorno (opcionales):
  LOGIN_MAX_INTENTOS    -> fallos permitidos antes de bloquear (por defecto 5)
  LOGIN_VENTANA_SEGUNDOS -> duración de la ventana y del bloqueo (por defecto 900)
"""

import os
import threading
import time
from collections import defaultdict, deque

MAX_INTENTOS = int(os.getenv("LOGIN_MAX_INTENTOS", "5"))
VENTANA = int(os.getenv("LOGIN_VENTANA_SEGUNDOS", "900"))


class LimitadorDeIntentos:
    def __init__(self, max_intentos: int = MAX_INTENTOS, ventana: int = VENTANA):
        self.max_intentos = max_intentos
        self.ventana = ventana
        self._fallos: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._cerrojo = threading.Lock()

    @staticmethod
    def _clave(ip: str, email: str) -> tuple[str, str]:
        return ip, email.strip().lower()

    def _purgar(self, fallos: deque[float], ahora: float) -> None:
        while fallos and fallos[0] <= ahora - self.ventana:
            fallos.popleft()

    def segundos_de_espera(self, ip: str, email: str, ahora: float | None = None) -> int:
        """0 si puede intentar; si no, los segundos que faltan para el siguiente intento."""
        ahora = time.monotonic() if ahora is None else ahora
        with self._cerrojo:
            fallos = self._fallos.get(self._clave(ip, email))
            if not fallos:
                return 0
            self._purgar(fallos, ahora)
            if len(fallos) < self.max_intentos:
                return 0
            return max(1, int(fallos[0] + self.ventana - ahora) + 1)

    def registrar_fallo(self, ip: str, email: str, ahora: float | None = None) -> None:
        ahora = time.monotonic() if ahora is None else ahora
        with self._cerrojo:
            fallos = self._fallos[self._clave(ip, email)]
            self._purgar(fallos, ahora)
            fallos.append(ahora)

    def registrar_exito(self, ip: str, email: str) -> None:
        with self._cerrojo:
            self._fallos.pop(self._clave(ip, email), None)

    def reiniciar(self) -> None:
        with self._cerrojo:
            self._fallos.clear()


limitador_login = LimitadorDeIntentos()
