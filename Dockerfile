FROM python:3.5-alpine
MAINTAINER Thom Wiggers <thom@thomwiggers.nl>
LABEL description="Contains the Thaliawebsite Django application"

# Try to keep static operation on top to maximise Docker cache utilisation

# Disable output buffering
ENV DJANGO_PRODUCTION 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /concrexit

# Create log dir
RUN mkdir /concrexit/log/
RUN touch /concrexit/log/uwsgi.log

RUN chown -R 33:33 /concrexit

# Create app directory
RUN mkdir -p /usr/src/app

# Install dependencies
RUN apk add --no-cache \
    gettext \
    bash \
    postgresql-client \
    libwebp \
    tiff \
    zlib \
    freetype \
    lcms2 \
    libxml2 \
    libxslt \
    libffi \
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
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    linux-headers \
    git \
    postgresql-dev

# Install mongodb separately because it's in edge still
RUN echo http://dl-4.alpinelinux.org/alpine/edge/community >> /etc/apk/repositories && \
    apk add --no-cache libsass

WORKDIR /usr/src/app
# install python requirements
COPY requirements.txt /usr/src/app/
COPY production-requirements.txt /usr/src/app/
COPY migration-requirements.txt /usr/src/app/
COPY dev-requirements.txt /usr/src/app/
RUN pip install --no-cache-dir \
    -r requirements.txt \
    -r production-requirements.txt \
    -r migration-requirements.txt \
    -r dev-requirements.txt

RUN apk del .builddeps

# Create entry points
WORKDIR /usr/local/bin
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY resources/entrypoint_production.sh /usr/local/bin/entrypoint_production.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint_production.sh

# copy app source
WORKDIR /usr/src/app
COPY website /usr/src/app/

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]
