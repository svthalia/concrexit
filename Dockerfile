FROM python:3.5
MAINTAINER Thom Wiggers <thom@thomwiggers.nl>
LABEL description="Contains the Thaliawebsite Django application"

# Try to keep static operation on top to maximise Docker cache utilisation

# Disable output buffering
ENV DJANGO_PRODUCTION 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive

# Set up entrypoint and command
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]

# Create /concrexit dir
# Create log dir and log file
# Create app dir
RUN mkdir /concrexit && \
    mkdir -p /concrexit/log/ && \
    touch /concrexit/log/uwsgi.log && \
    chown -R www-data:www-data /concrexit && \
    mkdir -p /usr/src/app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    gettext \
    ghostscript && \
    rm -rf /var/lib/apt

WORKDIR /usr/src/app
# install python requirements
COPY requirements.txt /usr/src/app/
COPY production-requirements.txt /usr/src/app/
COPY dev-requirements.txt /usr/src/app/
RUN pip install --no-cache-dir \
    -r requirements.txt \
    -r production-requirements.txt \
    -r dev-requirements.txt

# Create entry points
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY resources/entrypoint_production.sh /usr/local/bin/entrypoint_production.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && \
    chmod +x /usr/local/bin/entrypoint_production.sh

# copy app source
COPY website /usr/src/app/
