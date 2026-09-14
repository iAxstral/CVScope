from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import candidatos, vacantes, preseleccion, roles

app = FastAPI(
    title="CVScope API",
    description="Categoriza candidatos por rol, evalúa si cumplen los requisitos usando un LLM (Gemini) y genera un ranking explicable de aptos.",
    version="0.1.0",
)

# CORS: permite que el frontend (Vite, por defecto en localhost:5173) consuma la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(roles.router, prefix="/roles", tags=["Roles"])
app.include_router(vacantes.router, prefix="/vacantes", tags=["Vacantes"])
app.include_router(candidatos.router, prefix="/candidatos", tags=["Candidatos"])
app.include_router(preseleccion.router, prefix="/preseleccion", tags=["Preselección"])


@app.get("/")
def root():
    return {"mensaje": "CVScope API activa"}
