FROM python:3.11-slim-bullseye AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=production

WORKDIR /app


FROM base as build-final
# This stage installs the dependencies that need to be installed in the final image.

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install "poetry==1.3.1" && pip install --upgrade setuptools

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential libpq-dev libjpeg-dev zlib1g-dev libwebp-dev libmagic1

RUN  python -m venv /venv
ENV PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --only postgres


FROM build-final as build-scss
# This stage builds the SASS, using dependencies that are not needed in the final image.

RUN poetry install --only main --only postgres --only scss

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
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        cron postgresql-client libjpeg-dev zlib1g-dev libwebp-dev libmagic1 && \
    rm -rf /var/lib/apt/lists/*

COPY infra/concrexit/cronjobs /cronjobs
RUN crontab /cronjobs && rm /cronjobs

COPY infra/concrexit/docker-entrypoint.sh /app/docker-entrypoint.sh
CMD [ "/app/docker-entrypoint.sh" ]

COPY --from=build-final /venv /venv
COPY --from=build-scss /app/website /app/website
WORKDIR /app/website

RUN adduser --system --uid 5678 appuser

# Persist the SOURCE_COMMIT build argument as
# environment variable in the resulting image.
ARG SOURCE_COMMIT
ENV SOURCE_COMMIT=${SOURCE_COMMIT}
