FROM python:3.13-slim

# El clasificador de rol (PyTorch + sentence-transformers) viene activo por
# defecto. CON_CLASIFICADOR=false genera una imagen liviana sin él: entonces
# POST /preseleccion/categorizar responde 503 y el resto de la API funciona.
ARG CON_CLASIFICADOR=true

# El modelo de embeddings se descarga al construir la imagen, así que el
# contenedor no necesita acceso a Hugging Face al arrancar.
ENV HF_HOME=/app/.cache/huggingface

WORKDIR /app
COPY requirements-api.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt \
    && if [ "$CON_CLASIFICADOR" = "true" ]; then \
         pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
         && pip install --no-cache-dir -r requirements-ml.txt \
         && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"; \
       fi

COPY app ./app
COPY data ./data
COPY scripts ./scripts

RUN useradd --create-home cvscope && chown -R cvscope /app
USER cvscope

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
