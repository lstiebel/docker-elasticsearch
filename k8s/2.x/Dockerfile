FROM alpine:3.7

LABEL maintainer="l.stiebellehner@dodax.com"

# Volume for Elasticsearch data
VOLUME ["/data"]

EXPOSE 9200 9300

ARG ELASTICSEARCH_VERSION="2.4.6"

# Set environment variables defaults
ENV ES_HEAP_SIZE "512m"
ENV CLUSTER_NAME "elasticsearch-default"
ENV ES_PLUGINS_INSTALL "cloud-aws"
ENV MEMORY_LOCK "false"
ENV NODE_MASTER "true"
ENV NODE_DATA "true"
ENV HTTP_ENABLE "true"
ENV NETWORK_HOST "0.0.0.0"
ENV HTTP_CORS_ENABLE "true"
ENV HTTP_CORS_ALLOW_ORIGIN "*"
ENV MINIMUM_MASTER_NODES "1"
ENV NUMBER_OF_SHARDS "1"
ENV NUMBER_OF_REPLICAS "0"

# Install OpenJDK and Elasticsearch.
RUN apk add --no-cache wget ca-certificates sudo openjdk8-jre bash jq curl \
    && wget https://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/$ELASTICSEARCH_VERSION/elasticsearch-$ELASTICSEARCH_VERSION.tar.gz -O /tmp/elasticsearch.tar.gz \
    && tar xfv /tmp/elasticsearch.tar.gz -C /tmp \
    && mv /tmp/elasticsearch-$ELASTICSEARCH_VERSION /elasticsearch \
    && rm -rf /tmp/* \
    && apk del wget

# Copy configuration
COPY config /elasticsearch/config

# Copy startup script
COPY run-elasticsearch.sh /run-elasticsearch.sh
RUN chmod +x /run-elasticsearch.sh


CMD ["/bin/bash","/run-elasticsearch.sh"]