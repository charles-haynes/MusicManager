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

  digests = db.mp3_dups.find({'value': {'$gt': 1}},sort=[('value',-1)])
  for digest in digests:
    dups = db.files.find({'digest': digest['_id'], 'tags': {'$exists': True}})
    # if dups.count() == 0:
    #   continue
    print "*** %s: %d" % (digest['_id'], digest['value'])
    for dup in dups:
      print full_path(db.files,dup).encode('utf-8')
    print
