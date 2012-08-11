#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pdb

import bson
import cached_file
from datetime import datetime
import grp
import logging
import logging.config
import os
import os.path
import pickle
import populate_db_mp3
import pwd
import pymongo
import pymongo.binary
from stat import S_ISDIR
import sys
from warnings import warn

TEXT_ENCODING = 'utf8'

class FileCache():

    def __init__(self, file_db, on_changed=None, log_every_count_files = 1000):
        self.file_db = file_db
        self.count = 0
        self.log_every_count_files = log_every_count_files
        self.on_changed = on_changed

    def id(self, name, parent, mode, inode, size, mtime, pathname):
        cached_info = self.file_db.find_one({'name': name,'parent': parent})
        
        file = cached_file.CachedFile(name, parent, mode, inode, size, mtime)

        # hasChanged should be internal to file
        # file should provide a method that returns file_info
        # it should return cached if not hasChanged (and cache exists)
        # it should take a filename and a cached value and say if the
        # cached value is stale
        if cached_info and not file.hasChanged(cached_info):
            return cached_info['_id']

        # on_changed should be a notifier, taking a file? be internal
        # to File? on_changed is badly named, it actually (re-)computes the
        # value to be cached.
        if file.isRegularFile():
            mp3_info = self.on_changed(pathname, size)
            # the rest of this logic should be cached file updating
            # the cache
            try: mp3_info['tags'] = FileCache.pymongo_sanitize_dict(mp3_info['tags'])
            except KeyError: pass
            file.mp3 = mp3_info

        try:
            bson_doc = bson.BSON.encode(file.dict(),check_keys=True)
        except bson.errors.InvalidStringData:
            print repr(file.dict())

        print "saved %s" % (pathname,)
        return self.file_db.save(file.dict())

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
            print "UnicodeDecodeError Value: %s" % (s,)
            s=pymongo.binary.Binary(s)
        return s
        
    @staticmethod
    def pymongo_sanitize_dict(dict):
        return [(FileCache.bson_sanitize_string(k), FileCache.bson_sanitize_string(str(v))) for k,v in dict.iteritems()]

    def visit_file(self, file_name, stat, parent, pathname):
        return self.id(file_name, parent, stat.st_mode, stat.st_ino, stat.st_size, datetime.fromtimestamp(stat.st_mtime), pathname)


def on_changed(file_name, size):
    return populate_db_mp3.get_mp3_info(file_name, size)

if __name__ == '__main__':
    logging.captureWarnings(True)
    file_db = FileCache(pymongo.Connection().test.files, 1)
    file_db.on_changed = on_changed

    fpath = sys.argv[1] if (len(sys.argv) > 1) else os.getcwd()
    _id = file_db.visit_file(os.path.abspath(fpath), os.lstat(fpath), None, fpath)
    file_db.add_tree(fpath, _id)
