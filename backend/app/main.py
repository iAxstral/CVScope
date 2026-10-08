from dotenv import load_dotenv

load_dotenv()  # backend/.env: API key de Gemini, base de datos...

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.routers import candidatos, competencia, datasets, preseleccion, roles  # noqa: E402

app = FastAPI(
    title="CVScope API",
    description="Categoriza candidatos por rol, evalúa si cumplen los requisitos usando un LLM (Gemini) y genera un ranking explicable de aptos.",
    version="0.1.0",
)

# CORS: permite que el frontend (Vite, por defecto en localhost:5173) consuma la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(roles.router, prefix="/roles", tags=["Roles"])
app.include_router(candidatos.router, prefix="/candidatos", tags=["Candidatos"])
app.include_router(preseleccion.router, prefix="/preseleccion", tags=["Preselección"])
app.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
app.include_router(competencia.router, prefix="/competencia", tags=["Red competitiva"])


@app.get("/")
def root():
    return {"mensaje": "CVScope API activa"}
