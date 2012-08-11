#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import pickle
import populate_db_files
from stat import *
import unittest

from mock import call,Mock,patch

class TestPopulateDbFiles(unittest.TestCase):

    def setUp(self):
        self.find_result = {
            'mtime': datetime.fromtimestamp(2.0),
            'inode': 5,
            'size': 4,
            '_id': 7,
            'mp3': {'tag': 'value'}}
        self.mongo_db = Mock()
        self.mongo_db.find_one.return_value = self.find_result

        self.file_db = populate_db_files.FileCache(self.mongo_db)
        self.file_db.on_changed = Mock(return_value = {'digest': 0, 'tags': {'tag': 'value'}})
        self.stat = Mock(st_mode=S_IFREG, st_mtime=2.0, st_size=4, st_ino=5)

    @patch('os.lstat')
    @patch('os.path.join')
    @patch('os.listdir')
    def test_add_tree(self, mock_listdir,mock_path_join,mock_lstat):
        mock_listdir.side_effect = [['a','b'],['c']]
        mock_path_join.side_effect = (lambda x, y: x+'/'+y)
        mode = {'./a':self.stat,
                './b':Mock(st_mode=S_IFDIR, st_mtime=2.0, st_size=4, st_ino=5),
                './b/c':self.stat}
        mock_lstat.side_effect = (lambda x: mode[x])

        self.file_db.id = Mock(return_value=0)

        self.file_db.add_tree('.', None)

        expected = [call('./a', 'a', None, mode['./a']),
                    call('./b', 'b', None, mode['./b']),
                    call('./b/c', 'c', 0, mode['./b/c'])]

        self.assertEqual(self.file_db.id.call_args_list,expected)

    def test_id_calls_on_changed_for_regular_file(self):
        self.mongo_db.find_one.return_value = None
        self.stat.st_mode = S_IFREG
        self.file_db.id("test_file_name", "test_file_name", 8, self.stat)

        self.assertTrue(self.file_db.on_changed.called)
        self.assertTrue(self.mongo_db.save.called)

    def test_id_does_not_call_on_changed_for_directories(self):
        self.stat.st_mode = S_IFDIR
        self.file_db.id("test_file_name", "test_file_name", 8, self.stat)

        self.assertFalse(self.file_db.on_changed.called)
        self.assertFalse(self.mongo_db.save.called)

    def test_id_no_changes(self):
        self.file_db.id("test_file_name", "test_file_name", 8, self.stat)

        self.assertTrue(not self.file_db.on_changed.called)
        mock_calls = [call.find_one({'name': 'test_file_name', 'parent': 8})]
        self.assertEqual(self.mongo_db.mock_calls,mock_calls)
        self.assertFalse(self.mongo_db.save.called)

    def test_id_new(self):
        self.mongo_db.find_one.return_value = None
        self.file_db.id("test_file_name", "test_file_name", 8, self.stat)

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.file_db.on_changed.called)

    def test_id_mtime_changed(self):
        self.stat.st_mtime += 1.0
        self.file_db.id("test_file_name", "test_file_name", 8, self.stat)

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.file_db.on_changed.called)

    def test_id_size_changed(self):
        self.stat.st_size += 1
        self.file_db.id("test_file_name", "test_file_name", 8, self.stat)

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.file_db.on_changed.called)

    def test_id_ino_changed(self):
        self.stat.st_ino += 1
        self.file_db.id("test_file_name", "test_file_name", 8, self.stat)

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.file_db.on_changed.called)

    def test_id_no_mp3_info(self):
        del self.find_result['mp3']
        self.mongo_db.find_one.return_value = self.find_result
        self.file_db.id("test_file_name", "test_file_name", 8, self.stat)

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.file_db.on_changed.called)

if __name__ == "__main__":
    unittest.main()
