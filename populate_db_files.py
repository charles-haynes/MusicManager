#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

class FileDb():

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


    def visit_file(self, file_name, stat, parent_id, pathname):
        mode = stat.st_mode

        user = stat.st_uid
        try: user = pwd.getpwuid(user).pw_name
        except: pass

        group = stat.st_gid
        try: group = grp.getgrgid(group).gr_name
        except: pass

        file_info = {
            'name': file_name,
            'parent': parent_id,
            'format': [],
            'mode' : oct(S_IMODE(mode)),
            'inode' : stat.st_ino,
            'device' : stat.st_dev,
            'links' : stat.st_nlink,
            'user' : user,
            'group' : group,
            'size' : stat.st_size,
            'atime' : datetime.fromtimestamp(stat.st_atime),
            'mtime' : datetime.fromtimestamp(stat.st_mtime),
            'ctime' : datetime.fromtimestamp(stat.st_ctime)
            }


        if S_ISDIR(mode): file_info['format'].append('dir')
        if S_ISCHR(mode): file_info['format'].append('chr')
        if S_ISBLK(mode): file_info['format'].append('blk')
        if S_ISREG(mode): file_info['format'].append('reg')
        if S_ISFIFO(mode): file_info['format'].append('fifo')
        if S_ISLNK(mode): file_info['format'].append('lnk')
        if S_ISSOCK(mode): file_info['format'].append('sock')

        prev_file = self.files.find_one(
            {'name': file_info['name'],'parent': file_info['parent']},
            fields=('mtime','device','size','inode','_id','mp3'))

        if prev_file:
            if not S_ISREG(mode):
                return prev_file['_id']
            if ((prev_file['mtime'] >= file_info['mtime'])
            and (prev_file['size'] == file_info['size'])
            and (prev_file['device'] == file_info['device'])
            and (prev_file['inode'] == file_info['inode'])
            and ('mp3' in prev_file)):
                return prev_file['_id']
            print "changed ***", 
            if not (prev_file['mtime']>=file_info['mtime']):
                print 'mtime',prev_file['mtime'],'>=',file_info['mtime']
            if not (prev_file['size']==file_info['size']):
                print 'size ',prev_file['size'],'==',file_info['size']
            if not (prev_file['device']==file_info['device']):
                print 'device ',prev_file['device'],'==',file_info['device']
            if not (prev_file['inode']==file_info['inode']):
                print 'inode ',prev_file['inode'],'==',file_info['inode']
            if not ('mp3' in prev_file):
                print 'mp3 attribute ','mp3' in prev_file

        if self.on_changed and S_ISREG(mode):
            mp3_info = self.on_changed(pathname, stat.st_size)
            try:
                tags=[]
                for k,v in mp3_info['tags'].iteritems():
                    string=str(v)
                    if isinstance(string, unicode):
                        string=string.encode("utf-8")
                    else:
                        try:
                            string.decode('utf-8')
                        except UnicodeDecodeError:
                            string=pymongo.binary.Binary(string)
                            print "UnicodeDecodeError: %s, %r" % (k, v)
                    tags.append((k,string))
                mp3_info['tags']=tags
            except KeyError:
                pass
            file_info['mp3'] = mp3_info
            bson_doc = bson.BSON.encode(file_info,check_keys=True)

        id = self.files.save(file_info)
        print "saved %s, id %s" % (pathname,id)
        return id

def on_changed(file_name, size):
    return populate_db_mp3.get_mp3_info(file_name, size)

if __name__ == '__main__':
    logging.captureWarnings(True)
    file_db = FileDb(pymongo.Connection().test.files, 1)
    file_db.on_changed = on_changed

    fpath = sys.argv[1] if (len(sys.argv) > 1) else os.getcwd()
    _id = file_db.visit_file(fpath, os.lstat(fpath), None, fpath)
    file_db.add_tree(fpath, _id)
