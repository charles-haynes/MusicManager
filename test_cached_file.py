import cached_file
from datetime import datetime
from stat import *
import unittest

class TestCachedFile(unittest.TestCase):
    def setUp(self):
        self.file_info = {
            'name': 'test_file',
            'parent': 1,
            'mode': S_IFREG,
            'inode': 2,
            'size': 3,
            'mtime': datetime.fromtimestamp(4.0)}
        self.cached_file = cached_file.CachedFile(**self.file_info)
        self.cached_file_info = self.file_info.copy()
        self.cached_file_info['mp3'] = {'digest': '5', 'tags': {'tag': 'value'}}

    def test_hasChanged_no_changes(self):
        self.assertFalse(self.cached_file.hasChanged(self.cached_file_info))

    def test_hasChanged_mtime(self):
        self.cached_file_info['mtime'] = datetime.fromtimestamp(3.0)
        self.assertTrue(self.cached_file.hasChanged(self.cached_file_info))

    def test_hasChanged_size(self):
        self.cached_file_info['size'] += 1
        self.assertTrue(self.cached_file.hasChanged(self.cached_file_info))

    def test_hasChanged_inode(self):
        self.cached_file_info['inode'] += 1
        self.assertTrue(self.cached_file.hasChanged(self.cached_file_info))

    def test_hasChanged_mp3(self):
        self.assertTrue(self.cached_file.hasChanged(self.file_info))

    def test_isRegularFile_true_for_regular_file(self):
        self.assertTrue(self.cached_file.isRegularFile())

    def test_isRegularFile_false_for_dir(self):
        self.file_info['mode'] = S_IFDIR
        self.cached_file = cached_file.CachedFile(**self.file_info)
        self.assertFalse(self.cached_file.isRegularFile())

    def test_isDirectory_false_for_regular_file(self):
        self.assertFalse(self.cached_file.isDirectory())

    def test_isDirectory_true_for_dir(self):
        self.file_info['mode'] = S_IFDIR
        self.cached_file = cached_file.CachedFile(**self.file_info)
        self.assertTrue(self.cached_file.isDirectory())

    def test_dict(self):
        self.assertEqual(self.file_info, self.cached_file.dict())

