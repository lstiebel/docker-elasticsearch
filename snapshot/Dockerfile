FROM alpine:latest

ENV AWS_REGION eu-central-1
ENV AWS_ACCESS_KEY xxx
ENV AWS_SECRET_KEY xxx
ENV S3_STORAGE_CLASS standar_ia
ENV ELASTICSEARCH_HOST es-client
ENV CLUSTERNAME dop-search
ENV ENVIRONMENT production
ENV WAIT_FOR_COMPLETION true

RUN apk add --no-cache curl bash jq

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["bash", "/entrypoint.sh"]
