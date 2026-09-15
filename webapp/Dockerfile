# Build context is the repo root (needs both webapp/ and src/) — see
# docker-compose.prod.yml (`build.context: .`) and
# .github/workflows/deploy-web.yml (`file: webapp/Dockerfile`).
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias primero para cachear esta capa entre builds mientras
# solo cambia el código de la app.
COPY webapp/requirements.txt ./webapp/requirements.txt
RUN pip install --no-cache-dir -r webapp/requirements.txt

# Solo src/ (parsers/analysis/plotly_exports, sin PyQt6) y webapp/ — nunca
# se instala PyQt6 aquí, la imagen no tiene ni necesita libs gráficas de
# sistema (Xorg, Qt, etc.), a diferencia del ejecutable de escritorio.
COPY src ./src
COPY webapp ./webapp

ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_BASE_PATH=materialtestapp

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://localhost:8501/{os.environ[\"STREAMLIT_BASE_PATH\"]}/_stcore/health').read()" || exit 1

# Shell form (no exec-form array) a propósito: necesitamos que $STREAMLIT_BASE_PATH
# se expanda en tiempo de arranque para que docker-compose pueda sobreescribirlo.
CMD streamlit run webapp/streamlit_app.py \
    --server.address=0.0.0.0 \
    --server.port=8501 \
    --server.baseUrlPath=$STREAMLIT_BASE_PATH \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
