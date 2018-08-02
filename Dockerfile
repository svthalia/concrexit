FROM python:3.5
MAINTAINER Thom Wiggers <thom@thomwiggers.nl>
LABEL description="Contains the Thaliawebsite Django application"

# Arguments
ARG install_dev_requirements=1
ARG source_commit="unknown"

# Try to keep static operation on top to maximise Docker cache utilisation

# Disable output buffering
ENV DJANGO_PRODUCTION 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive
ENV SOURCE_COMMIT=${source_commit}

# Set up entrypoint and command
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]

# Create /concrexit dir
# Create log dir and log file
# Create app dir
RUN mkdir /concrexit && \
    mkdir -p /concrexit/log/ && \
    touch /concrexit/log/uwsgi.log && \
    mkdir -p /concrexit/docs/ && \
    chown -R www-data:www-data /concrexit && \
    mkdir -p /usr/src/app && \
    mkdir -p /usr/src/app/website && \
    mkdir -p /usr/src/app/docs

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    gettext \
    ghostscript && \
    rm -rf /var/lib/apt

WORKDIR /usr/src/app/website/
# install python requirements
COPY docs/requirements.txt /usr/src/app/docs/
COPY Pipfile /usr/src/app/website/
COPY Pipfile.lock /usr/src/app/website/
RUN pipenv install --system --deploy
RUN pip install --no-cache-dir \
    -r ../docs/requirements.txt

RUN if [ "$install_dev_requirements" -eq 1 ]; then \
        pipenv install --system --dev; \
    fi


# Create entry points
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY resources/entrypoint_production.sh /usr/local/bin/entrypoint_production.sh
COPY resources/entrypoint_celery.sh /usr/local/bin/entrypoint_celery.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && \
    chmod +x /usr/local/bin/entrypoint_production.sh && \
    chmod +x /usr/local/bin/entrypoint_celery.sh

# copy app source
COPY website /usr/src/app/website/

# Copy files for Sphinx documentation
COPY README.md /usr/src/app/
COPY docs /usr/src/app/docs

# Cache docs between builds if not mounting to FS
VOLUME /concrexit/docs

RUN echo "Don't build releases yourself, let CI do it!"
