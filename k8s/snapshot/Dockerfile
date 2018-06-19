FROM python:3.6-alpine

# see https://elasticsearch-py.readthedocs.io/en/master/index.html#compatibility
ARG ES_PYTHON_VERSION="elasticsearch>=5.0.0,<6.0.0"

ENV MODE "create"
ENV AWS_DEFAULT_REGION "eu-central-1"
ENV AWS_ACCESS_KEY_ID "secret"
ENV AWS_SECRET_ACCESS_KEY "secret"
ENV S3_BUCKET "some-bucket"
ENV ES_CLIENT_ADDRESS "es-client-node.tld"
# retention time in days
ENV ES_SNAPSHOT_RETENTION_TIME "60"

COPY es-snapshot /opt/es-snapshot/

RUN pip install --upgrade pip \
    && pip install --upgrade ${ES_PYTHON_VERSION} boto3 python_dateutil

# run container with `docker run --rm elasticsearch-snapshot restore` to restore backup
ENTRYPOINT [ "python", "/opt/es-snapshot/main.py" ]