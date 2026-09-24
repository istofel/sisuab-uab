FROM python:3.12-slim-trixie
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN useradd --create-home --uid 10001 app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY --chown=app:app app.py ./
COPY --chown=app:app core ./core
COPY --chown=app:app ui ./ui
COPY --chown=app:app config ./config
COPY --chown=app:app docs/banner ./docs/banner
COPY --chown=app:app .streamlit ./.streamlit
RUN mkdir -p /app/logs && chown app:app /app/logs
USER app
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health',timeout=3).read()==b'ok' else 1)"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
