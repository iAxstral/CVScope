"""
Las pruebas usan una base de datos SQLite temporal y vacía, para no tocar
backend/cvscope.db. Debe definirse antes de importar la aplicación.
"""

import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="cvscope-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp, 'pruebas.db')}"
