from fastapi import APIRouter

router = APIRouter()

# Roles de ejemplo con sus requisitos mínimos (esto luego debería vivir en
# la base de datos, no hardcodeado, pero sirve como punto de partida)
ROLES_EJEMPLO = [
    {
        "id": 1,
        "nombre": "Full Stack Developer",
        "requisitos": ["JavaScript/TypeScript", "React o similar", "Node.js o backend equivalente", "Bases de datos SQL/NoSQL"],
    },
    {
        "id": 2,
        "nombre": "Analista de Recursos Humanos",
        "requisitos": ["Gestión de procesos de selección", "Manejo de nómina", "Comunicación interpersonal"],
    },
    {
        "id": 3,
        "nombre": "Ejecutivo de Ventas",
        "requisitos": ["Experiencia en ventas B2B/B2C", "Manejo de CRM", "Negociación"],
    },
    {
        "id": 4,
        "nombre": "Especialista en Marketing Digital",
        "requisitos": ["SEO/SEM", "Gestión de redes sociales", "Analítica web (Google Analytics)"],
    },
]


@router.get("/")
def listar_roles():
    """Lista los roles/categorías profesionales disponibles con sus requisitos."""
    return {"roles": ROLES_EJEMPLO}


@router.get("/{rol_id}")
def obtener_rol(rol_id: int):
    """Consulta el detalle de un rol específico (requisitos mínimos)."""
    rol = next((r for r in ROLES_EJEMPLO if r["id"] == rol_id), None)
    return rol or {"error": "Rol no encontrado"}
