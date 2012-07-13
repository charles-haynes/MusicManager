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

TEXT_ENCODING = 'utf8'

trans_dot_to_colon = maketrans(u".",u":")

def maybe_get_MP3_size(f, size):
    is_mp3=False
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
                is_mp3=True
                start = insize+10
        except struct.error: pass

        if end-128 >= start:
            f.seek(-128, 2)
            if f.read(3) == "TAG":
                is_mp3=True
                end -= 128

    except IOError: pass
    return (is_mp3, start, end-start)

def hash_mp3(f, start, size)
    f.seek(start)
    buf=f.read(size)
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

skipTillFileName=""

for dirpath, dirnames, filenames in os.walk(dir_name):
    for name in filenames:
        if (skipTillFileName and name != skipTillFileName)
            continue
        skipTillFileName=""

        fname = os.path.join(dirpath, name)
        print fname,
        sys.stdout.flush()
        try:
            f = open(fname)
            stat = os.fstat(f.fileno())
        except IOError as exc:
            print "** %s" % (exc,)
            continue

        f_data = filesCollection.find_one({"device": stat.st_dev, "inode": stat.st_ino})

        if (f_data == None):
            print "** Not found"
            continue
            
        row = mp3_collection.find_one({'file_id': f_data['_id']})
        if (row != None):
            print "** Already parsed"
            continue

        try:
            (is_mp3, start, size)=maybe_get_MP3_size(f, stat.st_size)
            if is_mp3:
                digest=hash_MP3(f, start, size)
                row = {'file_id': f_data['_id'], 'digest': digest}

                mp3_tags = file_to_MP3_tag_dict(fname)
                if (mp3_tags != None):
                    for k, v in mp3_tags.items():
                        k=unicode(str(k).translate(trans_dot_to_colon), '8859')
                        row[k] = str(v)


            mp3_collection.insert(row)
            print "%s" % (".",)
        except (mutagen.mp3.HeaderNotFoundError,
                bson.errors.InvalidStringData,
                bson.errors.InvalidDocument,
                UnicodeEncodeError) as exc:
            print "** %s: %s" % (exc, row)

print "Done!"
