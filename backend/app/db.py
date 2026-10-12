"""
Conexión a la base de datos.

Por defecto usa un archivo SQLite (backend/cvscope.db), así el proyecto corre
sin instalar nada. Para PostgreSQL basta con definir DATABASE_URL, por
ejemplo: postgresql://usuario:clave@localhost:5432/cvscope
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

RUTA_SQLITE = Path(__file__).resolve().parent.parent / "cvscope.db"
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{RUTA_SQLITE}"

_es_sqlite = DATABASE_URL.startswith("sqlite")
engine = create_engine(
    DATABASE_URL,
    # SQLite: FastAPI atiende peticiones en varios hilos
    connect_args={"check_same_thread": False} if _es_sqlite else {},
    pool_pre_ping=not _es_sqlite,
)
SesionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
