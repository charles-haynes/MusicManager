#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pdb

from datetime import datetime
import filecache
import FileWithMetadata
import os
import pickle
import pymongo
from stat import *
import unittest

from mock import call,Mock,patch


class TestFileCache(unittest.TestCase):

    def setUp(self):
        self.find_result = {
            'mtime': datetime.fromtimestamp(2.0),
            'inode': 5,
            'size': 4,
            '_id': 7,
            'mp3': {'tag': 'value'}}
        self.mongo_db = Mock()
        self.mongo_db.find_one.return_value = self.find_result

        self.file_cache = filecache.FileCache(self.mongo_db)

        patcher1 = patch('FileWithMetadata.FileWithMetadata.metadata', Mock(return_value = {'digest': 0, 'tags': {'tag': 'value'}}))
        self.mock_metadata = patcher1.start()
        self.addCleanup(patcher1.stop)

        patcher2 = patch('os.lstat', Mock(return_value=Mock(st_mode=S_IFREG, st_mtime=2.0, st_size=4, st_ino=5)))
        self.mock_lstat = patcher2.start()
        self.addCleanup(patcher2.stop)

    @patch('os.path.join', Mock(side_effect = (lambda x, y: x+'/'+y)))
    @patch('os.listdir', Mock(side_effect = [['a','b'],OSError,['c'],OSError]))
    def test_add_tree(self):
        self.file_cache.id = Mock(return_value=0)

        self.file_cache.add_tree('.', None)

        expected = [call('./a', 'a', None),
                    call('./b', 'b', None),
                    call('./b/c', 'c', 0)]

        self.assertEqual(self.file_cache.id.call_args_list,expected)

    def test_id_calls_metadata_for_uncached_regular_file(self):
        self.mongo_db.find_one.return_value = None
        self.file_cache.id("test_file_name", "test_file_name", 8)
        self.mongo_db.find_one.return_value = self.find_result

        self.assertTrue(self.mock_metadata.called)
        self.assertTrue(self.mongo_db.save.called)

    def test_id_does_not_call_on_changed_info_for_directories(self):
        self.mock_lstat.return_value.st_mode=S_IFDIR
        self.file_cache.id("test_file_name", "test_file_name", 8)

        self.assertFalse(self.mock_metadata.called)
        self.assertFalse(self.mongo_db.save.called)

    def test_id_no_changes(self):
        self.file_cache.id("test_file_name", "test_file_name", 8)

        self.assertFalse(self.mock_metadata.called)
        mock_calls = [call.find_one({'name': 'test_file_name', 'parent': 8})]
        self.assertEqual(self.mongo_db.mock_calls,mock_calls)
        self.assertFalse(self.mongo_db.save.called)

    def test_id_new(self):
        self.mongo_db.find_one.return_value = None
        self.file_cache.id("test_file_name", "test_file_name", 8)

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.mock_metadata.called)

    def test_id_mtime_changed(self):
        self.mock_lstat.return_value.st_mtime += 1.0
        self.file_cache.id("test_file_name", "test_file_name", 8)

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.mock_metadata.called)

    def test_id_size_changed(self):
        self.mock_lstat.return_value.st_size += 1
        self.file_cache.id("test_file_name", "test_file_name", 8)

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.mock_metadata.called)

    def test_id_ino_changed(self):
        self.mock_lstat.return_value.st_ino += 1
        self.file_cache.id("test_file_name", "test_file_name", 8)

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.mock_metadata.called)

    def test_id_no_change_but_no_mp3_info(self):
        del self.find_result['mp3']
        self.mongo_db.find_one.return_value = self.find_result
        self.file_cache.id("test_file_name", "test_file_name", 8)

        self.assertFalse(self.mongo_db.save.called)
        self.assertFalse(self.mock_metadata.called)

if __name__ == "__main__":
    unittest.main()
