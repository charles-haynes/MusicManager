#!/usr/bin/env python

import os
import sys
import tempfile

translate = {}
deleted = []
rootdir = '/Volumes/Samsung 1TB (2)'
tempdir = tempfile.mkdtemp(dir=rootdir)
for ch in range(0,255):
  filename = 3*chr(ch)

  try:
    d=os.open(filename, os.O_CREAT)
  except (TypeError, OSError):
    deleted.append(ch)
    continue

  filenames = os.listdir(tempdir)
  for fn in filenames:
      if fn != filename:
          translate[filename] = fn
      os.remove(fn)

  os.close(d)
  os.remove(filename)

os.rmdir(tempdir)
print "Deleted: "+str(deleted)
print "Translate: "+str(translate)
