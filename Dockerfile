FROM thalia/concrexit-dependencies
MAINTAINER Thalia Technicie <www@thalia.nu>
LABEL description="Contains the Thaliawebsite Django application"

ARG install_dev_requirements=1
ARG source_commit="unknown"

ENV PYTHONUNBUFFERED 1
ENV SOURCE_COMMIT=${source_commit}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

COPY resources/entrypoint.sh resources/entrypoint_production.sh /usr/local/bin/

RUN if [ "$install_dev_requirements" -eq 1 ]; then \
        poetry install --no-interaction --extras "docs"; \
    else \
        poetry install --no-interaction --no-dev; \
    fi; \
    poetry cache clear --all --no-interaction pypi

RUN mkdir --parents /concrexit/log/ && \
    touch /concrexit/log/uwsgi.log && \
    chown --recursive www-data:www-data /concrexit/ && \
    chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/entrypoint_production.sh

COPY website /usr/src/app/website/
WORKDIR /usr/src/app/website/
