FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md alembic.ini /app/
COPY alembic /app/alembic
COPY scripts /app/scripts
COPY src /app/src

RUN chmod +x /app/scripts/start_app.sh /app/scripts/start_worker.sh \
    && python -m pip install --upgrade pip \
    && python -m pip install .

EXPOSE 8000

CMD ["/app/scripts/start_app.sh"]
