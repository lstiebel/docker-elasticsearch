#!/bin/bash

# Check if snapshot repository exists, try to create it
RESPONSE="$(curl -s -XGET http://${ELASTICSEARCH_HOST}:9200/_snapshot/${CLUSTERNAME}-${ENVIRONMENT}-snapshot/${START_DATE} | jq -r '.status')"

if [ "$RESPONSE" == "404" ] ; then
  REPOSITORY="{ \"type\": \"s3\", \"settings\": \
   { \"access_key\": \"${AWS_ACCESS_KEY}\", \
   \"secret_key\": \"${AWS_SECRET_KEY}\", \
   \"protocol\": \"https\", \
   \"bucket\": \"com-dodax-${CLUSTERNAME}-${ENVIRONMENT}-elasticsearch-snapshot\", \
   \"region\": \"${AWS_REGION}\", \
   \"storage_class\": \"${S3_STORAGE_CLASS}\"}"
  curl -X PUT -d "$RESPONSE" "http://${ELASTICSEARCH_HOST}:9200/_snapshot/${CLUSTERNAME}-${ENVRIONMENT}-snapshot"
fi

# trigger snapshot, wait until finish
START_DATE="$(date +%Y-%m-%d_%H-%M-%S)"
curl -XPUT "http://${ELASTICSEARCH_HOST}:9200/_snapshot/${CLUSTERNAME}-${ENVIRONMENT}-snapshot/${START_DATE}?wait_for_completion=${WAIT_FOR_COMPLETION}"