class Radioactive(object):
    "Radioactive is an api for getting gross and information about files in the TarTar System"

    def __init__(self):
        self.context = Context()
        self.db = self.context.getDB_local()

    def get_failures(self):
        self.db.table("failures").run()

    def get_process(self):
        self.db.table("process").run()

    def get_songs(self, up=100, bottom=0):
        self.db.table("songs").run()

    def get_songbyid(self, songid):
        pass
