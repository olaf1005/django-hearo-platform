from rethinkdb import r
import random


class InstallTarTar(object):
    def __init__(self, context):
        self.context = context

    def reinstall(self):
        x = self.context.getService("rethink")
        host = random.choice(x["nodelist"])
        rc = r.connect(host=host, port=28015).repl()

        try:
            r.db_drop(x["name"]).run(rc)
        except:
            pass

        rc.close()
        self.install()

    def install(self):
        x = self.context.getService("rethink")
        host = random.choice(x["nodelist"])
        rc = r.connect(host=host, port=28015).repl()

        r.db_create(x["name"]).run(rc)

        for table in x["tables"]:
            r.db(x["name"]).table_create(
                table["name"], primary_key=table["primary_key"]
            ).run(rc)
