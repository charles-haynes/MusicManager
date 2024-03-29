#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo 
from bson.code import Code

if __name__ == '__main__': 
  db = pymongo.Connection().test

  m = Code("""function() {
    if (this.digest)
        emit(this.digest,1);
    }""")

  r = Code("function(k, v) { return Array.sum(v) }")

  db.files.map_reduce(m, r, "mp3_dups", sort={"digest": 1})
