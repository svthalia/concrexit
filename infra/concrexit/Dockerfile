FROM python:3.11-alpine AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=production \
    TZ=Europe/Amsterdam

WORKDIR /app


FROM base as build-venv
# This stage installs the dependencies that need to be installed in the final image.

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install "poetry==1.8.2" && pip install --upgrade setuptools

RUN --mount=type=cache,target=/var/cache/apk \
    apk update && apk add  \
    build-base libpq-dev jpeg-dev zlib-dev libwebp-dev libmagic

RUN  python -m venv /venv
ENV PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --only postgres

ARG WITH_DEV
RUN if [ "$WITH_DEV" = "1" ]; then poetry install --only dev --only scss; fi


FROM python:3.11-slim-bookworm as build-scss
# This stage builds the SASS, using dependencies that are not needed in the final image.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=production \
    TZ=Europe/Amsterdam

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install "poetry==1.8.2" && pip install --upgrade setuptools


RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends  \
    build-essential libpq-dev libmagic1

RUN  python -m venv /venv
ENV PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main  --only postgres --only scss

COPY website /app/website

RUN MANAGE_PY=1 /venv/bin/python /app/website/manage.py compilescss


FROM base as final
# The final image, with only the dependencies needed in production, and compiled SASS.

EXPOSE 8000

VOLUME [ "/volumes/media", "/volumes/static" ]

ENV PATH=/venv/bin:$PATH \
    MEDIA_ROOT="/volumes/media" \
    STATIC_ROOT="/volumes/static" \
    SENDFILE_ROOT="/volumes/media"

# Install runtime dependencies.
RUN --mount=type=cache,target=/var/cache/apk\
    apk update && apk add \
    postgresql-client jpeg-dev zlib-dev libwebp-dev libmagic runuser


COPY infra/concrexit/server-entrypoint.sh /app/server-entrypoint.sh
COPY infra/concrexit/worker-entrypoint.sh /app/worker-entrypoint.sh
COPY infra/concrexit/gunicorn.conf.py /app/gunicorn.conf.py

# CMD can be set to /app/worker-entrypoint.sh for a celery worker container.
CMD [ "/app/server-entrypoint.sh" ]

COPY --from=build-venv /venv /venv
COPY --from=build-scss /app/website /app/website
WORKDIR /app/website

RUN adduser --system --uid 5678 appuser

# Persist the SOURCE_COMMIT build argument as
# environment variable in the resulting image.
ARG SOURCE_COMMIT
ENV SOURCE_COMMIT=${SOURCE_COMMIT}
