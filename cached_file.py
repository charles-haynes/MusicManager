from datetime import datetime
from stat import *

class CachedFile():
    def __init__(self, name, parent, mode, inode, size, mtime):
        self.name = name
        self.parent = parent
        self.mode = mode
        self.inode = inode
        self.size = size
        self.mtime = mtime

    def hasChanged(self,cached):
        return (
            cached['mtime'] < self.mtime
            or cached['size'] != self.size
            or cached['inode'] != self.inode)

    def isRegularFile(self):
        return S_ISREG(self.mode)

    def isDirectory(self):
        return S_ISDIR(self.mode)
