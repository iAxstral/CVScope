# Clasificador de rol: cómo reproducirlo

El clasificador decide a qué rol pertenece una hoja de vida (`fullstack`,
`rrhh`, `ventas` o `marketing`). Son **embeddings de `all-MiniLM-L6-v2`**
(sentence-transformers) y una **regresión logística** de scikit-learn, guardada
en `backend/app/ml_models/clasificador_rol.pkl`.

El script es [`backend/scripts/entrenar_clasificador_rol.py`](../backend/scripts/entrenar_clasificador_rol.py)
y acepta tres fuentes de datos con `--dataset`:

| `--dataset` | Datos | Uso |
|---|---|---|
| `sintetico` (por defecto) | `backend/data/dataset_seleccion.csv`: 240 hojas de vida sintéticas del repo (60 por rol) | Reproducible sin descargar nada |
| `kaggle` | CSV de Kaggle filtrado a los 4 roles | Hojas de vida reales (en inglés) |
| `combinado` | Las dos anteriores juntas (442 de Kaggle + 240 sintéticas) | **Modelo que está en el repo** |

El `.pkl` del repositorio está entrenado con `--dataset combinado`: Kaggle
aporta hojas de vida reales y el sintético aporta hojas de vida en español,
que es lo que recibe la aplicación.

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
python scripts/entrenar_clasificador_rol.py --dataset combinado   # el modelo del repo
python scripts/entrenar_clasificador_rol.py --dataset kaggle      # solo Kaggle
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
grupos y el resultado sea repetible. Con `--dataset combinado` se estratifica
por **(rol, fuente)**, para que las dos fuentes estén en entrenamiento y en
prueba.

**Modelo.** Cada hoja de vida se convierte en un vector de 384 dimensiones con
`all-MiniLM-L6-v2` y una `LogisticRegression(max_iter=1000)` aprende a separar
los 4 roles.

**Métricas.** Con el 20 % de prueba imprime el reporte de scikit-learn
(precisión, recall y F1 por rol) y guarda en
`backend/app/ml_models/clasificador_rol_metricas.json` la exactitud, el F1
macro, el reporte completo, el tamaño de cada grupo, las métricas de cada
fuente por separado (`por_fuente`) y las versiones usadas
(incluida la de scikit-learn con la que quedó el `.pkl`). Ese archivo es el que
se cita al reportar resultados: no se copian números a mano.

## Resultados del modelo del repo

Copiados de `clasificador_rol_metricas.json` (`--dataset combinado`, semilla
`2026`, 137 hojas de vida de prueba):

| Conjunto de prueba | Hojas de vida | Exactitud | F1 macro |
|---|---|---|---|
| Total | 137 | 0.964 | 0.964 |
| Parte Kaggle | 89 | 0.955 | 0.955 |
| Parte sintética | 48 | 0.979 | 0.979 |

Entrenado solo con Kaggle, el modelo clasificaba como `marketing` a varios
desarrolladores web y a hojas de vida en español. Con 15 textos de prueba
escritos a mano (6 en español y 9 en inglés), el modelo combinado acierta los
15; el `.pkl` que había antes en el repositorio acertaba 3 de los 6 en
español (confundía RR. HH., ventas y frontend con `marketing`).

## Limitaciones

- El CSV de Kaggle está en **inglés** y la aplicación recibe hojas de vida en
  español. `all-MiniLM-L6-v2` es un modelo de embeddings centrado en inglés, así
  que el clasificador puede rendir peor con hojas de vida en español; conviene
  medirlo con hojas de vida propias.
- Los embeddings de MiniLM leen solo los primeros ~256 *tokens*: para hojas de
  vida largas se usa el comienzo del texto.
- Las categorías de Kaggle son etiquetas de un portal de empleo, no una
  anotación experta. En particular, `INFORMATION-TECHNOLOGY` son sobre todo
  perfiles de **soporte e infraestructura** (mesa de ayuda, redes, servidores),
  no de desarrollo. Entrenado solo con Kaggle, el clasificador confundía a los
  desarrolladores web con `marketing` (la categoría `DIGITAL-MEDIA` incluye
  diseño web); por eso el modelo del repo se entrena con `--dataset combinado`.
  Aun así, un perfil de soporte de TI sale como `fullstack`, porque es el único
  rol técnico de CVScope.
- Con `--dataset sintetico` las métricas son casi perfectas porque las hojas de
  vida salen de plantillas; sirven para probar el flujo, no para estimar el
  rendimiento real.
