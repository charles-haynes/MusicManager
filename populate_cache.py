#!/usr/bin/env python
# -*- coding: utf-8 -*-

import filecache
import logging
import os
import os.path
import pymongo
import sys

TEXT_ENCODING = 'utf8'

if __name__ == '__main__':
    logging.captureWarnings(True)
    file_cache = filecache.FileCache(pymongo.Connection().test.files, 1)

    fpath = sys.argv[1] if (len(sys.argv) > 1) else os.getcwd()
    fpath=os.path.abspath(fpath)
    _id = file_cache.id(fpath, fpath, None)
    file_cache.add_tree(fpath, _id)
