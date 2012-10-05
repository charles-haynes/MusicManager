#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pdb

import hashlib
import io
import mutagen
import mutagen.flac
import mutagen.mp3
import mutagen.mp4
import mutagen.musepack
from mutagen.id3 import BitPaddedInt
import os.path
import re
import string
import struct
from warnings import warn

TEXT_ENCODING = 'utf8'

class NoCanonicalName(Exception):
    pass

class Metadata(object):
    """Encapsulate size, digest, and tag metadata for a file.
    
    Size is the length of the file. Digest is the sha256 of the
    "interesting" data in the file. Tags are the mutagen metadata tags
    """

    def __init__(self, name, size=None):
        self.name = name
        self.size = size if size is not None else os.path.getsize(name)
        self._digest = self._digest_from_file()
        self._tags = self._tags_from_file()

    @classmethod
    def FromFile(name):
        """Create metadata from a named file.

        returns a metadata object including digest, and music tags if any
        """
        retval = Metadata(name)
        retval.digest
        retval.tags
        return retval

    @property
    def canonical_name(self):
        if not isinstance(self.tags, mutagen.mp3.MP3):
            raise NoCanonicalName(self.name)

        fields = {'album': self.tags['TALB'],
                  'artist': self.tags['TPE1'],
                  'title': self.tags['TIT2'],
                  'ext': os.path.splitext(self.name)[1]}

        grandparent_dir_format = "{artist!s}"
        dir_format = "{album!s}"
        file_format = "{title!s}{ext!s}"

        if 'TCMP' in self.tags and self.tags['TCMP']:
            grandparent_dir_format = "Various Artists"
            file_format = "{artist!s} - " + file_format
        try:
            fields['track'] = int(re.match('\d+',str(self.tags['TRCK'])).group())
            file_format = "{track:02d} - " + file_format
        except (KeyError, AttributeError):
            pass

        return os.path.join(grandparent_dir_format.format(**fields),
                            dir_format.format(**fields),
                            file_format.format(**fields))

    @property
    def digest(self):
        if self._digest is None:
            self._digest = self._digest_from_file()
        
        return self._digest

    def _digest_from_file(self):
        with io.open(self.name, 'rb') as f:
            start=0
            end=self.size

            try:
                # technically an insize=0 tag is invalid, but we skip it anyway
                f.seek(start)
                idata = f.read(10)
                try:
                    id3, insize = struct.unpack('>3sxxx4s', idata)
                    insize = BitPaddedInt(insize)
                    if id3 == 'ID3' and insize >= 0 and insize+10 <= end:
                        start = insize+10
                except struct.error:
                    pass

                f.seek(-128, 2)
                idata=f.read(3)
                if idata == "TAG":
                    end -= 128

            except IOError:
                pass

            f.seek(start)
            buf=f.read(end-start)
            return hashlib.sha256(buf).hexdigest()

    @property
    def metadata(self):
        ret_val = {'digest': self.digest}
        if self.tags is not None:
            ret_val['tags'] = self.tags
        return ret_val

    @property
    def tags(self):
        if self._tags is None:
            self._tags = self._tags_from_file()
            
        return self._tags

    def _tags_from_file(self):
        try:
            return mutagen.File(self.name)
        except (
            mutagen.mp4.error,
            mutagen.mp3.error,
            mutagen.musepack.error,
            mutagen.flac.error
            ) as exc:
            warn("{} {}".format(self.name, exc))
        return None
