from app.schemas.rol import RolCreate
from app.schemas.candidato import CandidatoCreate, EstadoEvaluacion


class RolStore:
    def __init__(self):
        self._roles: dict[int, dict] = {}
        self._next_id = 1
        self._seed()

    def _seed(self):
        ejemplos = [
            RolCreate(
                nombre="Full Stack Developer",
                requisitos=["JavaScript/TypeScript", "React o similar", "Node.js o backend equivalente", "Bases de datos SQL/NoSQL"],
            ),
            RolCreate(
                nombre="Analista de Recursos Humanos",
                requisitos=["Gestión de procesos de selección", "Manejo de nómina", "Comunicación interpersonal"],
            ),
            RolCreate(
                nombre="Ejecutivo de Ventas",
                requisitos=["Experiencia en ventas B2B/B2C", "Manejo de CRM", "Negociación"],
            ),
            RolCreate(
                nombre="Especialista en Marketing Digital",
                requisitos=["SEO/SEM", "Gestión de redes sociales", "Analítica web (Google Analytics)"],
            ),
        ]
        for r in ejemplos:
            self.create(r)

    def list_all(self) -> list[dict]:
        return list(self._roles.values())

    def get(self, rol_id: int) -> dict | None:
        return self._roles.get(rol_id)

    def create(self, data: RolCreate) -> dict:
        rol = {"id": self._next_id, **data.model_dump()}
        self._roles[self._next_id] = rol
        self._next_id += 1
        return rol


class CandidatoStore:
    def __init__(self):
        self._candidatos: dict[int, dict] = {}
        self._next_id = 1

    def list_all(self) -> list[dict]:
        return list(self._candidatos.values())

    def list_by_rol(self, rol_id: int) -> list[dict]:
        return [c for c in self._candidatos.values() if c.get("rol_id") == rol_id]

    def get(self, candidato_id: int) -> dict | None:
        return self._candidatos.get(candidato_id)

    def create(self, data: CandidatoCreate) -> dict:
        candidato = {
            "id": self._next_id,
            "nombre": data.nombre,
            "email": data.email,
            "hoja_de_vida_texto": data.hoja_de_vida_texto,
            "rol_id": data.rol_id,
            "rol_nombre": None,
            "estado": EstadoEvaluacion.PENDIENTE,
            "score": None,
            "requisitos_cumplidos": [],
            "requisitos_faltantes": [],
            "explicacion": None,
        }
        self._candidatos[self._next_id] = candidato
        self._next_id += 1
        return candidato

    def update(self, candidato_id: int, **campos) -> dict | None:
        candidato = self._candidatos.get(candidato_id)
        if candidato is None:
            return None
        candidato.update(campos)
        return candidato


rol_store = RolStore()
candidato_store = CandidatoStore()