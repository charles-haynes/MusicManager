#!/usr/bin/env python
# -*- coding: utf-8 -*-

import merge_metadata
from mock import call, MagicMock, Mock, patch
import unittest

@patch('os.path.join', Mock(side_effect = lambda x, y: x+'/'+y))
@patch('os.path.dirname',Mock())
@patch('os.makedirs', Mock())
@patch('shutil.copy', Mock())
@patch('merge_metadata.replace_metadata')
class TestMergeMetadata_merge_file_metadata(unittest.TestCase):
    def setUp(self):
        self.dict_base = {'a': 'b', 'c': 'd'}
        self.dict_no_conflict = {'a': 'b', 'e': 'f'}
        self.dict_conflict = {'a': 'b', 'c': 'e'}
        self.dict_merged = {'a': 'b', 'c': 'd', 'e': 'f'}

        patcher=patch('metadata.Metadata')
        self.mock_file_with_metadata = patcher.start()
        self.mock_file_with_metadata.return_value.canonical_name.__radd__.return_value = 'artist/album/title.ext'
        self.addCleanup(patcher.stop)

    def test_merge_file_metadata(self, mock_replace):
        merge_metadata.merge_file_metadata(
            {'1': self.dict_base, '2': self.dict_no_conflict})
        self.assertEqual(
            mock_replace.call_args,
            call('artist/album/title.ext', {'a': 'b', 'c': 'd', 'e': 'f'}))

    def test_merge_file_metadata_with_base_dir(self, mock_replace):
        merge_metadata.merge_file_metadata(
            {'1': self.dict_base, '2': self.dict_no_conflict}, base_dir='z')
        self.assertEqual(
            mock_replace.call_args,
            call('artist/album/title.ext', {'a': 'b', 'c': 'd', 'e': 'f'}))

    def test_merge_file_metadata_with_conflict(self, mock_replace):
        merge_metadata.merge_file_metadata(
            {'1': self.dict_base, '2': self.dict_conflict}, base_dir=None)
        self.assertFalse(mock_replace.called)

class TestMergeMetadata(unittest.TestCase):
    def setUp(self):
        self.dict_base = {'a': 'b', 'c': 'd'}
        self.dict_no_conflict = {'a': 'b', 'e': 'f'}
        self.dict_conflict = {'a': 'b', 'c': 'e'}
        self.dict_merged = {'a': 'b', 'c': 'd', 'e': 'f'}

    def test_merge(self):
        result = merge_metadata.merge([self.dict_base, self.dict_no_conflict])
        self.assertEqual(self.dict_merged,result)

    def test_merge_conflict(self):
        self.assertRaises(merge_metadata.MergeConflict,
                          merge_metadata.merge,
                          ([self.dict_base, self.dict_conflict]))

    @patch('mutagen.File')
    def test_replace_metadata(self, mock_mutagen):
        mutagen1 = MagicMock()
        mutagen2 = Mock()
        mutagen2.items.return_value = [('a', 'b'), ('c', 'd'), ('e', 'f')]
        mock_mutagen.side_effect = [mutagen1, mutagen2]
        merge_metadata.replace_metadata('test_file', self.dict_merged)
        self.assertTrue(mutagen1.save.called)
