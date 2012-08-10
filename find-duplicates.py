#!/usr/bin/env python
# -*- coding: utf-8 -*-

# make file walker use unicode

import grp
import os
import pwd
import pymongo
import re
import sys
import unicodedata

from bson.code import Code
from datetime import datetime
from stat import *

trans_tbl = {
    0x2019: ord(u"_"),
    ord(u"*"): ord(u"_"),
    ord(u"."): ord(u"_"),
    ord(u":"): ord(u"_"),
    ord(u"/"): ord(u"_"),
    ord(u"?"): ord(u"_"),
    ord(u"\\"): ord(u"_"),
    ord(u'"'): ord(u"_"),
    ord(u"'"): ord(u"_")
    }

TRCK = u'TRCK'
TIT2 = u'TIT2'
TALB = u'TALB'
TPE2 = u'TPE2'
NAME = u'name'
_ID = u'_id'
PARENT = u'parent'
FILE_ID = u'file_id'

def getPath(n):
    p="/"+n[NAME]
    while n[PARENT]:
        n=db.files.find_one({_ID: n[PARENT]})
        p="/"+n[NAME]+p
    return p

def normalize(s):
    return unicodedata.normalize('NFC', s).translate(trans_tbl)

def forEachDupMp3(dup_mp3):
#   merge any tags
#   pick one to delete
#     delete it
#   save merged tags
    dup_file = db.files.find_one({_ID: dup_mp3[FILE_ID]})
    print(getPath(dup_file))

def forEachMp3(mp3):
    file = db.files.find_one({_ID: mp3[FILE_ID]})
    file_name = file[NAME]
    m = re.match(r"(?P<track_number>\d+)\s*(-\s*)?(?P<track_name>.+?)(\.mp3)?$", file_name)
    try:
        file_track_number = m.group('track_number')
        file_track_name = m.group('track_name')
    except AttributeError:
        file_track_number = "0"
        file_track_name = file_name

    # compare track name to file name
    try:
        if (TRCK in mp3):
            track = re.match(ur"(\d+)/?(\d+)?",mp3[TRCK]).group(1)
            if (int(track) != int(file_track_number)):
                print(u"TRCK: %s, file track number: %s" % (mp3[TRCK], file_track_number))
    except (ValueError, AttributeError):
        print("Can't parse track number for %s. TRCK %s, file_track_number %s"
              % (file_name, mp3[TRCK], file_track_number))

    # compare track name to file name
    if (TIT2 in mp3 and normalize(mp3[TIT2]) != normalize(file_track_name)):
        try:
            print(u"TIT2: %s, file track name: %s" % (mp3[TIT2], file_track_name))
        except UnicodeEncodeError:
            print("UnicodeEncodeError: %s, %s" %
                  (mp3[TIT2].encode('unicode-escape'), file_track_name.encode(u'unicode-escape')))

    # compare album name to parent file name
    parent = db.files.find_one({_ID: file[PARENT]})
    if (TALB in mp3 and normalize(mp3[TALB]) != normalize(parent[NAME])):
	print(u"TALB: %s, parent: %s" % (mp3[TALB],parent[NAME]))

    # compare artist name to grandparent file name
    grandparent = db.files.find_one({_ID: parent[PARENT]})
    if (TPE2 in mp3 and normalize(mp3[TPE2]) != normalize(grandparent[NAME])):
	print("TPE2: %s, grandparent: %s" % (mp3[TPE2], grandparent[NAME]))

def forEachDup(dup_digest):
    for f in db.mp3.find({"digest": dup_digest[_ID]}):
        forEachDupMp3(f)
    print

if __name__ == '__main__': 
  m = Code("""function() {
    if (this.mp3 && this.mp3.tags)
        for (i=0;i<this.mp3.tags.length; i+=1)
            emit(this.mp3.tags[i][0],1);
    }""")

  r = Code("function(k, v) { return Array.sum(v) }")

  db = pymongo.Connection().test
  files = db.files

  files.map_reduce(m, r, "mp3_tags")

  m = Code("""function() {
    if (this.mp3 && this.mp3.digest)
        emit(this.mp3.digest,1);
    }""")

  r = Code("function(k, v) { return Array.sum(v) }")

  # files.map_reduce(m, r, "mp3_dups", sort={"digest": 1})
  files.map_reduce(m, r, "mp3_dups")

  # for each mp3 file
  # if doesn't have musicbrainz tags
  #   look up in musicbrainz
  #   tag with musicbrainz tags

  # for each duplicate
  # if it is an mp3 file
  #   if it has tags
  #     merge tags
  #   delete dup
