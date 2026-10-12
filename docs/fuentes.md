# Fuentes del código

De dónde sale cada pieza de CVScope: modelos, datasets, papers y librerías.
Las versiones de las librerías son las fijadas en `backend/requirements-*.txt`
y `frontend/package.json`.

## Modelos de IA

| Pieza | Fuente | Dónde se usa |
|---|---|---|
| Embeddings `all-MiniLM-L6-v2` | Modelo de [sentence-transformers](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) en Hugging Face (destilado de MiniLM, Wang et al., 2020) | `app/services/ia_services.py`; entrada del clasificador de rol |
| Regresión logística | `sklearn.linear_model.LogisticRegression` (scikit-learn) | Clasificador de rol (`clasificador_rol.pkl`) |
| Red de evaluación 1026-64-32-1 | **Propia**, en NumPy; entrenada con duelos de pares (RankNet) | `app/services/red_competitiva/modelo.py` |
| Capa competitiva MAXNET | **Propia**, en NumPy; sigue la red de Hamming (Hagan et al.; Lippmann, 1987) | `red_competitiva/competitiva.py` |
| Capa competitiva LVQ (LVQ1) | **Propia**, en NumPy; regla de Kohonen | `red_competitiva/lvq.py` |
| Gemini 2.5 Flash (**opcional**) | Google AI Studio, por el endpoint compatible con OpenAI (`generativelanguage.googleapis.com/v1beta/openai/`) | `app/services/llm_service.py`; solo con `OPENAI_API_KEY` |
| Evaluador por palabras clave | **Propio**: léxico de sinónimos por requisito, detección de negaciones y años de experiencia | `app/services/evaluador_requisitos.py` |
| Anonimizador | **Propio**: expresiones regulares y listas de nombres y ciudades | `app/services/anonimizador.py` |
| Extractor de características | **Propio**: 2 rasgos explícitos + 1024 *n-gramas* con *hashing trick* (`crc32`) | `red_competitiva/caracteristicas.py` |

## Datasets

| Dataset | Fuente | Notas |
|---|---|---|
| `backend/data/dataset_seleccion.csv` | **Sintético**, generado por `scripts/generar_datasets.py` (semilla 2026) | 240 hojas de vida (60 por rol) con rol y apto/no apto |
| `backend/data/dataset_ranking.csv` | **Sintético**, mismo script | 60 hojas de vida (15 por rol) con puntaje y posición de referencia |
| Resume Dataset (Kaggle) | [kaggle.com/datasets/snehaanbhawal/resume-dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) | **Opcional**, descarga manual; solo para reentrenar el clasificador de rol (ver [clasificador_rol.md](clasificador_rol.md)). No está en el repo; respeta la licencia indicada en Kaggle |

## Papers y libros

- Hagan, M. T., Demuth, H. B., Beale, M. H. y De Jesús, O. *Neural Network
  Design*. Red de Hamming y MAXNET (redes competitivas).
- Lippmann, R. P. (1987). *An introduction to computing with neural nets*.
  IEEE ASSP Magazine, 4(2), 4-22. Origen de la red de Hamming con MAXNET.
- Kohonen, T. (1990). *Improved versions of learning vector quantization*.
  IJCNN 1990. Regla de aprendizaje de la capa LVQ; también en Kohonen, *Self-Organizing
  Maps* (Springer).
- Burges, C. et al. (2005). *Learning to rank using gradient descent*. ICML 2005
  (RankNet). Entrenamiento de la red comparando pares de hojas de vida.
- Kingma, D. P. y Ba, J. (2015). *Adam: a method for stochastic optimization*.
  ICLR 2015. Optimizador de la red de evaluación.
- He, K., Zhang, X., Ren, S. y Sun, J. (2015). *Delving deep into rectifiers*.
  ICCV 2015. Inicialización He de los pesos con ReLU.
- Reimers, N. y Gurevych, I. (2019). *Sentence-BERT: sentence embeddings using
  Siamese BERT-networks*. EMNLP 2019. Librería y enfoque de los embeddings.
- Wang, W. et al. (2020). *MiniLM: deep self-attention distillation for
  task-agnostic compression of pre-trained transformers*. NeurIPS 2020.
- Explicación del ranking: quitar la evidencia de un requisito y medir cuánto
  baja la fuerza es una técnica estándar de interpretabilidad (ablación u
  oclusión); aquí está implementada de forma propia en
  `servicio.explicar_ranking`.
- RFC 8018 (PBKDF2) y RFC 2104 (HMAC), para las contraseñas y los tokens de
  sesión (`app/services/auth.py`, con la librería estándar de Python).

## Librerías del backend

| Librería | Versión | Para qué |
|---|---|---|
| FastAPI | 0.142.4 | API REST |
| Uvicorn | 0.54.0 | Servidor ASGI |
| Pydantic | 2.13.5 | Validación de esquemas |
| python-dotenv | 1.2.4 | Lee `backend/.env` |
| python-multipart | 0.0.32 | Subida de archivos |
| SQLAlchemy | 2.1.4 | Base de datos (SQLite o PostgreSQL) |
| psycopg | 3.3.6 | Conexión a PostgreSQL |
| NumPy | 2.5.3 | Red competitiva, MAXNET y LVQ |
| openai (SDK) | 3.26.0 | Cliente del endpoint compatible con OpenAI de Gemini |
| pypdf | 6.19.0 | Extraer texto de PDF |
| python-docx | 1.2.0 | Extraer texto de DOCX |
| scikit-learn | 1.9.1 | Regresión logística del clasificador de rol |
| sentence-transformers | 6.1.0 | Embeddings del clasificador de rol |
| joblib | 1.6.0 | Guardar y cargar el clasificador |
| pytest, httpx, reportlab | 9.1.1, 0.28.1, 5.0.1 | Pruebas |

## Librerías y herramientas del frontend

| Herramienta | Versión | Para qué |
|---|---|---|
| React / React DOM | ^19.2.8 | Interfaz |
| React Router | ^7.18.3 | Rutas |
| Vite | ^8.3.0 | Servidor de desarrollo y *build* |
| oxlint | ^1.81.0 | *Lint* |
| Playwright | 1.56.1 | Pruebas de punta a punta |
| Fuentes Fraunces, Inter e IBM Plex Mono | Google Fonts | Tipografía |

## Infraestructura y documentación

- PostgreSQL 16 y nginx (imágenes oficiales de Docker), Docker Compose.
- GitHub Actions: `actions/checkout@v4`, `setup-python@v5`, `setup-node@v4`,
  `upload-artifact@v4`.
- Diagramas: [draw.io / diagrams.net](https://www.drawio.com) (formato `.drawio`)
  generados con `docs/diagrama/generar_diagrama.py`; el diagrama de flujo del README
  usa [Mermaid](https://mermaid.js.org).

## Código propio

Todo lo demás (evaluador, anonimizador, red competitiva, torneo, explicación
del ranking, pruebas, interfaz) es código propio del proyecto, escrito sobre
las librerías de las tablas anteriores.
