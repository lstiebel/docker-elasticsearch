#!/usr/bin/env python3

import os
import datetime
import argparse
from es import connect_to_cluster
from es import get_indices
from es import get_repositories
from es import create_repository
from es import purge_repositories
from es import create_snapshot
from es import close_index
from es import get_latest_snapshot
from es import get_repositories


def create_new_snapshot(es):
    """
    Create new snapshot and repository (new repo monthly)
    Parameters:
        es: Elasticsearch connection object
    """
    s3_bucket = os.environ['S3_BUCKET']
    region = os.environ['AWS_DEFAULT_REGION']
    access_key = os.environ['AWS_ACCESS_KEY_ID']
    secret_key = os.environ['AWS_SECRET_ACCESS_KEY']

    # determine date ('2018-03')
    timestamp_month = datetime.datetime.today().strftime('%Y-%m')
    # get list of repositories, check if repo already exists or we need to create it
    repositories = get_repositories(es)
    if timestamp_month in repositories:
        print("[INFO] Found repo with date %s" % (timestamp_month))
        # use timestamp as name for snapshot
        timestamp_snapshot = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        indices = get_indices(es)
        create_snapshot(es=es, indices=indices, repository=timestamp_month,
                        snapshot_name=timestamp_snapshot)

    else:
        # create repo if not present, verify after creation
        create_repository(es=es, repository_name=timestamp_month, s3_bucket=s3_bucket, s3_base_path=timestamp_month,
                          region=region, access_key=access_key, secret_key=secret_key)
        # use timestamp as name for snapshot
        timestamp_snapshot = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        indices = get_indices(es)
        create_snapshot(es=es, indices=indices, repository=timestamp_month,
                        snapshot_name=timestamp_snapshot)


if __name__ == "__main__":
    """
    Parse command line arguments, connect to ES, invoke actions
    """
    parser = argparse.ArgumentParser(
        description='Create and rotate snapshots and repositories on S3 for Elasticsearch. \
                     Confguration via environment variables and arguments.')
    config = parser.add_argument_group('parameters')
    config.add_argument('-m', '--mode', help="Mode of operation. Choose 'create' or 'restore'",
                        choices=['create', 'restore'], default='create', required=False)
    args = parser.parse_args()

    address = os.environ['ES_CLIENT_ADDRESS']
    retention_time = int(os.environ['ES_SNAPSHOT_RETENTION_TIME'])
    es = connect_to_cluster(address)

    if args.mode == 'create':
        create_new_snapshot(es)
        purge_repositories(es=es, retention_time=retention_time)
    if args.mode == 'restore':
        print("Todo")
        # repository = os.environ['ES_REPOSITORY_RESTORE']
        # snapshot = os.environ['ES_SNAPSHOT_RESTORE']

        # indices = get_indices(es)
        # for index in indices:
        #    close_index(es=es, index=index)
        
        # restore_snapshot(es)
        # reopen_indices(es)
