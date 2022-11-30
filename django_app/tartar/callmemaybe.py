import os
import time
import base64
import hmac
import hashlib
import uuid
import urllib.request, urllib.parse, urllib.error
import re

from .thriftshop import ThriftShop


S3_BUCKET = os.getenv("S3_BUCKET")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")


def unique_name(original_name):
    # remove all non ascii characters which cause problems
    original_name = re.sub(r"[^\x00-\x7f]", r"", original_name)
    return "CMM_{}-{}".format(str(uuid.uuid4()), original_name)


class CallMeMaybe(ThriftShop):
    """
    A thin API for cloud file management for tune.fm

    This API is used for file uploading, getting file status,
    and fetching public URLs

    cmm = CallMeMaybe()

    cmm.register(songid, filename, userid, CallMeMaybe.Song)

    cmm.register(imgid, filename, userid, CallMeMaybe.Image.profile)


    check on the song with:
    cmm.whatstage(objid, resourcetype)


    to fetch the url for a song or image
    cmm.getpublicurl(objid,resourcetype)


    Mechanism to update an existing song!
    Backburner
        localcaching for streaming urls
        memorycaching for streaming urls
    """

    @staticmethod
    def generate_signature(objectname, mime, expiration=1000):
        name = unique_name(objectname).replace(" ", "")
        s3_secret_key = S3_SECRET_KEY.encode("utf-8")

        amz_headers = "x-amz-acl:public-read"

        expires = int(time.time() + expiration)
        signature = b""
        while not signature or b"+" in signature:
            expires += 1  # huge hack, gotta change the hash somehow...
            put_request = "PUT\n\n{}\n{:d}\n{}\n/{}/{}".format(
                mime, expires, amz_headers, S3_BUCKET, name
            )

            signature = base64.encodestring(
                hmac.new(
                    s3_secret_key, put_request.encode("ascii"), hashlib.sha1
                ).digest()
            )

        signature = urllib.parse.quote(signature.strip())
        url = "https://{}.s3.amazonaws.com/{}".format(S3_BUCKET, name)

        signed_request = (
            urllib.parse.quote(
                "{}?AWSAccessKeyId={}&Expires={:d}&Signature=".format(
                    url, S3_ACCESS_KEY, expires
                )
            )
            + signature
        )

        return {"signed_request": signed_request, "url": url, "name": name}

    def register(self, objid, filename, userid, resourcetype):
        """
        register a song as being uploaded
        """

        # sets base dict
        ins = resourcetype.schema()

        # sets the primary key

        # sets other fields
        ins["created"] = int(time.time())
        ins["status"] = 0
        ins["user"] = userid
        ins["marked"] = 0
        ins["percent"] = 0
        ins["filename"] = filename

        t = self.inserthelper(
            objid, resourcetype, ins, resourcetype.table_process(), throwexception=True
        )

        return objid

    def isready(self, objid, resourcetype):
        """
        function: isready()
        accepts:  objid   the id of the object
                    resourcetype, the resourcetype of the object
        returns:  True if the song is ready and online, False otherwise

        is a song ready?
        """
        t = self.gethelper(objid, resourcetype, throwexception=False)
        return t is not None

    def hasfailed(self, objid, resourcetype):
        """
        function: hasfailed)
        accepts:  objid   the id of the object
                    resourcetype, the resourcetype of the object
        returns:  True if the song has failed, false otherwise

        is a song ready?
        """

        t = self.gethelper(
            objid, resourcetype, resourcetype.table_failed(), throwexception=False
        )
        return t is not None

    def getpercent(self, objid, resourcetype):
        """
        returns a percentage based off this scheme:

        0 - uploading
        10 - uploaded
        10-70 some percentage of waiting queue
        70-100 stages based on progress
        100 - done
        -1 the file failed
        -2 the file is not in the system #could be inaccurate
        """
        t = {"percent": -2}
        try:
            t = self.gethelper(objid, resourcetype, resourcetype.table_process())
        except:
            if self.isready(objid, resourcetype):
                return 100
            elif self.hasfailed(objid, resourcetype):
                return -1

        if t["percent"] == 0:
            return 0
        elif t["percent"] == 10:

            per = 60 - (60 * (t["bytesahead"] / t["bytestotal"]))
            return per + 10
        else:
            return t["percent"]

    def setmeta(self, objid, resourcetype, meta):
        """
        #TODO error handling
        a dict, meta to be updated
        """

        if not meta:
            return False

        final = resourcetype.keys_final()

        update = {k: meta[k] for k in list(meta.keys()) if k not in final}

        self.updatehelper(objid, resourcetype, update)

        return True

    def getmeta(self, objid, resourcetype, keys=None):
        """
        inputs:  objid - the id of the object
                    keys   - an array of String keys

        outputs: a dict - a key map between keys and metadata

        throws FileNotFound exception
        """
        song = self.gethelper(objid, resourcetype)

        if not keys:
            keys = resourcetype.keys_default()

        return {k: song[k] for k in keys if k in song}
