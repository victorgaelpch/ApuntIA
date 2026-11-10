# Imagen del backend de ApuntIA (FULL-13): FastAPI + OpenCV + Tesseract + ReportLab.
# Construir desde la raíz del repositorio (lo hace fullstack/compose.yaml).
#
# Base Ubuntu 24.04 LTS: trae Tesseract 5.3.4, la MISMA versión con la que se midió el OCR
# (PROCESAMIENTO.md, docs/evaluacion.md), así los resultados en Docker son comparables.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH=/opt/venv/bin:$PATH

# Python 3.12 y Tesseract con español e inglés (≈ 30 MB): el OCR funciona sin descargas al arrancar.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates \
       tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/venv

WORKDIR /app/back/motori_magenes
# Dependencias primero (capa en caché mientras no cambien), con las versiones fijadas.
COPY back/motori_magenes/requirements.txt back/motori_magenes/constraints.txt ./
RUN pip install -r requirements.txt -c constraints.txt

# Código: solo lo necesario para ejecutar (sin pruebas, datos ni entornos locales).
COPY back/motori_magenes/app ./app
COPY back/motori_magenes/main.py ./

# Usuario sin privilegios y carpeta de datos persistente (volumen).
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin apuntia \
    && mkdir -p /datos && chown apuntia /datos
USER apuntia

ENV DATA_DIR=/datos \
    FRONT_DIR="" \
    OCR_MOTOR=tesseract \
    OCR_IDIOMAS=spa+eng \
    MPLCONFIGDIR=/tmp/matplotlib
VOLUME ["/datos"]
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import json,urllib.request,sys; sys.exit(0 if json.load(urllib.request.urlopen('http://127.0.0.1:8000/salud', timeout=4))['estado']=='ok' else 1)"

# --proxy-headers: detrás de Nginx, el esquema y el host son los del navegador (comprobación de Origin).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*", "--timeout-graceful-shutdown", "15"]
