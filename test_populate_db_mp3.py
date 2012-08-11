#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import mutagen
import os
import populate_db_mp3
import struct
import unittest
from mock import call,Mock,MagicMock,patch
import warnings

hash_empty = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
hash_1234 = '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4'
id3v2_header = 'ID3'+'\x00'*(10-3)
id3v1_trailer = 'TAG'+'\x00'*(128-3)
id3v1v2 = id3v2_header+id3v1_trailer

class TestPopulateDbMp3(unittest.TestCase):

    def setUp(self):
        self.f=Mock()
        self.f.read.return_value=''
        self.f_size=0

    def test_hash_mp3_not_MP3(self):
        self.f.read.side_effect=['','','']
        sha256hex = populate_db_mp3.hash_mp3(self.f, self.f_size)
        self.assertEqual(sha256hex,hash_empty)

    def test_hash_mp3_id3v1(self):
        self.f.read.side_effect=['',id3v1_trailer[:3],'']
        sha256hex = populate_db_mp3.hash_mp3(self.f, self.f_size)
        self.assertEqual(sha256hex,hash_empty)

    def test_hash_mp3_id3v2(self):
        self.f.read.side_effect=[id3v2_header, '','']
        sha256hex = populate_db_mp3.hash_mp3(self.f, self.f_size)
        self.assertEqual(sha256hex,hash_empty)

    def test_hash_mp3_id3v1v2(self):
        self.f.read.side_effect=[id3v2_header, id3v1_trailer[:3], '']
        sha256hex = populate_db_mp3.hash_mp3(self.f, self.f_size)
        self.assertEqual(sha256hex,hash_empty)

    @patch('mutagen.File')
    def test_non_mp3_file_to_mp3_tags(self,mock_mutagen):
        mock_mutagen.return_value=None
        mp3_tags = populate_db_mp3.file_to_MP3_tags('file_name')
        self.assertEqual(mp3_tags,None)

    @patch('mutagen.File')
    def test_mp3_file_to_MP3_tags(self,mock_mutagen):
        mock_mutagen.return_value = {'tag': 'value'}
        mp3_tags = populate_db_mp3.file_to_MP3_tags('')
        self.assertEqual(mp3_tags,{'tag': 'value'})
        self.assertTrue(mock_mutagen.called)

    @patch('os.stat')
    @patch('__builtin__.open')
    def test_malformed_mp3_file_to_mp3_tags(self,mock_open,mock_stat):
        self.f.read.return_value=id3v1v2
        self.f_size=len(id3v1v2)
        mock_open.return_value=self.f
        mock_stat.return_value.st_size = self.f_size
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mp3_tags = populate_db_mp3.file_to_MP3_tags('file_name')
        self.assertEqual(mp3_tags , None)
        self.assertEqual(len(w),1)
        self.assertTrue(issubclass(w[0].category, UserWarning))
        self.assertEqual(str(w[0].message), "file_name can't sync to an MPEG frame")

    @patch('mutagen.File')
    @patch('__builtin__.open')
    def test_get_mp3_info_not_MP3(self,mock_open,mock_mutagen):
        self.f.read.side_effect=['', '', '1234']
        magic_f=MagicMock(__enter__=Mock(return_value=self.f))
        mock_open.return_value=magic_f
        mock_mutagen.return_value=None
        info = populate_db_mp3.get_mp3_info('', self.f_size)
        self.assertEqual(info,{'digest': hash_1234})

    @patch('mutagen.File')
    @patch('__builtin__.open')
    def test_get_mp3_info_id3v2(self,mock_open,mock_mutagen):
        self.f.read.side_effect=[id3v2_header, '', '1234']
        magic_f=MagicMock(__enter__=Mock(return_value=self.f))
        mock_open.return_value=magic_f
        mock_mutagen.return_value={'tag': 'value'}
        info = populate_db_mp3.get_mp3_info('', self.f_size)
        self.assertEqual(info,{'digest': hash_1234, 'tags': {'tag': 'value'}})

    @patch('mutagen.File')
    @patch('__builtin__.open')
    def test_get_mp3_info_id3v1v2(self,mock_open,mock_mutagen):
        self.f.read.side_effect=[id3v2_header, id3v1_trailer[:3], '1234']
        magic_f=MagicMock(__enter__=Mock(return_value=self.f))
        mock_open.return_value=magic_f
        mock_mutagen.return_value={'tag': 'value'}
        info = populate_db_mp3.get_mp3_info('', self.f_size)
        self.assertEqual(info,{'digest': hash_1234, 'tags': {'tag': 'value'}})

if __name__ == "__main__":
    unittest.main()
