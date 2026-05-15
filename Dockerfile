FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=7860

WORKDIR /app

# Copy everything first — keeps things simple and correct.
# We sacrifice a little layer caching for a build that actually works.
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip && pip install .

EXPOSE 7860

RUN useradd --create-home --uid 1000 app
USER app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request, sys; urllib.request.urlopen('http://localhost:7860/healthz', timeout=3); sys.exit(0)" || exit 1

CMD ["python", "-m", "appstore_intel_mcp"]