# Clasificador de rol: cómo reproducirlo

El clasificador decide a qué rol pertenece una hoja de vida (`fullstack`,
`rrhh`, `ventas` o `marketing`). Son **embeddings de `all-MiniLM-L6-v2`**
(sentence-transformers) y una **regresión logística** de scikit-learn, guardada
en `backend/app/ml_models/clasificador_rol.pkl`.

El script es [`backend/scripts/entrenar_clasificador_rol.py`](../backend/scripts/entrenar_clasificador_rol.py)
y acepta dos fuentes de datos con `--dataset`:

| `--dataset` | Datos | Uso |
|---|---|---|
| `sintetico` (por defecto) | `backend/data/dataset_seleccion.csv`: 240 hojas de vida sintéticas del repo (60 por rol) | Reproducible sin descargar nada |
| `kaggle` | CSV de Kaggle filtrado a los 4 roles | Hojas de vida reales (en inglés) |

## 1 · Instalar las dependencias

Las versiones están fijadas en `backend/requirements-ml.txt` (scikit-learn
`1.9.1`, sentence-transformers `6.1.0`, joblib `1.6.0`). Hay que entrenar con
**esas** versiones: un `.pkl` guardado con otra versión de scikit-learn lanza
`InconsistentVersionWarning` al cargarlo y puede dar resultados inválidos.

```bash
cd backend
pip install -r requirements.txt
```

## 2 · Descargar el CSV de Kaggle (a mano)

El CSV **no está en el repositorio** (por tamaño y por licencia). Se descarga
manualmente:

1. Entra a [Kaggle](https://www.kaggle.com) con tu cuenta y abre el dataset
   **Resume Dataset** (`snehaanbhawal/resume-dataset`).
2. Descarga el archivo `Resume/Resume.csv`.
3. Guárdalo en `backend/data/kaggle/Resume.csv` (esa carpeta está en
   `.gitignore`) o pasa otra ruta con `--csv`.

Debe tener las columnas `Category` y `Resume_str` (también se acepta una
columna `Resume`).

## 3 · Entrenar

```bash
cd backend
python scripts/entrenar_clasificador_rol.py --dataset kaggle
# o con otra ruta: --csv ruta/a/Resume.csv
```

Requiere acceso a Hugging Face la primera vez, para descargar el modelo de
embeddings.

## Qué hace el script

**Filtro a 4 roles.** Del CSV solo se conservan estas categorías de Kaggle, que
se renombran a los roles de CVScope; las demás se descartan. También se quitan
las hojas de vida vacías (menos de 50 caracteres) y las repetidas.

| Categoría de Kaggle | Rol de CVScope |
|---|---|
| `INFORMATION-TECHNOLOGY` | `fullstack` |
| `HR` | `rrhh` |
| `SALES` | `ventas` |
| `DIGITAL-MEDIA` | `marketing` |

**División.** 80 % para entrenar y 20 % para probar, **estratificada por rol**
y con semilla `2026`, para que cada rol tenga la misma proporción en ambos
grupos y el resultado sea repetible.

**Modelo.** Cada hoja de vida se convierte en un vector de 384 dimensiones con
`all-MiniLM-L6-v2` y una `LogisticRegression(max_iter=1000)` aprende a separar
los 4 roles.

**Métricas.** Con el 20 % de prueba imprime el reporte de scikit-learn
(precisión, recall y F1 por rol) y guarda en
`backend/app/ml_models/clasificador_rol_metricas.json` la exactitud, el F1
macro, el reporte completo, el tamaño de cada grupo y las versiones usadas
(incluida la de scikit-learn con la que quedó el `.pkl`). Ese archivo es el que
se cita al reportar resultados: no se copian números a mano.

## Limitaciones

- El CSV de Kaggle está en **inglés** y la aplicación recibe hojas de vida en
  español. `all-MiniLM-L6-v2` es un modelo de embeddings centrado en inglés, así
  que el clasificador puede rendir peor con hojas de vida en español; conviene
  medirlo con hojas de vida propias.
- Los embeddings de MiniLM leen solo los primeros ~256 *tokens*: para hojas de
  vida largas se usa el comienzo del texto.
- Las categorías de Kaggle son etiquetas de un portal de empleo, no una
  anotación experta: `INFORMATION-TECHNOLOGY` agrupa perfiles de TI que no
  siempre son *full stack*.
- Con `--dataset sintetico` las métricas son casi perfectas porque las hojas de
  vida salen de plantillas; sirven para probar el flujo, no para estimar el
  rendimiento real.
