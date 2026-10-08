import os

from dotenv import load_dotenv

load_dotenv()  # backend/.env: API key de Gemini, base de datos...

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.dependencias import usuario_actual  # noqa: E402
from app.routers import auth, candidatos, competencia, datasets, preseleccion, roles  # noqa: E402

app = FastAPI(
    title="CVScope API",
    description="Categoriza candidatos por rol, evalúa si cumplen los requisitos usando un LLM (Gemini) y genera un ranking explicable de aptos.",
    version="0.1.0",
)

# Todos los endpoints, salvo /auth/login y la raíz, exigen sesión iniciada.
protegido = [Depends(usuario_actual)]

# CORS: orígenes del frontend que pueden consumir la API (Vite en desarrollo;
# en Docker se agrega el del contenedor con CORS_ORIGINS, separados por comas)
ORIGENES_PERMITIDOS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(roles.router, prefix="/roles", tags=["Roles"], dependencies=protegido)
app.include_router(candidatos.router, prefix="/candidatos", tags=["Candidatos"], dependencies=protegido)
app.include_router(preseleccion.router, prefix="/preseleccion", tags=["Preselección"], dependencies=protegido)
app.include_router(datasets.router, prefix="/datasets", tags=["Datasets"], dependencies=protegido)
app.include_router(competencia.router, prefix="/competencia", tags=["Red competitiva"], dependencies=protegido)


@app.get("/")
def root():
    return {"mensaje": "CVScope API activa"}
