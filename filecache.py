#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cached_file
from datetime import datetime
import FileWithMetadata
import logging
import os
import os.path
import cPickle as pickle
import pymongo
import pymongo.binary
from stat import S_ISDIR
import string
import sys
from warnings import warn

TEXT_ENCODING = 'utf8'

class FileCache(object):

    def __init__(self, file_db, log_every_count_files = 1000):
        self.file_db = file_db
        self.count = 0
        self.log_every_count_files = log_every_count_files

    def id(self, pathname, name, parent):
        stat = os.lstat(pathname)
        size=stat.st_size

        cached_info = self.file_db.find_one({'name': name,'parent': parent})
        
        cf = cached_file.CachedFile.FromStat(self, None, stat)

        # hasChanged should be internal to file
        # file should provide a method that returns file_info
        # it should return cached if not hasChanged (and cache exists)
        # it should take a filename and a cached value and say if the
        # cached value is stale
        if cached_info and not cf.hasChanged(cached_info):
            return cached_info['_id']

        if cf.isRegularFile:
            mf = FileWithMetadata.FileWithMetadata(pathname, size)
            metadata = mf.metadata()
            # the rest of this logic should be cachedFile updating
            # the cache
            try:
                cf.digest = metadata['digest']
            except KeyError:
                pass
            try:
                cf.tags=pymongo.binary.Binary(
                    pickle.dumps(metadata['tags'], pickle.HIGHEST_PROTOCOL))
            except KeyError:
                pass

        return self.add(cf, pathname)

    def add_tree(self, parent_name, parent_id):
        '''recursively descend the directory tree rooted at top,
           calling the callback function for each regular file'''

        for child_name in os.listdir(parent_name):
            pathname = os.path.join(parent_name, child_name)
            try:
                _id = self.id(pathname, child_name, parent_id)
            except OSError as exc:
                warn('"%s": %s' % (pathname, exc))
                continue
            self.count += 1
            if (self.log_every_count_files > 0) and (self.count % self.log_every_count_files) == 0:
                logging.info(pathname)

            try: self.add_tree(pathname, _id)
            except OSError: pass

    def add(self, cached_file, pathname):
        cached_file.id = self.file_db.save(cached_file.__dict__)
        print "saved {}".format(pathname)
        return cached_file.id

    def delete(self, cached_file):
        self.file_db.delete(cached_file.id)

    def copy(self, cached_file, location):
        # make a copy of the existing record, with a new location
        return self.file_db.save()

    def rename(self, cached_file, location):
        # change name and parent to match location
        parent, name = os.path.split(location)
        id = self.copy(cached_file, location)
        self.delete(cached_file)
        return id

    def full_path(self, id):
        if id is None:
            return os.sep
        row=self.file_db.find_one({'_id':id},{'name':1,'parent':1})
        return os.path.join(self.full_path(row['parent']), row['name'])

