from rethinkdb import r

# import sys
# sys.path.append("/home/crew/TarTar")
from tartar import GangnamStyle
from infrared import Context

from disco import Format
from disco import Package

import random

context = Context()
db = context.getDB_local()

ret = db.table("songs").pluck("songid").run()
cnt = db.table("songs").pluck("songid").count().run()

print(ret)


def r(ret):
    return ret[random.randint(0, cnt - 1)]["songid"]


g = GangnamStyle()


arr = [r(ret)]
p = Package()
p.pack(Format.MP3_320(), arr)
zero = g.requestdownload("user1", p)


arr1 = [r(ret), r(ret), r(ret), r(ret)]
arr2 = [r(ret), r(ret), r(ret)]
arr3 = [r(ret), r(ret), r(ret)]
arr4 = [r(ret), r(ret)]


p1 = Package()
p1.pack(Format.MP3_320(), arr1)
p1.pack(Format.FLAC(), arr2)
p1.pack(Format.WAV(), arr3)

p2 = Package()
p2.pack(Format.MP3_320(), arr2)

p3 = Package()
p3.pack(Format.FLAC(), arr3)

p4 = Package()
p4.pack(Format.WAV(), arr4)

one = g.requestdownload("user1", p1)
two = g.requestdownload("user1", p2)
thr = g.requestdownload("user1", p3)
fou = g.requestdownload("user1", p4)

print(g.status(one))
print(g.status(two))
print(g.status(thr))
print(g.status(fou))
