import os
import json

from rethinkdb import r

db_name = os.getenv("RETHINKDB_DB_NAME")
db_host = os.getenv("RETHINKDB_HOST")
conn = r.connect(host=db_host, port=28015).repl()

importpath = "upgrade_rethinkdb/rethinkdb_export_2015-03-24T11:48:38+00:00_24428/prod"

for table in [
    "changes",
    "downloads",
    "downloads_changes",
    "downloads_lock",
    "images",
    "in_process",
    "songs",
    "images_changes",
    "process",
    "failures",
    "images_lock",
    "services",
]:
    r.db(db_name).table(table).delete()

    for line in open("{}/{}".format(importpath, table)):
        r.db(db_name).table(table).insert(json.loads(line)).run()
