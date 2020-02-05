FROM python:3.8
MAINTAINER Thalia Technicie <www@thalia.nu>
LABEL description="Contains the Thaliawebsite Django application"

# Arguments
ARG install_dev_requirements=1
ARG source_commit="unknown"

# Try to keep static operation on top to maximise Docker cache utilisation

# Disable output buffering
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive
ENV SOURCE_COMMIT=${source_commit}
ENV PATH /root/.poetry/bin:${PATH}

# Set up entrypoint and command
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Create /concrexit dir
# Create log dir and log file
# Create app dir
RUN mkdir /concrexit && \
    mkdir -p /concrexit/log/ && \
    touch /concrexit/log/uwsgi.log && \
    chown -R www-data:www-data /concrexit && \
    mkdir -p /usr/src/app && \
    mkdir -p /usr/src/app/website

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    gettext \
    ghostscript && \
    rm -rf /var/lib/apt

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python && \
    poetry config virtualenvs.create false

WORKDIR /usr/src/app/website/
# install python requirements
COPY pyproject.toml /usr/src/app/website/
COPY poetry.lock /usr/src/app/website/
RUN if [ "$install_dev_requirements" -eq 1 ]; then \
        poetry install --no-interaction; \
    else \
        echo "This will fail if the dependencies are out of date"; \
        poetry install --no-interaction --no-dev; \
    fi; \
    poetry cache clear --all --no-interaction pypi

# Create entry points
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY resources/entrypoint_production.sh /usr/local/bin/entrypoint_production.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && \
    chmod +x /usr/local/bin/entrypoint_production.sh

# copy app source
COPY website /usr/src/app/website/

RUN echo "Don't build releases yourself, let CI do it!"
