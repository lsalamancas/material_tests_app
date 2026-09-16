# Build context is the repo root (needs both webapp/ and src/) — see
# docker-compose.prod.yml (`build.context: .`) and
# .github/workflows/deploy-web.yml (`file: webapp/Dockerfile`).
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias primero para cachear esta capa entre builds mientras
# solo cambia el código de la app.
COPY webapp/requirements.txt ./webapp/requirements.txt
RUN pip install --no-cache-dir -r webapp/requirements.txt

# El HTML base que sirve Streamlit (index.html, empaquetado dentro del
# propio paquete) trae hardcodeado <title>Streamlit</title> — eso es lo que
# se ve en la pestaña una fracción de segundo antes de que el JS del app
# arranque y lo reemplace por el page_title real (st.set_page_config, en
# streamlit_app.py). Se parchea acá para que nunca se vea "Streamlit" ni
# de refilón. Resuelve la ruta vía Python (no un path hardcodeado) para no
# depender de la versión exacta de Python/Streamlit de la imagen.
RUN python -c "import streamlit, os; print(os.path.join(os.path.dirname(streamlit.__file__), 'static', 'index.html'))" \
    | xargs -I{} sed -i 's#<title>Streamlit</title>#<title>Fertechnologies · Material Testing Analyzer</title>#' {}

# Solo src/ (parsers/analysis/plotly_exports, sin PyQt6) y webapp/ — nunca
# se instala PyQt6 aquí, la imagen no tiene ni necesita libs gráficas de
# sistema (Xorg, Qt, etc.), a diferencia del ejecutable de escritorio.
COPY src ./src
COPY webapp ./webapp
# Tema claro forzado (ver comentario en el archivo) — Streamlit lo busca en
# <CWD>/.streamlit/config.toml, y CWD aquí es /app (WORKDIR), no webapp/.
COPY .streamlit ./.streamlit

ENV PYTHONUNBUFFERED=1

EXPOSE 8501

# Sirve en la raíz — la app vive en su propio subdominio
# (materials-app.fertechnologies.com), no bajo un path compartido con otro
# sitio, así que no hace falta --server.baseUrlPath.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health').read()" || exit 1

CMD ["streamlit", "run", "webapp/streamlit_app.py", \
    "--server.address=0.0.0.0", \
    "--server.port=8501", \
    "--server.headless=true", \
    "--server.enableCORS=false", \
    "--server.enableXsrfProtection=false", \
    "--browser.gatherUsageStats=false"]
