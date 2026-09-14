# CVScope

Sistema inteligente de preselección y categorización de talento humano.

Proyecto del curso PTIA (Principios y Tecnologías de Inteligencia Artificial)
- Escuela Colombiana de Ingeniería Julio Garavito
- Tomás Olaya Díaz y Juan Pablo Vega Villamil
- 2026-2

## Descripción

CVScope categoriza candidatos por rol profesional (Full Stack, RRHH, ventas,
marketing digital, etc.), evalúa si cumplen los requisitos mínimos de ese rol
usando un LLM (Gemini), y genera un ranking de los candidatos aptos según qué
tan bien encajan con el perfil buscado — devolviendo no solo un veredicto,
sino una **explicación** de qué requisitos cumple y cuáles no cada candidato,
priorizando interpretabilidad sobre una simple decisión de caja negra.

## Stack

- **Backend:** Python + FastAPI
- **Frontend:** React + Vite
- **LLM:** Gemini 2.5 Flash (vía endpoint compatible con OpenAI)
- **Base de datos:** PostgreSQL

## Estructura del repositorio

```
cvscope/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/       # Endpoints: vacantes, candidatos, preseleccion
│   │   ├── services/      # Lógica de negocio (integración con Gemini)
│   │   ├── models/        # Modelos de base de datos
│   │   └── schemas/       # Esquemas Pydantic (validación de datos)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── components/
        ├── pages/
        └── services/
```

## Cómo ejecutar

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env        # Y completar con tu API key de Google AI Studio
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Estado del proyecto

🚧 En desarrollo — Hito 1 (Exploración)
