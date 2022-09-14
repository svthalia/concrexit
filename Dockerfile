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
RUN poetry install --no-dev --extras "production"

FROM base as final

EXPOSE 8000

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ghostscript postgresql-client libjpeg-dev zlib1g-dev libwebp-dev libmagic1 && \
        rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
COPY . .
COPY infra/docker/local/docker-entrypoint.sh /app/docker-entrypoint.sh

VOLUME [ "/static" ]
ENV STATIC_ROOT=/static

RUN mkdir /static && \
    MANAGE_PY=1 /venv/bin/python website/manage.py collectstatic && \
    MANAGE_PY=1 /venv/bin/python website/manage.py compress

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

WORKDIR /app/website
CMD [ "/app/docker-entrypoint.sh" ]
