import os
import logging

from boto.s3.key import Key
from boto.s3.connection import S3Connection
from boto.s3.bucket import Bucket
from boto.exception import S3ResponseError

from .hearostorage import HearoStorage


logger = logging.getLogger("tartar.hearos3")


class HearoS3(HearoStorage):
    """ Hearo's S3 Abstractionv
    """

    def conn(self):
        """ connects to s3
            returns the connection
        """
        c = self.context.getService("s3")

        username = os.getenv("S3_ACCESS_KEY", c["username"])
        password = os.getenv("S3_SECRET_KEY", c["password"])

        s3conn = S3Connection(username, password)

        logger.debug("connected to s3 %s", str(s3conn))

        return s3conn

    def reUpload(self, containeralias, key, path):
        """ uploads the file at path, path to
            containername on containername
        """
        s3conn = self.conn()
        bucketname = self.getcontainername(containeralias, "s3")

        k = Key(s3conn.get_bucket(bucketname))
        k.key = key
        k = k.set_contents_from_filename(path)

        ret = {}
        ret["key"] = key
        ret["public_url"] = None
        return ret

    def download(self, containeralias, key, path):
        """ Downloads a file in containername, containername to the path
        """
        s3conn = self.conn()
        bucketname = self.getcontainername(containeralias, "s3")

        fp = open(path, "wb")

        try:
            k = Key(s3conn.get_bucket(bucketname))
            k.key = key
            k.get_contents_to_file(fp)
        except S3ResponseError as e:
            logger.exception(e)
            return False

        fp.close()
        return True

    def delete(self, containeralias, key):
        """ deletes a key from s3
        """

        s3conn = self.conn()
        bucketname = self.getcontainername(containeralias, "s3")

        bucket = s3conn.get_bucket(bucketname)
        k = bucket.get_key(key)
        k.delete()

        return True

    def exists(self, containeralias, key):
        """ test if a keys exists
        """
        s3conn = self.conn()
        bucketname = self.getcontainername(containeralias, "s3")
        bucket = s3conn.get_bucket(bucketname)
        key = bucket.get_key(key)

        if not key:
            return False
        return True

    def size(self, containeralias, key):
        """ returns size of a given key
        """
        s3conn = self.conn()
        bucketname = self.getcontainername(containeralias, "s3")
        bucket = s3conn.get_bucket(bucketname)
        key = bucket.get_key(key)

        if not key:
            return False

        return key.size

    def copy_object(
        self,
        containeralias,
        src_key_name,
        dst_containeralias,
        dst_key_name,
        metadata=None,
        preserve_acl=True,
    ):
        """
        Copy an existing object to another location.

        src_bucket_name   Bucket containing the existing object.
        src_key_name      Name of the existing object.
        dst_bucket_name   Bucket to which the object is being copied.
        dst_key_name      The name of the new object.
        metadata          A dict containing new metadata that you want
                        to associate with this object.  If this is None
                        the metadata of the original object will be
                        copied to the new object.
        preserve_acl      If True, the ACL from the original object
                        will be copied to the new object.  If False
                        the new object will have the default ACL.
        """
        s3conn = self.conn()
        bucketname = self.getcontainername(containeralias, "s3")
        bucket = s3conn.lookup(bucketname)

        # Lookup the existing object in S3
        key = bucket.lookup(src_key_name)

        dst_bucketname = self.getcontainername(dst_containeralias, "s3")

        # Copy the key back on to itself, with new metadata
        return key.copy(
            dst_bucketname, dst_key_name, metadata=metadata, preserve_acl=preserve_acl
        )
