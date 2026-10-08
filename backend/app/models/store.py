"""
Acceso a roles y candidatos guardados en la base de datos.

Los métodos devuelven diccionarios, igual que el almacenamiento en memoria
que había antes, así el resto del código no depende de SQLAlchemy.
"""

from sqlalchemy import select

from app.db import Base, SesionLocal, engine
from app.models.tablas import Candidato, Rol
from app.schemas.candidato import CandidatoCreate, EstadoEvaluacion
from app.schemas.rol import RolCreate

ROLES_INICIALES = [
    RolCreate(
        nombre="Full Stack Developer",
        clave="fullstack",
        requisitos=["JavaScript/TypeScript", "React o similar", "Node.js o backend equivalente", "Bases de datos SQL/NoSQL"],
    ),
    RolCreate(
        nombre="Analista de Recursos Humanos",
        clave="rrhh",
        requisitos=["Gestión de procesos de selección", "Manejo de nómina", "Comunicación interpersonal"],
    ),
    RolCreate(
        nombre="Ejecutivo de Ventas",
        clave="ventas",
        requisitos=["Experiencia en ventas B2B/B2C", "Manejo de CRM", "Negociación"],
    ),
    RolCreate(
        nombre="Especialista en Marketing Digital",
        clave="marketing",
        requisitos=["SEO/SEM", "Gestión de redes sociales", "Analítica web (Google Analytics)"],
    ),
]


def _a_dict(fila) -> dict:
    return {c.name: getattr(fila, c.name) for c in fila.__table__.columns}


class RolStore:
    def list_all(self) -> list[dict]:
        with SesionLocal() as s:
            return [_a_dict(r) for r in s.scalars(select(Rol).order_by(Rol.id))]

    def get(self, rol_id: int) -> dict | None:
        with SesionLocal() as s:
            rol = s.get(Rol, rol_id)
            return _a_dict(rol) if rol else None

    def get_by_clave(self, clave: str) -> dict | None:
        with SesionLocal() as s:
            rol = s.scalar(select(Rol).where(Rol.clave == clave))
            return _a_dict(rol) if rol else None

    def create(self, data: RolCreate) -> dict:
        with SesionLocal() as s:
            rol = Rol(**data.model_dump())
            s.add(rol)
            s.commit()
            return _a_dict(rol)


class CandidatoStore:
    def list_all(self) -> list[dict]:
        with SesionLocal() as s:
            return [_a_dict(c) for c in s.scalars(select(Candidato).order_by(Candidato.id))]

    def list_by_rol(self, rol_id: int) -> list[dict]:
        with SesionLocal() as s:
            consulta = select(Candidato).where(Candidato.rol_id == rol_id).order_by(Candidato.id)
            return [_a_dict(c) for c in s.scalars(consulta)]

    def get(self, candidato_id: int) -> dict | None:
        with SesionLocal() as s:
            candidato = s.get(Candidato, candidato_id)
            return _a_dict(candidato) if candidato else None

    def create(self, data: CandidatoCreate) -> dict:
        with SesionLocal() as s:
            candidato = Candidato(
                nombre=data.nombre,
                email=data.email,
                hoja_de_vida_texto=data.hoja_de_vida_texto,
                rol_id=data.rol_id,
                estado=EstadoEvaluacion.PENDIENTE.value,
                requisitos_cumplidos=[],
                requisitos_faltantes=[],
            )
            s.add(candidato)
            s.commit()
            return _a_dict(candidato)

    def update(self, candidato_id: int, **campos) -> dict | None:
        with SesionLocal() as s:
            candidato = s.get(Candidato, candidato_id)
            if candidato is None:
                return None
            for campo, valor in campos.items():
                setattr(candidato, campo, getattr(valor, "value", valor))
            s.commit()
            return _a_dict(candidato)


def init_db() -> None:
    """Crea las tablas si no existen y carga los roles iniciales la primera vez."""
    Base.metadata.create_all(engine)
    with SesionLocal() as s:
        if s.scalar(select(Rol.id).limit(1)) is None:
            s.add_all(Rol(**r.model_dump()) for r in ROLES_INICIALES)
            s.commit()


init_db()
rol_store = RolStore()
candidato_store = CandidatoStore()
