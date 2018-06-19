FROM alpine:3.7
LABEL maintainer="l.stiebellehner@dodax.com"

EXPOSE 9200 9300
# Volume for Elasticsearch data
VOLUME ["/data"]

ARG ES_VERSION="5.6.6"

# set environment variable defaults
ENV DISCOVERY_SERVICE "elasticsearch-discovery"
ENV ES_PLUGINS_INSTALL "repository-s3 analysis-stempel analysis-kuromoji"
ENV ES_JAVA_OPTS "-Xms512m -Xmx512m"
ENV CLUSTER_NAME "elasticsearch-default"
ENV NODE_MASTER "true"
ENV NODE_DATA "true"
ENV NODE_INGEST "true"
ENV HTTP_ENABLE "true"
ENV NETWORK_HOST "0.0.0.0"
ENV HTTP_CORS_ENABLE "true"
ENV HTTP_CORS_ALLOW_ORIGIN "*"
ENV MINIMUM_MASTER_NODES "1"
ENV MAX_LOCAL_STORAGE_NODES "1"
ENV SHARD_ALLOCATION_AWARENESS "rack_id"
ENV SHARD_ALLOCATION_AWARENESS_ATTR ""
ENV MEMORY_LOCK "false"
ENV PROCESSORS ""
#ENV REPO_LOCATIONS []

# set ES download parameters
ENV DOWNLOAD_URL "https://artifacts.elastic.co/downloads/elasticsearch"
ENV ES_TARBALL "${DOWNLOAD_URL}/elasticsearch-${ES_VERSION}.tar.gz"
ENV ES_TARBALL_ASC "${DOWNLOAD_URL}/elasticsearch-${ES_VERSION}.tar.gz.asc"
ENV GPG_KEY "46095ACC8548582C1A2699A9D27D666CD88E42B4"
ENV JAVA_HOME=/usr/lib/jvm/default-jvm/jre

# Install OpenJDK and Elasticsearch.
RUN apk add --no-cache --update bash ca-certificates su-exec util-linux curl openjdk8-jre jq curl
RUN apk add --no-cache -t .build-deps gnupg openssl \
    && cd /tmp \
    && curl -o elasticsearch.tar.gz -Lskj "$ES_TARBALL"; \
    if [ "$ES_TARBALL_ASC" ]; then \
    curl -o elasticsearch.tar.gz.asc -Lskj "$ES_TARBALL_ASC"; \
    export GNUPGHOME="$(mktemp -d)"; \
    gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEY"; \
    gpg --batch --verify elasticsearch.tar.gz.asc elasticsearch.tar.gz; \
    rm -r "$GNUPGHOME" elasticsearch.tar.gz.asc; \
    fi; \
    tar -xf elasticsearch.tar.gz \
    && ls -lah \
    && mv elasticsearch-$ES_VERSION /elasticsearch \
    && adduser -DH -s /sbin/nologin elasticsearch \
    && for path in \
    /elasticsearch/config \
    /elasticsearch/config/scripts \
    /elasticsearch/plugins \
    ; do \
    mkdir -p "$path"; \
    chown -R elasticsearch:elasticsearch "$path"; \
    done \
    && rm -rf /tmp/* \
    && apk del --purge .build-deps

ENV PATH /elasticsearch/bin:$PATH

WORKDIR /elasticsearch

# Copy config dir
COPY config /elasticsearch/config

# Copy startup script
COPY run-elasticsearch.sh /run-elasticsearch.sh
RUN chmod +x /run-elasticsearch.sh

CMD ["/bin/bash","/run-elasticsearch.sh"]