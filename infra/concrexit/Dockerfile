
FROM python:3.13-slim-bookworm AS build-scss

# This stage builds the SASS, using dependencies that are not needed in the final image.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=production \
    TZ=Europe/Amsterdam \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends  \
    build-essential libpq-dev

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-cache --no-dev

COPY website /app/website

RUN MANAGE_PY=1 python /app/website/manage.py compilescss


FROM python:3.13-alpine AS final

VOLUME [ "/volumes/media", "/volumes/static" ]

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=production \
    TZ=Europe/Amsterdam \
    PATH="/app/.venv/bin:$PATH" \
    MEDIA_ROOT="/volumes/media" \
    STATIC_ROOT="/volumes/static" \
    SENDFILE_ROOT="/volumes/media"

EXPOSE 8000
WORKDIR /app

RUN adduser --system --uid 5678 appuser

COPY infra/concrexit/server-entrypoint.sh /app/server-entrypoint.sh
COPY infra/concrexit/worker-entrypoint.sh /app/worker-entrypoint.sh
COPY infra/concrexit/gunicorn.conf.py /app/gunicorn.conf.py

# CMD can be set to /app/worker-entrypoint.sh for a celery worker container.
CMD [ "/app/server-entrypoint.sh" ]

# Install runtime dependencies.
RUN --mount=type=cache,target=/var/cache/apk\
    apk update && apk add \
    postgresql-client jpeg-dev zlib-dev libwebp-dev runuser

# This stage installs the dependencies that need to be installed in the final image.
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-cache --no-dev --no-group scss

COPY --from=build-scss /app/website /app/website
WORKDIR /app/website

# Persist the SOURCE_COMMIT build argument as
# environment variable in the resulting image.
ARG SOURCE_COMMIT
ENV SOURCE_COMMIT=${SOURCE_COMMIT}
