FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build deps first for layer caching
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

# App source
COPY src ./src
RUN pip install --no-deps .

EXPOSE 7860
ENV PORT=7860

# Non-root for safety
RUN useradd --create-home --uid 1000 app
USER app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request, sys; urllib.request.urlopen('http://localhost:7860/healthz', timeout=3); timeout=3); sys.exit(0)" || exit 1

CMD ["python", "-m", "appstore_intel_mcp"]
