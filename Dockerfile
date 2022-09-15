FROM python:3.10-slim-bullseye AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=production
WORKDIR /app

FROM base as builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install "poetry==1.1.13"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential libpq-dev libjpeg-dev zlib1g-dev libwebp-dev libmagic1

RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

FROM base as final

EXPOSE 8000

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ghostscript postgresql-client libjpeg-dev zlib1g-dev libwebp-dev libmagic1 && \
        rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
COPY website /app/website
COPY infra/docker/docker-entrypoint.sh /app/docker-entrypoint.sh
COPY infra/docker/collect-static.sh /app/collect-static.sh

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app

ENV MEDIA_ROOT="/media" \
    STATIC_ROOT="/static"
VOLUME [ "/media", "/static" ]
WORKDIR /app/website
CMD [ "/app/docker-entrypoint.sh" ]
