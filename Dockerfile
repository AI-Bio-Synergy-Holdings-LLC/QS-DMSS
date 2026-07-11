FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install --upgrade pip build && \
    python -m build --wheel


FROM python:3.12-slim AS runtime

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" qsdmss && \
    mkdir -p /app/runs && \
    chown -R qsdmss:qsdmss /app

COPY --from=builder /build/dist/*.whl /tmp/dist/

RUN python -m pip install --upgrade pip && \
    python -m pip install /tmp/dist/*.whl && \
    rm -rf /tmp/dist

USER qsdmss

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8001\")}/api/health', timeout=3).read()"

CMD ["sh", "-c", "qs-dmss cockpit --host 0.0.0.0 --port ${PORT:-8001} --output-root /app/runs"]
