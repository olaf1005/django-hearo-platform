# Superclass for abstracted objects:
#   1. HearoS3
#   2. HearoCloudFiles

from .context import Context


class HearoStorage(object):
    def __init__(self, context):

        self.context = context
        if self.context is None:
            self.context = Context

    def upload(self, containername, path, suffix=None):
        # fetches a new uuid
        key = self.context.getUUID(suffix=suffix)
        # upload the file
        obj = self.reUpload(containername, key, path)

        return obj

    def reUpload(self, containername, key, path):
        raise NotImplementedError()

    def getcontainername(self, containername, servicename):
        """ returns the physical containername
            for the alias containername
        """

        return self.context.getService(servicename)["instances"][containername][
            "container"
        ]
