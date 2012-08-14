#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pdb

from hashlib import sha256
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

class FileWithMetadata(object):

    def __init__(self, name, size=None):
        self.name = name
        self.size = size if size is not None else os.path.getsize(name)
        self._digest = None
        self._tags = None

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
        if self._digest:
            return self._digest

        with open(self.name, 'rb') as f:
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
            self._digest = sha256(buf).hexdigest()
            return self._digest

    @property
    def metadata(self):
        ret_val = {'digest': self.digest}
        if self.tags is not None:
            ret_val['tags'] = self.tags
        return ret_val

    @property
    def tags(self):
        if self._tags is not None:
            return self._tags
        try:
            self._tags = mutagen.File(self.name)
            return self._tags
        except (
            mutagen.mp4.error,
            mutagen.mp3.error,
            mutagen.musepack.error,
            mutagen.flac.error
            ) as exc:
            warn("%s %s"%(self.name, exc))
        return None
