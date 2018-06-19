#!/bin/bash

BASE=/elasticsearch

# allow for memlock if enabled
if [ "$MEMORY_LOCK" == "true" ]; then
	ulimit -l unlimited
fi

# Set a random node name if not set.
if [ -z "${NODE_NAME}" ]; then
	NODE_NAME=$(uuidgen)
fi
export NODE_NAME=${NODE_NAME}

# Create a temporary folder for Elasticsearch ourselves.
# Ref: https://github.com/elastic/elasticsearch/pull/27659
export ES_TMPDIR=$(mktemp -d -t)

# Prevent "Text file busy" errors
sync

if [ ! -z "${ES_PLUGINS_INSTALL}" ]; then
	OLDIFS=$IFS
	IFS=','
	for plugin in ${ES_PLUGINS_INSTALL}; do
		if ! $BASE/bin/elasticsearch-plugin list | grep -qs "${plugin}"; then
			until $BASE/bin/elasticsearch-plugin install --batch "${plugin}"; do
				echo "failed to install ${plugin}, retrying in 3s"
				sleep 3
			done
		fi
	done
	IFS=$OLDIFS
fi

# Set RACK_ID to AWS AZ

AWS_AZ="$(curl -s -m 2 http://169.254.169.254/latest/meta-data/placement/availability-zone)"
wait

if [ -z "$AWS_AZ" ]; then
	SHARD_ALLOCATION_AWARENESS_ATTR="local"
else
	SHARD_ALLOCATION_AWARENESS_ATTR="$AWS_AZ"
fi

if [ ! -z "${SHARD_ALLOCATION_AWARENESS_ATTR}" ] && ! grep "${SHARD_ALLOCATION_AWARENESS}" "$BASE/config/elasticsearch.yml"; then
	if [ "$NODE_DATA" == "true" ]; then
		NODE_NAME="${ES_SHARD_ATTR}-${NODE_NAME}"
		printf "\n%s\n" "node.attr.${SHARD_ALLOCATION_AWARENESS}: ${SHARD_ALLOCATION_AWARENESS_ATTR}" >>$BASE/config/elasticsearch.yml
	fi
	if [ "$NODE_MASTER" == "true" ]; then
		printf "\n%s\n" "cluster.routing.allocation.awareness.attributes: ${SHARD_ALLOCATION_AWARENESS}" >>$BASE/config/elasticsearch.yml
	fi
fi

# run
if [[ $(whoami) == "root" ]]; then
	chown -R elasticsearch:elasticsearch $BASE
	chown -R elasticsearch:elasticsearch /data
	exec su-exec elasticsearch $BASE/bin/elasticsearch
else
	# the container's first process is not running as 'root',
	# it does not have the rights to chown. however, we may
	# assume that it is being ran as 'elasticsearch', and that
	# the volumes already have the right permissions. this is
	# the case for kubernetes for example, when 'runAsUser: 1000'
	# and 'fsGroup:100' are defined in the pod's security context.
	$BASE/bin/elasticsearch
fi
