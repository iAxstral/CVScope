"""
Las pruebas usan una base de datos SQLite temporal y vacía, para no tocar
backend/cvscope.db. Debe definirse antes de importar la aplicación.
Para probar contra PostgreSQL: DATABASE_URL=postgresql://... pytest
"""

import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="cvscope-tests-")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(_tmp, 'pruebas.db')}")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _sesion_de_prueba(request):
    """
    Las pruebas funcionales corren con una sesión simulada. Las pruebas de
    autenticación se marcan con @pytest.mark.sin_sesion para probar el flujo real.
    """
    from app.dependencias import usuario_actual
    from app.main import app

    if request.node.get_closest_marker("sin_sesion"):
        yield
        return
    app.dependency_overrides[usuario_actual] = lambda: {
        "id": 0, "email": "pruebas@cvscope.co", "nombre": "Pruebas",
    }
    yield
    app.dependency_overrides.pop(usuario_actual, None)
