import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key


def connection():
    return S3Connection(os.getenv("S3_ACCESS_KEY"), os.getenv("S3_SECRET_KEY"))


def setup(bucket, filename=None):
    """
    Abstraction. Just creates the useful objects
    given a bucket name and file name
    """
    conn = connection()
    bucket = conn.create_bucket(bucket)

    if not filename:
        return conn, bucket

    key = Key(bucket)
    key.key = filename

    return conn, bucket, key


def upload_file(content, bucket, filename):
    "PUT a file"
    conn, bucket, key = setup(bucket, filename)
    key.set_contents_from_string(content)

    bucket.set_acl("public-read", filename)
    return filename


def delete_file(bucket, filename):
    "Permanently DELETE a file"
    conn, bucket, key = setup(bucket, filename)
    bucket.delete_key(key)

    return True


def all_files(bucket):
    conn, bucket = setup(bucket)
    return bucket.list()


def get_file(bucket, filename):
    conn, bucket = setup(bucket)
    key = bucket.lookup(filename)
    if not key:
        key = Key(bucket)
        key.key = filename
        key.set_contents_from_string("")
    return key
