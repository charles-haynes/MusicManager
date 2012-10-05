#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cached_file
from datetime import datetime
import metadata
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

    def __init__(self, file_db, log_every_count_files_added = 1000):
        self.file_db = file_db
        self.added_count = 0
        self.log_every_count_files_added = log_every_count_files_added

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
            mf = metadata.Metadata(pathname, size)
            my_metadata = mf.metadata()
            # the rest of this logic should be cachedFile updating
            # the cache
            try:
                cf.digest = my_metadata['digest']
            except KeyError:
                pass
            try:
                cf.tags=pymongo.binary.Binary(
                    pickle.dumps(my_metadata['tags'], pickle.HIGHEST_PROTOCOL))
            except KeyError:
                pass

        return self.add(cf, pathname)

    def id_for_path(self, pathname):
        pathname = os.path.abspath(pathname)
        path_elements = pathname.split(os.sep)
        path=os.sep
        parent = self.id(path, '', None)
        for element in path_elements[1:]:
            path = os.path.join(path, element)
            parent = self.id(path, element, parent)
        return parent

    def add_tree(self, parent_name, parent_id):
        '''recursively descend the directory tree rooted at top,
           calling the callback function for each regular file'''

        for child_name in os.listdir(parent_name):
            pathname = os.path.join(parent_name, child_name)
            try:
                _id = self.id(pathname, child_name, parent_id)
            except OSError as exc:
                warn('"{}": {}'.format(pathname, exc))
                continue

            try:
                self.add_tree(pathname, _id)
            except OSError:
                pass

    def add(self, cached_file, pathname):
        self.added_count += 1
        if ((self.log_every_count_files_added > 0)
            and (self.added_count % self.log_every_count_files_added) == 0):
            logging.info(pathname)
        cached_file.id = self.file_db.save(cached_file.__dict__)
        print "saved {}".format(pathname)
        return cached_file.id

    def delete(self, cached_file):
        self.file_db.delete(cached_file.id)

    def copy(self, cached_file, location):
        # make a copy of the existing record, with a new location
        # compute the parent and name of the new location
        # see if it already exists
        # save it
        return self.file_db.save(cached_file.__dict__)

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

