FROM python:3.13-slim

# CON_CLASIFICADOR=true instala también el clasificador de rol (PyTorch, ~2 GB)
ARG CON_CLASIFICADOR=false

WORKDIR /app
COPY requirements-api.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt \
    && if [ "$CON_CLASIFICADOR" = "true" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi

COPY app ./app
COPY data ./data
COPY scripts ./scripts

RUN useradd --create-home cvscope && chown -R cvscope /app
USER cvscope

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
