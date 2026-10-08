from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    clave: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    requisitos: Mapped[list] = mapped_column(JSON)
    umbral_apto: Mapped[float] = mapped_column(Float, default=0.66)


class Candidato(Base):
    __tablename__ = "candidatos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255))
    hoja_de_vida_texto: Mapped[str] = mapped_column(Text)
    rol_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)
    rol_nombre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    requisitos_cumplidos: Mapped[list] = mapped_column(JSON, default=list)
    requisitos_faltantes: Mapped[list] = mapped_column(JSON, default=list)
    explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    nombre: Mapped[str] = mapped_column(String(150))
    hash_contrasena: Mapped[str] = mapped_column(String(255))
