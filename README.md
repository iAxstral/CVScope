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
   lo sustenta; es **apto** si cumple al menos el 66% de los requisitos. Hay dos
   motores: **palabras clave** (determinístico) y **Gemini** (entiende
   redacciones indirectas; debe citar evidencia literal o el requisito no se
   acepta). El CV se puede subir en PDF, DOCX o TXT.
3. **Rankear** — entre las hojas de vida aptas del rol se devuelve el **top 5**.
   Puntaje = 80 × fracción de requisitos cumplidos + 20 × experiencia (tope 12 años).

## Red neuronal competitiva

![Diagrama de la red neuronal competitiva](docs/diagrama/red_competitiva.png)

Es una **red competitiva tipo Hamming** (ver [docs/diagrama](docs/diagrama/README.md)):
cada hoja de vida es una **neurona** y compiten hasta que solo queda una activa.

1. **Entrada:** el texto de cada hoja de vida, anonimizado, convertido en un
   vector de 1026 características (fracción de requisitos con evidencia, años de
   experiencia y 1024 n-gramas con *hashing*).
2. **Capa de evaluación** (feedforward, entrenada): red siamesa
   `1026 → 64 → 32 → 1` (ReLU) que le da a cada hoja de vida su **fuerza** `s(x)`.
3. **Capa competitiva MAXNET** (recurrente): una neurona por hoja de vida con
   autoexcitación `+1` e inhibición lateral `−ε`:
   `aᵢ(t+1) = max(0, aᵢ(t) − ε · Σⱼ≠ᵢ aⱼ(t))`. Las neuronas débiles se apagan
   hasta que solo queda la **ganadora** (*winner-take-all*).
4. **Salida:** vector one-hot con la ganadora, probabilidad de ganar de cada
   una (`softmax(s)`; en un duelo `σ(s_A − s_B)`) y el top 5 (se retira la
   ganadora y se repite).

Se puede jugar como **competencia abierta** (todas a la vez) o como **torneo**
de eliminación directa, donde cada duelo es una MAXNET de 2 neuronas y la
ganadora pasa a la siguiente ronda. La interfaz muestra cómo se apagan las
neuronas iteración por iteración.

- **Entrenamiento** (solo la capa de evaluación): 4.512 duelos dentro de cada
  rol del dataset de selección (gana el mayor puntaje de referencia; los
  empates se etiquetan 0.5), entropía cruzada por pares, Adam + L2.
- **Prueba (dataset de ranking, no visto en el entrenamiento):**

| Métrica | Red competitiva | Palabras clave |
|---|---|---|
| Exactitud en duelos | 0.959 | 0.934 |
| Precisión@5 | 0.80 | 0.70 |

Entrenar de nuevo: `python scripts/entrenar_red_competitiva.py` (desde `backend/`).

## Sesgos y equidad

Antes de que cualquier modelo vea una hoja de vida se quitan nombre, ciudad,
edad, estado civil, género y datos de contacto. Una auditoría con
contrafactuales (`python scripts/auditar_sesgos.py`) verifica que cambiar
solo esos datos no cambia la evaluación (variación 0); encontró y permitió
corregir dos fugas. Detalles y limitaciones en [docs/sesgos.md](docs/sesgos.md).

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
clave no detecta; ahí es donde Gemini debería aportar. Para medirlo (requiere
la API key): `python scripts/evaluar_llm.py --n 40`.

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
│   │   ├── services/      # anonimizador, evaluadores (palabras clave y Gemini), red_competitiva/, extractor de archivos
│   │   ├── models/        # Store en memoria (roles y candidatos)
│   │   ├── schemas/       # Esquemas Pydantic (validación de datos)
│   │   └── ml_models/     # clasificador_rol.pkl, red_competitiva.npz
│   ├── data/              # dataset_seleccion.csv, dataset_ranking.csv
│   ├── scripts/           # generar datasets, entrenar, evaluar y auditar sesgos
│   ├── tests/             # pruebas (pytest)
│   ├── requirements.txt
│   └── .env.example
├── docs/
│   ├── diagrama/          # diagrama de la red competitiva (.drawio, .svg, .png)
│   └── sesgos.md
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
| POST | `/preseleccion/evaluar` | Apto/no apto + evidencia por requisito; `motor`: `palabras_clave` o `llm` (Gemini) |
| GET | `/preseleccion/motores` | Indica si Gemini está disponible (hay API key) |
| POST | `/preseleccion/extraer-texto` | Extrae el texto de un CV en PDF, DOCX o TXT |
| GET | `/preseleccion/ranking/{rol_id}?top=5` | Top N de hojas de vida aptas del rol |
| GET | `/preseleccion/hojas-de-vida/{cv_id}` | Detalle explicable de un CV del dataset o registrado |
| POST | `/competencia/comparar` | Duelo (MAXNET de 2 neuronas): probabilidad, ganador, explicación y traza de activaciones |
| POST | `/competencia/torneo` | Torneo por rondas, competencia abierta (MAXNET con todas), campeón y top N |
| GET | `/competencia/modelo` | Arquitectura y métricas de la red competitiva |
| GET | `/datasets/` · `/datasets/seleccion` · `/datasets/ranking` | Resumen y consulta de los datasets |

## Cómo ejecutar

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env        # Opcional: API key de Google AI Studio para usar Gemini
uvicorn app.main:app --reload
python -m pytest tests      # pruebas (pip install pytest)
```

Sin API key todo funciona con el motor de palabras clave; con
`OPENAI_API_KEY` en `backend/.env` se habilita Gemini en "Seleccionar CV".

### Frontend
```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173 (backend en VITE_API_URL, por defecto http://127.0.0.1:8000)
```

## Estado del proyecto

🚧 En desarrollo — Hito 2
