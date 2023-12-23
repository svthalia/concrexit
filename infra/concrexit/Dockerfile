FROM python:3.11-slim-bullseye AS base

ARG DJANGO_ENV
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=${DJANGO_ENV} \
    TZ=Europe/Amsterdam

WORKDIR /app


FROM base as build-venv
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

RUN echo $DJANGO_ENV
RUN if [ $DJANGO_ENV="development" ]; then echo "_$DJANGO_ENV"; else echo "success!!"; fi
RUN if [ $DJANGO_ENV="development" ]; then poetry install --only main --only postgreslocal; else poetry install --only main --only postgres; fi


FROM build-venv as build-scss
# This stage builds the SASS, using dependencies that are not needed in the final image.

RUN if [ $DJANGO_ENV="development" ]; then poetry install --only main --only postgreslocal --only scss; else poetry install --only main --only postgres --only scss; fi

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
    postgresql-client libjpeg-dev zlib1g-dev libwebp-dev libmagic1 && \
    rm -rf /var/lib/apt/lists/*


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
