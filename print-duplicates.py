#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

  digests = db.mp3_dups.find({},sort=[('value',-1)])
  for digest in digests:
    print "*** %s: %d" % (digest['_id'], digest['value'])
    for dup in db.files.find({'digest': digest['_id']}):
      print full_path(db.files,dup).encode('utf-8')
    print
