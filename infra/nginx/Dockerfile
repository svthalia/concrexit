FROM jonasal/nginx-certbot:4.2-alpine

# The nginx base image will envsubst the template with env variables at runtime and place
# it at /etc/nginx/conf.d/concrexit.conf. See https://registry.hub.docker.com/_/nginx/.
COPY concrexit.conf.template /etc/nginx/templates/concrexit.conf.template
COPY resources /resources

VOLUME ["/vol/static", "/vol/media"]

# Persist the SOURCE_COMMIT build argument as
# environment variable in the resulting image.
ARG SOURCE_COMMIT
ENV SOURCE_COMMIT=${SOURCE_COMMIT}
