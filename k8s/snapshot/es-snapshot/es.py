import dateutil.parser
import datetime
import sys
from elasticsearch import Elasticsearch
from elasticsearch import NotFoundError
from aws_s3 import delete_object_from_s3


def connect_to_cluster(address):
    """
    Connect to elasticsearch cluster, returns ES client object
    Parameters:
        address: ES client node address
    """
    try:
        es = Elasticsearch([address], sniff_on_start=True, sniff_on_connection_fail=True, timeout=300,
                           sniffer_timeout=60, request_timeout=300, retry_on_timeout=True, max_retries=3)
        print("[INFO] Connected to cluster: %s" % (es.info()))
        return es

    except Exception as e:
        print("[ERROR] Error connecting to cluster: %s" % (str(e)))
        sys.exit(1)


def close_index(es, index):
    """
    Close index
    Parameters:
        es: ES client object
        index: index name, _all and wildcards possible
    """
    try:
        print("[INFO] Closing index %s" % (index))
        result = es.indices.close(index=index, allow_no_indices=True, master_timeout="5m")
        return result
    except NotFoundError:
        print("[WARN] Could not close index on target cluster: '%s'" % (index))
    except Exception as e:
        print("[ERROR] Error closing index: %s" % (str(e)))
        sys.exit(1)    


def open_index(es, index):
    """
    Open indices
    Used to ensure indices are re-opened after a restore operation
    Parameters:
        es: ElasticSearch connection object
        index: index name to open
    """
    try:
        print("[INFO] Opening index: '%s'" % (index))
        es.indices.open(index=index, ignore_unavailable=True, master_timeout="5m")
    except NotFoundError:
        print("[WARN] Could not reopen index on target cluster: '%s'" % (index))
    except Exception as e:
        print("[ERROR] Unexpected error when reopening index %s" % (str(e)))


def get_indices(es):
    """
    Get all indices in cluster
    Parameters:
        es: ES client object
    """
    try:
        indices = es.indices.get('*').keys()
        return indices

    except Exception as e:
        print("[ERROR] Error listing indices: %s" % (str(e)))
        sys.exit(1)


def get_repositories(es):
    """
    List all repositories that exist in the cluster.
    Parameters:
        es: Elasticsearch client object
    """
    try:
        repositories = es.snapshot.get_repository('*').keys()
        return repositories

    except Exception as e:
        print("[ERROR] Error listing reposotires: %s" % (str(e)))
        sys.exit(1)


def get_latest_snapshot(es, repository):
    """
    Returns name of latest successful snapshots in repo
    Parameters:
        es: Elasticsearch client object
        repository: repo to list
    """
    try:
        all_snapshots = es.snapshot.get(repository=repository, snapshot="_all")
        list_snapshots = all_snapshots['snapshots']
        # filter only successful snapshots, sort by end_time_in_milis
        list_snapshots.sort(key=lambda t: t['end_time_in_millis'])
        snapshots_successful = list(filter(lambda s: s['state'] in "SUCCESS", list_snapshots))
        latest_snapshot = snapshots_successful[-1]['snapshot']

        return latest_snapshot

    except Exception as e:
        print("[ERROR] Error getting latest snapshots: %s" % (str(e)))
        sys.exit(1) 


def verify_repository(es, repository):
    """
    Verify repository on all nodes, check for running snapshots in repo
    Parameters:
        es: Elasticsearch client object
        repository: name of snapshot repo to check
    """
    try:
        # check if snapshot for repo is already running in cluster
        running_snapshots = es.snapshot.status(repository=repository)['snapshots']
        running_snapshots_count = sum(map(len, running_snapshots))
        if running_snapshots_count > 0:
            print("[ERROR] %s snapshots already running for repository %s" % (running_snapshots_count, repository))
            sys.exit(1)

        result = es.snapshot.verify_repository(repository=repository, timeout="5m", master_timeout="5m")

        return result

    except Exception as e:
        print("[ERROR] Error verifying repository: %s" % (str(e)))
        sys.exit(1)


def create_snapshot(es, indices, repository, snapshot_name):
    """
    Take a snapshot of index specified as argument.
    Timeout is set to 5min at the moment, better solution possible.
    Parameters:
        es: Elasticsearch client object (source)
        indices: names of indices to snapshot as dict
        repository_name: name of repository, has to exist already
        snapshot_name: name of the snapshot
    """
    try:
        verify_repository(es=es, repository=repository)

        index_count = len(indices)
        index_names = ','.join(map(str, indices))
        print("[INFO] Snapshotting %s indices to S3: %s" % (index_count, index_names))
        es.snapshot.create(repository=repository,
                           snapshot=snapshot_name,
                           master_timeout="5m",
                           body={
                               "indices": index_names},
                           wait_for_completion=False)
        print("[INFO] Snapshotting triggered successfully.")

    except Exception as e:
        print("[ERROR] Error triggering snapshots: %s" % (str(e)))
        sys.exit(1)


def create_repository(es, repository_name, s3_bucket, s3_base_path, region, access_key, secret_key):
    """
    Create S3 repository
    Parameters:
        es: Elasticsearch client object (source)
        repository_name: name of the repository to be created
        s3_bucket: name of S3 bucket (has to exist already)
        s3_base_path: key in S3 bucket
        region: AWS region
        access_key: AWS access key
        secret_key: AWS secret key
    """
    try:
        print("[INFO] Creating new repository using bucket %s with base path %s" % (s3_bucket, s3_base_path))
        repository = es.snapshot.create_repository(repository=repository_name,
                                                   verify=True,
                                                   master_timeout="2m",
                                                   body={
                                                       "type": "s3",
                                                       "settings": {
                                                           "region": region,
                                                           "bucket": s3_bucket,
                                                           "base_path": s3_base_path,
                                                           "access_key": access_key,
                                                           "secret_key": secret_key
                                                        }
                                                    })
        return repository

    except Exception as e:
        print("[ERROR] Error creating repository: %s" % (str(e)))
        sys.exit(1)


def purge_repositories(es, retention_time):
    """
    Delete repositories from Elasticsearch that are older than retantion_time.
    Invoke delete_object_from_s3 on the corresponding directory in the S3 bucket
    Requires that AWS credentials are set as ENV variables or IAM role!
    Parameters:
        es: Elasticsearch client object
        retention_time: retention time as datetime.timedelta object
                        see: https://docs.python.org/3/library/datetime.html#timedelta-objects
    """
    date_cutoff = datetime.datetime.today() - datetime.timedelta(days=retention_time)
    repositories = get_repositories(es)

    for repository in repositories:
        print("[INFO] Checking repository %s" % (repository))

        try:
            # parse repo name for timestamp, check if cutoff is larger than creation date
            date_creation = dateutil.parser.parse(repository, fuzzy=True)
            if date_cutoff > date_creation:
                print("[INFO] Found outdated repository %s, removing it from Elasticsearch." % (repository))
                # determine S3 bucket from repo config
                try:
                    bucket = es.snapshot.get_repository(repository).values()[0]['settings']['bucket']
                except Exception as e:
                    print("[ERROR] Error getting S3 bucket from ES repo configuration: %s" % (str(e)))
                # delete repo from ES
                try:
                    es.snapshot.delete_repository(repository=repository)
                except Exception as e:
                    print("[ERROR] Error deleting from S3: %s" % (str(e)))
                # actually delete object from S3, requires IAM role or AWS credentials as env variables
                delete_object_from_s3(bucket=bucket, key=date_creation)

            else:
                print("[INFO] Repository %s not old enough for removal, keeping it." % (repository))

        except Exception as e:
            print("[ERROR] Error purging repository: %s" % (str(e)))
            sys.exit(1)


def restore_snapshot(es, index, repository_name, snapshot_name, replicas):
    """
    Restore the specified index from the snapshot.
    Elasticsearch automatically replicates the indices across the ES cluster after the restore.
    Parameters:
        index: name of index to snapshot
        es: Elasticsearch client object (destination)
        repository_name: name of repository, has to exist already
        snapshot_name: name of the snapshot
    """
    try:
        print("[INFO] Restoring ES index %s from snapshot %s" % (index, snapshot_name))
        es.snapshot.restore(repository=repository_name,
                            snapshot=snapshot_name,
                            body={
                                "indices": index},
                            wait_for_completion=False)
    except Exception as e:
        print("[ERROR] Error restoring snapshot: %s" % (str(e)))