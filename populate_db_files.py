#!/usr/bin/env python
# -*- coding: utf-8 -*-

import grp
import os
import pwd
import pymongo
import sys

from datetime import datetime
from stat import *

TEXT_ENCODING = 'utf8'

count  = 0
log_every_count_files = 1000

def walktree(top, callback, top_id):
    '''recursively descend the directory tree rooted at top,
       calling the callback function for each regular file'''

    global count

    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        try:
            st = os.lstat(pathname)
        except OSError as exc:
            print '"%s": %s' % (pathname, exc)
            continue
        _id = callback(f, st, top_id)
        count += 1
        if (count % log_every_count_files) == 0: print pathname
        if S_ISDIR(st.st_mode):
            walktree(pathname, callback, _id)


def visitfile(file, stat, top_id):
    mode = stat.st_mode

    user = stat.st_uid
    try: user = pwd.getpwuid(user).pw_name
    except: pass

    group = stat.st_gid
    try: group = grp.getgrgid(group).gr_name
    except: pass
        
    file_info = {
        'name': file,
        'parent': top_id,
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
    _id = files.insert(file_info)
    return _id

if __name__ == '__main__':
    files = pymongo.Connection().test.files
    files.drop()

    fpath = sys.argv[1] if (len(sys.argv) > 1) else os.getcwd()
    _id = visitfile(fpath, os.stat(fpath), None)
    walktree(fpath, visitfile, _id)
