import boto3


def delete_object_from_s3(bucket, key):
    """
    Delete object from S3 bucket
    Parameters:
        bucket: S3 bucket
        key: object to delete
    """
    try:
        print("[INFO] Deleting key %s from bucket %s" % (key, bucket))
        s3 = boto3.resource('s3')
        response = s3.Object(bucket, key).delete()
        return response
    except Exception as e:
        print("[ERROR] Error deleting from S3: %s" % (str(e)))
