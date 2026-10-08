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

## Flujo

1. **Categorizar** — un clasificador (embeddings `all-MiniLM-L6-v2` + regresión
   logística, `app/ml_models/clasificador_rol.pkl`) predice el rol del CV.
2. **Seleccionar** — se evalúa el CV contra los requisitos mínimos del rol:
   cada requisito queda como *cumple / no cumple* con el fragmento del CV que
   lo sustenta; es **apto** si cumple al menos el 66% de los requisitos.
3. **Rankear** — entre las hojas de vida aptas del rol se devuelve el **top 5**.
   Puntaje = 80 × fracción de requisitos cumplidos + 20 × experiencia (tope 12 años).

## Red neuronal competitiva

Pone a competir las hojas de vida de un rol **de a dos**: en cada duelo la red
decide cuál es mejor y la ganadora pasa a la siguiente ronda, hasta que queda
un campeón (eliminación directa; si no son potencia de 2, los primeros
sembrados pasan la primera ronda sin jugar). El top 5 se obtiene jugando
torneos sucesivos y retirando al campeón de cada uno.

- **Arquitectura:** red siamesa en NumPy. La misma red (1026 → 64 → 32 → 1,
  ReLU) le da a cada hoja de vida un puntaje de fuerza `s(x)` y
  `P(A gana a B) = sigmoide(s(A) − s(B))`, así el duelo es consistente
  (`P(A>B) = 1 − P(B>A)`).
- **Entrada (1026):** fracción de requisitos con evidencia, años de experiencia
  y una bolsa de unigramas/bigramas con *hashing* (1024). Los n-gramas le
  permiten reconocer requisitos escritos sin las palabras clave.
- **Entrenamiento:** duelos dentro de cada rol del dataset de selección (gana
  el mayor puntaje de referencia; los empates se etiquetan 0.5), pérdida de
  entropía cruzada por pares, Adam + L2.
- **Prueba (dataset de ranking, no visto en el entrenamiento):**

| Métrica | Red competitiva | Palabras clave |
|---|---|---|
| Exactitud en duelos | 0.956 | 0.934 |
| Precisión@5 del torneo | 0.80 | 0.70 |

Entrenar de nuevo: `python scripts/entrenar_red_competitiva.py`.
Pruebas: `pip install pytest && python -m pytest tests` (desde `backend/`).

## Datasets

Ambos son sintéticos y reproducibles (`python scripts/generar_datasets.py`,
semilla fija). Incluyen ruido intencional: requisitos descritos con redacción
implícita y menciones negadas ("sin experiencia en nómina").

| Dataset | Archivo | Filas | Uso |
|---|---|---|---|
| Selección | `backend/data/dataset_seleccion.csv` | 240 (60 por rol) | Rol + veredicto apto/no apto. Entrena el clasificador de rol y valida la selección. |
| Ranking | `backend/data/dataset_ranking.csv` | 60 (15 por rol) | Puntaje y posición de referencia. Valida el top 5 por rol. |

Métricas del evaluador de requisitos (`python scripts/evaluar_datasets.py`):

- Selección: exactitud 0.954 · precisión 1.000 · recall 0.917 · F1 0.957
- Ranking: precisión@5 promedio 0.75 (fullstack 2/5, marketing 4/5, rrhh 4/5, ventas 5/5)

Los errores vienen de redacciones implícitas que la búsqueda por palabras
clave no detecta; ahí es donde el LLM debería aportar.

Para reentrenar el clasificador de rol con el dataset de selección:
`python scripts/entrenar_clasificador_rol.py` (necesita `sentence-transformers`
y acceso a Hugging Face).

## Estructura del repositorio

```
cvscope/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/       # roles, candidatos, preseleccion, datasets, vacantes
│   │   ├── services/      # clasificador de rol, evaluador de requisitos, red_competitiva/, datasets, LLM
│   │   ├── models/        # Store en memoria (roles y candidatos)
│   │   ├── schemas/       # Esquemas Pydantic (validación de datos)
│   │   └── ml_models/     # clasificador_rol.pkl, red_competitiva.npz
│   ├── data/              # dataset_seleccion.csv, dataset_ranking.csv
│   ├── scripts/           # generar, evaluar y entrenar
│   ├── tests/             # pruebas de la red competitiva
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── api/           # Cliente HTTP del backend
        ├── components/
        ├── hooks/
        ├── pages/         # Dashboard, Seleccionar, Ranking, Red competitiva, Detalle, Datasets
        └── utils/
```

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/preseleccion/categorizar` | Rol predicho por el clasificador |
| POST | `/preseleccion/evaluar` | Apto/no apto + evidencia por requisito (rol opcional: si falta, se categoriza) |
| GET | `/preseleccion/ranking/{rol_id}?top=5` | Top N de hojas de vida aptas del rol |
| GET | `/preseleccion/hojas-de-vida/{cv_id}` | Detalle explicable de un CV del dataset o registrado |
| POST | `/competencia/comparar` | Duelo entre dos hojas de vida: probabilidad, ganador y explicación |
| POST | `/competencia/torneo` | Torneo completo por rondas, campeón y top N |
| GET | `/competencia/modelo` | Arquitectura y métricas de la red competitiva |
| GET | `/datasets/` · `/datasets/seleccion` · `/datasets/ranking` | Resumen y consulta de los datasets |

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
npm run dev                 # http://localhost:5173 (backend en VITE_API_URL, por defecto http://127.0.0.1:8000)
```

## Estado del proyecto

🚧 En desarrollo — Hito 2
