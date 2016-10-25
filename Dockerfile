FROM python:3.5-alpine
MAINTAINER Thom Wiggers <thom@thomwiggers.nl>
LABEL version=1.0
LABEL description="Contains the Thaliawebsite Django application"

# Try to keep static operation on top to maximise Docker cache utilisation

# Disable output buffering
ENV DJANGO_PRODUCTION 1
ENV PYTHONUNBUFFERED 1

# Create log dir
RUN mkdir /log/
RUN touch /log/uwsgi.log
# Create app directory
RUN mkdir -p /usr/src/app

# Create entry points
WORKDIR /usr/local/bin
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY resources/entrypoint_production.sh /usr/local/bin/entrypoint_production.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint_production.sh

# Install dependencies
RUN apk add --no-cache \
    gettext \
    bash \
    postgresql-client \
    libwebp \
    tiff \
    zlib \
    freetype \
    uwsgi \
    lcms2 \
    libjpeg-turbo

# Install build deps
RUN apk add --no-cache --virtual .builddeps \
    build-base \
    tiff-dev \
    libjpeg-turbo-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    libwebp-dev \
    postgresql-dev

WORKDIR /usr/src/app
# install python requirements
COPY requirements.txt /usr/src/app/
COPY production-requirements.txt /usr/src/app/
RUN pip install --no-cache-dir \
    -r requirements.txt \
    -r production-requirements.txt

RUN apk del .builddeps

# copy app source
COPY website /usr/src/app/

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]
