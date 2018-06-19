#!/bin/bash

# provision elasticsearch user
addgroup sudo
adduser -D -g '' elasticsearch
adduser elasticsearch sudo
chown -R elasticsearch /elasticsearch /data
echo '%sudo ALL=(ALL) NOPASSWD:ALL' >>/etc/sudoers

# allow for memlock
ulimit -l unlimited

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
		printf "\n%s\n" "node.rack_id: ${SHARD_ALLOCATION_AWARENESS_ATTR}" >>/elasticsearch/config/elasticsearch.yml
	fi
	if [ "$NODE_MASTER" == "true" ]; then
		printf "\n%s\n" "cluster.routing.allocation.awareness.attributes: ${SHARD_ALLOCATION_AWARENESS}" >>/elasticsearch/config/elasticsearch.yml
	fi
fi

if [ ! -z "${ES_PLUGINS_INSTALL}" ]; then
	OLDIFS=$IFS
	IFS=','
	for plugin in ${ES_PLUGINS_INSTALL}; do
		if ! sudo -E -u elasticsearch /elasticsearch/bin/plugin list | grep -qs "${plugin}"; then
			until sudo -E -u elasticsearch /elasticsearch/bin/plugin install "${plugin}"; do
				echo "failed to install ${plugin}, retrying in 3s"
				sleep 3
			done
		fi
	done
	IFS=$OLDIFS
fi

# run
sudo -E -u elasticsearch /elasticsearch/bin/elasticsearch
