FROM docker.pkg.github.com/svthalia/concrexit/dependencies
MAINTAINER Thalia Technicie <www@thalia.nu>
LABEL description="Contains the Thaliawebsite Django application"

ARG source_commit="unknown"

ENV PYTHONUNBUFFERED 1
ENV SOURCE_COMMIT=${source_commit}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

COPY resources/entrypoint.sh resources/entrypoint_production.sh /usr/local/bin/

RUN mkdir --parents /concrexit/log/ && \
    touch /concrexit/log/uwsgi.log && \
    chown --recursive www-data:www-data /concrexit/ && \
    chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/entrypoint_production.sh

COPY website /usr/src/app/website/
WORKDIR /usr/src/app/website/
