# test callmemaybe
#
# uploads a song to the CDN
import os
import uuid
import random
import time
import threading

import boto
from boto.s3.key import Key
from boto.s3.connection import S3Connection
from boto.s3.bucket import Bucket

from tartar import CallMeMaybe
from infrared import Cred

import Queue


queue = Queue.Queue()


class UploadMe(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

        self.cmm = CallMeMaybe(True)
        s3cred = Cred.Amazon()
        self.s3conn = S3Connection(s3cred.username(), s3cred.secret())

    def run(self):
        while True:
            self.filename = self.queue.get()
            self.songid = str(uuid.uuid4())
            self.prefix = str(random.randint(100000, 999999))

            keyname = self.prefix + "_" + self.filename

            print("uploading " + str(self.cmm.register(self.songid, keyname, "user1", CallMeMaybe.Song)))

            k = Key(self.s3conn.get_bucket(os.getenv('S3_BUCKET'))
            k.key = keyname
            k.set_contents_from_filename("./testfiles/" + self.filename)

            print(keyname + " uploaded!")

            # self.cmm.register_marktobeprocessed(self.songid)
            self.queue.task_done()
            if self.queue.empty():
                break


mypath = "./testfiles/"
onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]

for i in range(3):
    t = UploadMe(queue)
    t.daemon = True
    t.start()

for f in onlyfiles:
    queue.put(f)

queue.join()

print("closing connections...")
time.sleep(10)
