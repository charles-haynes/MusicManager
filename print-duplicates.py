#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cPickle as pickle
import merge_metadata
import os
import os.path
import pymongo 

def full_path(coll, id):
    if id is None:
        return os.sep
    row=coll.find_one({'_id':id},{'name':1,'parent':1})
    return os.path.join(full_path(coll, row['parent']),row['name'])

if __name__ == '__main__': 
    db = pymongo.Connection().test

    digests = db.mp3_dups.find({'value': {'$gt': 1}},sort=[('value',-1)])
    for digest in digests:
        dups = db.files.find({'digest': digest['_id']})
        print "*** %s: %d" % (digest['_id'], digest['value'])
        dup_dict = {}
        for dup in dups:
            try:
                dup_name = os.path.join(full_path(db.files, dup['parent']),dup['name']).encode('utf-8')
                dup_dict[dup_name] = pickle.loads(dup['tags'])
            except KeyError:
                continue 
        print '\n'.join(dup_dict.keys())
        if dup_dict:
            merge_metadata.merge_file_metadata(dup_dict, 'new_files')
        print
