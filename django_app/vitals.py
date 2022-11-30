import os
import time

from rethinkdb import r


db_name = os.getenv("RETHINKDB_DB_NAME")
db_host = os.getenv("RETHINKDB_HOST")
c = r.connect(db_host).repl()

try:
    print("TarTar Live Stats!")
    y = 1
    for (x, s) in [
        (60, "minute"),
        (60, "hour"),
        (24, "day"),
        (7, "week"),
        (30 / 7, "30 days"),
    ]:
        y = y * x
        lb = time.time() - y
        print(s + "     seconds ago:  " + str(y))
        ts = r.db("prod").table("songs").filter(r.row["time"] > lb).count().run(c)
        tf = r.db("prod").table("failures").filter(r.row["time"] > lb).count().run(c)
        print("songs    %d" % ts)
        print("failures %d" % tf)
        print("")
except Exception as e:
    print(str(e))
print("")
print("ALL TIME:")
print("songs    %d" % r.db("prod").table("songs").count().run(c))
print("failures %d" % r.db("prod").table("failures").count().run(c))
print("process  %d" % r.db("prod").table("process").count().run(c))
print("in_p     %d" % r.db("prod").table("in_process").count().run(c))
