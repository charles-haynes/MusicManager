#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pdb

import bson
from datetime import datetime
import grp
import logging
import logging.config
import os
import pickle
import populate_db_mp3
import pwd
import pymongo
import pymongo.binary
from stat import *
import sys
from warnings import warn

TEXT_ENCODING = 'utf8'

class CachedFile():
    def __init__(self, file_name, stat, parent_id):
        self.name = file_name
        self.parent = parent_id
        self.mode = stat.st_mode
        self.inode = stat.st_ino
        self.size = stat.st_size
        self.mtime = datetime.fromtimestamp(stat.st_mtime)

    def hasChanged(self,prev_file):
        return (
            not (prev_file['mtime'] >= self.mtime)
            or not (prev_file['size'] == self.size)
            or not (prev_file['inode'] == self.inode)
            or not ('mp3' in prev_file))

    def isRegularFile(self):
        return S_ISREG(self.mode)

    def isDirectory(self):
        return S_ISDIR(self.mode)

class FileCache():

    def __init__(self, mongo_file_db, on_changed=None, log_every_count_files = 1000):
        self.files = mongo_file_db
        self.count = 0
        self.log_every_count_files = log_every_count_files
        self.on_changed = on_changed

    def add_tree(self, parent_name, parent_id):
        '''recursively descend the directory tree rooted at top,
           calling the callback function for each regular file'''

        for child_name in os.listdir(parent_name):
            pathname = os.path.join(parent_name, child_name)
            try:
                st = os.lstat(pathname)
            except OSError as exc:
                warn('"%s": %s' % (pathname, exc))
                continue
            _id = self.visit_file(child_name, st, parent_id, pathname)
            self.count += 1
            if (self.log_every_count_files > 0) and (self.count % self.log_every_count_files) == 0:
                logging.info(pathname)

            if S_ISDIR(st.st_mode):
                self.add_tree(pathname, _id)

    @staticmethod
    def bson_sanitize_string(s):
        if isinstance(s, unicode):
            return s.encode("utf-8")
        try:
            s.decode('utf-8')
        except UnicodeDecodeError:
            print "UnicodeDecodeError Value: %s, %r" % (k, v)
            s=pymongo.binary.Binary(s)
        return s
        
    @staticmethod
    def pymongo_sanitize_dict(dict):
        return [(FileCache.bson_sanitize_string(k), FileCache.bson_sanitize_string(str(v))) for k,v in dict.iteritems()]

    def visit_file(self, file_name, stat, parent_id, pathname):
        file=CachedFile(file_name, stat, parent_id)

        prev_file = self.files.find_one(
            {'name': file.name,'parent': file.parent},
            fields=('mtime','size','inode','_id','mp3'))

        # hasChanged should be internal to file
        # file should provide a method that returns file_info
        # it should return cached if not hasChanged (and cache exists)
        # it should take a filename and a cached value and say if the
        # cached value is stale
        if prev_file and not file.hasChanged(prev_file):
            return prev_file['_id']

        # on_changed should be a notifier, taking a file? be internal
        # to File? on_changed is badly named, it actually (re-)computes the
        # value to be cached.
        if file.isRegularFile():
            mp3_info = self.on_changed(pathname, stat.st_size)
            # the rest of this logic should be cached file updating
            # the cache
            try: mp3_info['tags'] = FileCache.pymongo_sanitize_dict(mp3_info['tags'])
            except KeyError: pass
            file.mp3 = mp3_info

        try:
            bson_doc = bson.BSON.encode(file.__dict__,check_keys=True)
        except bson.errors.InvalidStringData:
            print repr(file.__dict__)

        print "saved %s" % (pathname,)
        return self.files.save(file.__dict__)

def on_changed(file_name, size):
    return populate_db_mp3.get_mp3_info(file_name, size)

if __name__ == '__main__':
    logging.captureWarnings(True)
    file_db = FileCache(pymongo.Connection().test.files, 1)
    file_db.on_changed = on_changed

    fpath = sys.argv[1] if (len(sys.argv) > 1) else os.getcwd()
    _id = file_db.visit_file(fpath, os.lstat(fpath), None, fpath)
    file_db.add_tree(fpath, _id)
