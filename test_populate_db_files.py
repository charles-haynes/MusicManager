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
        self.stat = Mock(
            st_mode=S_IFREG,
            st_atime=1.0,
            st_mtime=2.0,
            st_ctime=3.0,
            st_size=4,
            st_ino=5,
            st_dev=6,
            st_uid=100,
            st_gid=101,
            st_nlink=1)

    @patch('os.lstat')
    @patch('os.path.join')
    @patch('os.listdir')
    def test_add_tree(self, mock_listdir,mock_path_join,mock_lstat):
        mock_listdir.side_effect = [['a','b'],['c']]
        mock_path_join.side_effect = (lambda x, y: x+'/'+y)
        mode = {'./a':Mock(st_mode=S_IFREG),
                './b':Mock(st_mode=S_IFDIR),
                './b/c':Mock(st_mode=S_IFREG)}
        mock_lstat.side_effect = (lambda x: mode[x])

        self.file_db.visit_file = Mock(return_value=0)

        self.file_db.add_tree('.', None)

        expected = [call('a',mode['./a'],None,'./a'),
                    call('b',mode['./b'],None,'./b'),
                    call('c',mode['./b/c'],0,'./b/c')]

        self.assertEqual(self.file_db.visit_file.call_args_list,expected)

    def test_visit_file_calls_on_changed_for_regular_file(self):
        self.mongo_db.find_one.return_value = None
        self.stat.st_mode = S_IFREG
        self.file_db.visit_file("test_file_name", self.stat, 8, "test_file_name")

        self.assertTrue(self.file_db.on_changed.called)
        self.assertTrue(self.mongo_db.save.called)

    def test_visit_file_does_not_call_on_changed_for_directories(self):
        self.stat.st_mode = S_IFDIR
        self.file_db.visit_file("test_file_name", self.stat, 8, "test_file_name")

        self.assertFalse(self.file_db.on_changed.called)
        self.assertFalse(self.mongo_db.save.called)

    def test_visit_file_no_changes(self):
        self.file_db.visit_file("test_file_name", self.stat, 8, "test_file_name")

        self.assertTrue(not self.file_db.on_changed.called)
        mock_calls = [call.find_one({'name': 'test_file_name', 'parent': 8})]
        self.assertEqual(self.mongo_db.mock_calls,mock_calls)
        self.assertFalse(self.mongo_db.save.called)

    def test_visit_file_new(self):
        self.mongo_db.find_one.return_value = None
        self.file_db.visit_file("test_file_name", self.stat, 8, "test_file_name")

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.file_db.on_changed.called)

    def test_visit_file_mtime_changed(self):
        self.stat.st_mtime += 1.0
        self.file_db.visit_file("test_file_name", self.stat, 8, "test_file_name")

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.file_db.on_changed.called)

    def test_visit_file_size_changed(self):
        self.stat.st_size += 1
        self.file_db.visit_file("test_file_name", self.stat, 8, "test_file_name")

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.file_db.on_changed.called)

    def test_visit_file_ino_changed(self):
        self.stat.st_ino += 1
        self.file_db.visit_file("test_file_name", self.stat, 8, "test_file_name")

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.file_db.on_changed.called)

    def test_visit_file_no_mp3_info(self):
        del self.find_result['mp3']
        self.mongo_db.find_one.return_value = self.find_result
        self.file_db.visit_file("test_file_name", self.stat, 8, "test_file_name")

        self.assertTrue(self.mongo_db.save.called)
        self.assertTrue(self.file_db.on_changed.called)

if __name__ == "__main__":
    unittest.main()
