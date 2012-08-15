from datetime import datetime
import shutil
from stat import *

class CachedFile(object):
    def __init__(self, cache, id, mode, inode, size, mtime):
        self.cache = cache
        self.id = id
        self.mode = mode
        self.inode = inode
        self.size = size
        self.mtime = mtime

    @staticmethod
    def FromStat(cache, id, stat):
        return CachedFile(
            cache, id,
            stat.st_mode, stat.st_ino, stat.st_size, datetime.fromtimestamp(stat.st_mtime))

    def hasChanged(self,cached):
        return (
            cached['mtime'] < self.mtime
            or cached['size'] != self.size
            or cached['inode'] != self.inode)

    @property
    def isRegularFile(self):
        return S_ISREG(self.mode)

    @property
    def isDirectory(self):
        return S_ISDIR(self.mode)

    @property
    def full_path(self):
        return self.cache.full_path(self.id)

    def delete(self):
        self.cache.delete(self)
        os.remove()

    def copy(self, location):
        shutil.copy()
        self.cache.copy(self, location)
    
    def move(self, location):
        os.rename()
        self.cache.rename(self, location)

