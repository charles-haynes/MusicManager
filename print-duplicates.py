#!/usr/bin/env python
# -*- coding: utf-8 -*-

import merge_metadata
import os
import os.path
import pymongo 

def full_path(coll, row):
    if row is None:
        return os.sep
    parent=coll.find_one({'_id':row['parent']},{'name':1,'parent':1})
    return os.path.join(full_path(coll, parent),row['name'])

if __name__ == '__main__': 
  db = pymongo.Connection().test

  digests = db.mp3_dups.find({'value': {'$gt': 1}},sort=[('value',-1)])
  for digest in digests:
    dups = db.files.find({'digest': digest['_id']})
    print "*** %s: %d" % (digest['_id'], digest['value'])
    paths = [full_path(db.files, dup).encode('utf-8') for dup in dups]
    print '\n'.join(paths)
    merge_metadata.merge_file_metadata(paths)
    print
