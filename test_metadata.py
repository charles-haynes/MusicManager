#!/usr/bin/env python
# -*- coding: utf-8 -*-

import metadata
from mock import  Mock,MagicMock,patch
import mutagen
import mutagen.flac
import mutagen.mp3
import mutagen.mp4
import mutagen.musepack
import unittest

hash_empty = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
hash_1234 = '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4'
id3v2_header = 'ID3'+'\x00'*(10-3)
id3v1_trailer = 'TAG'+'\x00'*(128-3)
id3v1v2 = id3v2_header+id3v1_trailer

def mockOpen(read_values):
    retval = MagicMock()
    retval.return_value.__enter__.return_value.read.side_effect = read_values
    return retval

@patch('mutagen.File', MagicMock())
class TestMetadataDigest(unittest.TestCase):
    @patch('io.open', mockOpen(['','','']))
    def test_digest_not_mp3(self):
        f = metadata.Metadata(
            'test_file',
            sum([len(x) for x in ['','','']]))
        digest = f.digest
        self.assertEqual(digest,hash_empty)

    @patch('io.open', mockOpen(['',id3v1_trailer[:3],'']))
    def test_digest_id3v1(self):
        f = metadata.Metadata(
            'test_file',
            sum([len(x) for x in ['',id3v1_trailer[:3],'']]))
        digest = f.digest
        self.assertEqual(digest,hash_empty)

    @patch('io.open', mockOpen([id3v2_header, '','']))
    def test_digest_id3v2(self):
        f = metadata.Metadata(
            'test_file',
            sum([len(x) for x in [id3v2_header, '','']]))
        digest = f.digest
        self.assertEqual(digest,hash_empty)

    @patch('io.open', mockOpen([id3v2_header, id3v1_trailer[:3], '']))
    def test_digest_id3v1v2(self):
        f = metadata.Metadata(
            'test_file',
            sum([len(x) for x in [id3v2_header, id3v1_trailer[:3], '']]))
        digest = f.digest
        self.assertEqual(digest,hash_empty)

@patch('mutagen.File')
@patch('io.open',MagicMock())
@patch('hashlib.sha256',Mock(return_value=Mock(hexdigest=Mock(return_value=hash_1234))))
class TestMetadataTags(unittest.TestCase):
    def test_non_mp3_file_to_mp3_tags(self, mock_mutagen):
        mock_mutagen.return_value=None
        f = metadata.Metadata('test_file',0)
        mp3_tags = f.tags
        self.assertEqual(mp3_tags,None)

    def test_mp3_file_to_mp3_tags(self, mock_mutagen):
        mock_mutagen.return_value = {'tag': 'value'}
        f = metadata.Metadata('test_file',0)
        mp3_tags = f.tags
        self.assertEqual(mp3_tags,{'tag': 'value'})
        self.assertTrue(mock_mutagen.called)


    def test_malformed_mp3_file_to_mp3_tags(self, mock_mutagen):
        mock_mutagen.side_effect=mutagen.mp3.HeaderNotFoundError('test error')
        f = metadata.Metadata('test_file',len(id3v1v2))
        mp3_tags = f.tags
        self.assertIsNone(mp3_tags)

    @patch('io.open', mockOpen(['', '', '1234']))
    def test_metadata_of_non_mp3_file(self, mock_mutagen):
        mock_mutagen.return_value = None
        f = metadata.Metadata('test_file', len(''+''+'1234'))
        info = f.metadata
        self.assertEqual(info,{'digest': hash_1234})

    @patch('io.open', mockOpen([id3v2_header, '', '1234']))
    def test_metadata_id3v2(self, mock_mutagen):
        mock_mutagen.return_value={'tag': 'value'}
        f = metadata.Metadata('test_file', len(id3v2_header+''+'1234'))
        info = f.metadata
        self.assertEqual(info,{'digest': hash_1234, 'tags': {'tag': 'value'}})

    @patch('io.open', mockOpen([id3v2_header, id3v1_trailer[:3], '1234']))
    def test_metadata_id3v1v2(self, mock_mutagen):
        mock_mutagen.return_value={'tag': 'value'}
        f = metadata.Metadata('test_file', len(id3v2_header+id3v1_trailer[:3]+'1234'))
        info = f.metadata
        self.assertEqual(info,{'digest': hash_1234, 'tags': {'tag': 'value'}})

class TestMetadataErrors(unittest.TestCase):
    def metadata_error(self, error):
        with patch('io.open', mockOpen([id3v2_header, id3v1_trailer[:3], '1234'])) as mock_open:
            with patch('mutagen.File', Mock(side_effect=error)):
               # with warnings.catch_warnings(record=True) as w:
               #     warnings.simplefilter("always")
                try:
                    f = metadata.Metadata('test_file', len(id3v2_header+id3v1_trailer[:3]+'1234'))
                    info = f.metadata
                except TypeError:
                    print mock_open.mock_calls
                # self.assertEqual(info, {'digest': hash_1234})
                # self.assertEqual(len(w),1)
                # self.assertTrue(issubclass(w[0].category, UserWarning))
                # self.assertEqual(str(w[0].message), "test_file test")

    def test_metadata_mp3_error(self):
        self.metadata_error(mutagen.mp3.HeaderNotFoundError('test'))

    def test_metadata_mp4_error(self):
        self.metadata_error(mutagen.mp4.MP4StreamInfoError('test'))

    def test_metadata_musepack_error(self):
        self.metadata_error(mutagen.musepack.MusepackHeaderError('test'))

    def test_metadata_flac_error(self):
        self.metadata_error(mutagen.flac.FLACNoHeaderError('test'))

@patch('io.open', MagicMock())
class TestCanonicalNames(unittest.TestCase):

    def setUp(self):
        self.attrs = {'TALB': 'album',
                      'TPE1': 'artist',
                      'TIT2': 'title'}
        self.mock_file = Mock(spec=mutagen.mp3.MP3,
                         __getitem__ = Mock(side_effect = lambda x: self.attrs[x]),
                         __contains__ = Mock(side_effect = lambda x: x in self.attrs))
        self.mock_file.name='name.ext'

        patcher = patch('mutagen.File', Mock(return_value=self.mock_file))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_canonical_name(self):
        f = metadata.Metadata('test_file.ext',0)
        self.assertEqual(f.canonical_name,'artist/album/title.ext')

    def test_canonical_compilation_name(self):
        self.attrs['TCMP'] = 'true'
        f = metadata.Metadata('test_file.ext',0)
        self.assertEqual(f.canonical_name,'Various Artists/album/artist - title.ext')

    def test_canonical_name_with_track(self):
        self.attrs['TRCK'] = '09/10'
        f = metadata.Metadata('test_file.ext',0)
        self.assertEqual(f.canonical_name,'artist/album/09 - title.ext')

    def test_canonical_compilation_name_with_track(self):
        self.attrs['TCMP'] = 'true'
        self.attrs['TRCK'] = '9'
        f = metadata.Metadata('test_file.ext',0)
        self.assertEqual(f.canonical_name,'Various Artists/album/09 - artist - title.ext')

    def test_canonical_name_with_bad_track(self):
        self.attrs['TRCK'] = 'zzzz'
        f = metadata.Metadata('test_file.ext',0)
        self.assertEqual(f.canonical_name,'artist/album/title.ext')

if __name__ == "__main__":
    unittest.main()
