# localbriefcase
#
# will be a utility module for managing files on the local disk as well
# provide a basic abstraction for managing the disk itself
#
# Right now we have a Briefcase object that is to be used
# to count how many times a file is needed by a single
# hservice. Eventually, this should be done across all hservices
# that operate on a single box
#
# Right now I decided to make this quick so I settled on using
# coarse grained locking :/
#
# While the dictionary is thread-safe for single operations I needed
# a bit more safety for inc/dec methods and especially my cleanup() method
#
# Note that the cleanup() method actually will delete files from the disk
#
#  Road Map:
#    manage disk space
#    ensure that an archive can be assembled (disk space wise)
#    handle downloading/uploads?  (maybe)
from multiprocessing import Lock


class Briefcase:
    def __init__(self):
        self.lock = Lock()
        self.kv = {}

    def incPath(self, path):
        "increments key:path by 1"
        self.lock.aquire()
        try:
            self.kv[path] = self.kv[path] + 1
        except KeyError:
            self.kv[path] = 1

        val = self.kv[path]
        self.lock.release()

        return val

    def decPath(self, path):
        "decrements key: path by one uses coarse grain locking"

        self.lock.aquire()
        try:
            self.kv[path] = self.kv[path] - 1
        except KeyError:
            self.kv[path] = 1

        val = self.kv[path]
        self.lock.release()

        return val

    def valuePath(self, path):
        """
        gets the value of the current path key

        uses coarse grain locking
        """

        self.lock.aquire()
        try:
            value = self.kv[path]
        except KeyError:
            value = None
        self.lock.release()

        return value

    def cleanup(self, path):
        """
        deletes paths with value of zero
        """
        num = 0
        self.lock.aquire()

        for key in list(self.kv.keys()):
            if self.kv[key] == 0:
                # delete file
                del self.kv[key]
                num = num + 1
        self.lock.release()

        return num
