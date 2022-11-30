import os

from rethinkdb import r

db_name = os.getenv("RETHINKDB_DB_NAME")
db_host = os.getenv("RETHINKDB_HOST")
conn = r.connect(host=db_host, port=28015).repl()

try:
    r.db_drop("test").run()
except:
    pass

try:
    r.db_drop(db_name).run()
except:
    pass

r.db_create(db_name).run()

# main song url mapping
r.db(db_name).table_create("songs", primary_key="songid").run()

# distributed lock table
r.db(db_name).table_create("in_process", primary_key="songid").run()

# songs to be processed
r.db(db_name).table_create("process", primary_key="songid").run()

# uploads that failed during conversion
r.db(db_name).table_create("failures", primary_key="songid").run()
r.db(db_name).table_create("changes", primary_key="songid").run()
r.db(db_name).table_create("downloads", primary_key="downloadid").run()
r.db(db_name).table_create("downloads_lock", primary_key="downloadid").run()
r.db(db_name).table_create("downloads_changes", primary_key="downloadid").run()

# images
r.db(db_name).table_create("images", primary_key="imageid").run()
r.db(db_name).table_create("images_lock", primary_key="imageid").run()
r.db(db_name).table_create("images_changes", primary_key="imageid").run()

# services
r.db(db_name).table_create("services", primary_key="id").run()

print(r.db(db_name).table_list().run())
