#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bson
import mutagen
import os
import pymongo
import stat
import struct
import sys

from hashlib import sha256
from mutagen.id3 import BitPaddedInt
from string import maketrans

trans_dot_to_colon = maketrans(u".",u":")

def hash_MP3(f, size):
    start=0
    end=size

    try:
        # technically an insize=0 tag is invalid, but we skip it anyway
        f.seek(start)
        idata = f.read(10)
        try:
            id3, insize = struct.unpack('>3sxxx4s', idata)
            insize = BitPaddedInt(insize)
            if id3 == 'ID3' and insize >= 0 and insize+10 <= end:
                start = insize+10
        except struct.error: pass

        try:
            f.seek(-128, 2)
            if f.read(3) == "TAG" and end-128 >= start:
                end -= 128
        except IOError: pass

    except IOError: pass
    f.seek(start)
    buf=f.read(end-start)
    return sha256(buf).hexdigest()

def file_to_MP3_tag_dict(fname):
    mp3_tags=None
    try:
        mp3_tags=mutagen.File(fname)
    except mutagen.mp4.MP4StreamInfoError as exc:
        print "%s %s" % (dirpath, exc),

    return mp3_tags

if (len(sys.argv) > 1):
    dir_name = sys.argv[1]
else:
    raise SystemExit("Usage: %s <filename>" % (sys.argv[0]))

test_db = pymongo.Connection().test
mp3_collection = test_db.mp3
filesCollection = test_db.files

flag=False

for dirpath, dirnames, filenames in os.walk(dir_name):
    for name in filenames:
        if (flag and name != "13 'night on the Bare Mountain'.mp3"):
            continue
        flag=False

        print name,
        fname = os.path.join(dirpath, name)
        f = open(fname)
        stat = os.fstat(f.fileno())

        f_data = filesCollection.find_one({"device": stat.st_dev, "inode": stat.st_ino})

        if (f_data == None):
            print " %s Not found" % (dirpath,)
            continue
            
        row = mp3_collection.find_one({'file_id': f_data['_id']})
        if (row != None):
            print "%s Already parsed" % (dirpath,)
            continue

        try:
            digest=hash_MP3(f, stat.st_size)

            row = {'file_id': f_data['_id'], 'digest': digest}

            mp3_tags = file_to_MP3_tag_dict(fname)
            if (mp3_tags != None):
                for k, v in mp3_tags.items():
                    k=unicode(str(k).translate(trans_dot_to_colon), '8859')
                    row[k] = str(v)


            mp3_collection.insert(row)
        except bson.errors.InvalidStringData as exc:
            print "%s %s, row: %s" % (dirpath, exc, row)
        else:
            print

print "Done!"
