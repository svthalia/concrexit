FROM python:3.11-slim-bullseye AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=production

WORKDIR /app

FROM base as builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install "poetry==1.3.1"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential libpq-dev libjpeg-dev zlib1g-dev libwebp-dev libmagic1

RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv
COPY pyproject.toml poetry.lock ./

RUN pip install --upgrade setuptools
RUN poetry install --only main --extras "postgres"

FROM base as final

EXPOSE 8000

VOLUME [ "/volumes/media", "/volumes/static" ]

ENV MEDIA_ROOT="/volumes/media" \
    STATIC_ROOT="/volumes/static" \
    SENDFILE_ROOT="/volumes/media"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ghostscript postgresql-client libjpeg-dev zlib1g-dev libwebp-dev libmagic1 && \
        rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
COPY infra/concrexit/docker-entrypoint.sh /app/docker-entrypoint.sh
COPY website /app/website

WORKDIR /app/website

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app

CMD [ "/app/docker-entrypoint.sh" ]

# Persist the SOURCE_COMMIT build argument as
# environment variable in the resulting image.
ARG SOURCE_COMMIT
ENV SOURCE_COMMIT=${SOURCE_COMMIT}
