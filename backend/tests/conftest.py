"""
Las pruebas usan una base de datos SQLite temporal y vacía, para no tocar
backend/cvscope.db. Debe definirse antes de importar la aplicación.
Para probar contra PostgreSQL: DATABASE_URL=postgresql://... pytest
"""

import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="cvscope-tests-")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(_tmp, 'pruebas.db')}")
