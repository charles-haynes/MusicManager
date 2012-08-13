#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import pymongo 
from bson.code import Code

if __name__ == '__main__': 
  m = Code("""function() {
    if (this.tags)
        for (i=0;i<this.tags.length; i+=1)
            emit(this.tags[i][0],1);
    }""")

  r = Code("function(k, v) { return Array.sum(v) }")

  db = pymongo.Connection().test
  files = db.files

  files.map_reduce(m, r, "mp3_tags")
