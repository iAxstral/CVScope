from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.extractor_texto import ArchivoIlegible, FormatoNoSoportado, extraer_texto

ARCHIVOS = Path(__file__).parent / "archivos"
client = TestClient(app)


def test_pdf_de_varias_paginas():
    texto = extraer_texto("cv.pdf", (ARCHIVOS / "cv_ejemplo.pdf").read_bytes())
    assert "6 años de experiencia" in texto
    assert "React" in texto and "Segunda página" in texto


def test_docx_incluye_tablas():
    texto = extraer_texto("cv.docx", (ARCHIVOS / "cv_ejemplo.docx").read_bytes())
    assert "Camila Rojas" in texto
    assert "React, Node.js, PostgreSQL" in texto


def test_txt_en_utf8_y_latin1():
    assert extraer_texto("cv.txt", "Experiencia en nómina".encode("utf-8")) == "Experiencia en nómina"
    assert extraer_texto("cv.txt", "Experiencia en nómina".encode("latin-1")) == "Experiencia en nómina"


def test_formato_no_soportado_y_archivo_vacio():
    with pytest.raises(FormatoNoSoportado):
        extraer_texto("cv.doc", b"binario")
    with pytest.raises(ArchivoIlegible):
        extraer_texto("cv.txt", b"   ")
    with pytest.raises(ArchivoIlegible):
        extraer_texto("cv.pdf", b"no es un pdf")


def test_api_extraer_texto():
    with open(ARCHIVOS / "cv_ejemplo.pdf", "rb") as f:
        r = client.post("/preseleccion/extraer-texto", files={"archivo": ("cv_ejemplo.pdf", f, "application/pdf")})
    assert r.status_code == 200
    assert "TypeScript" in r.json()["hoja_de_vida_texto"]
    r = client.post("/preseleccion/extraer-texto", files={"archivo": ("cv.doc", b"x", "application/msword")})
    assert r.status_code == 415


def test_api_rechaza_archivos_de_mas_de_5_mb():
    grande = b"a" * (5 * 1024 * 1024 + 1)
    r = client.post("/preseleccion/extraer-texto", files={"archivo": ("cv.txt", grande, "text/plain")})
    assert r.status_code == 413
