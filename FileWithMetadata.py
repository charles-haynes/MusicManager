#!/usr/bin/env python
# -*- coding: utf-8 -*-

from hashlib import sha256
import mutagen
from mutagen.id3 import BitPaddedInt
import os.path
import struct
from warnings import warn

TEXT_ENCODING = 'utf8'

class FileWithMetadata():

    def __init__(self, name, size):
        self.name = name
        self.size = size
        self._digest = None
        self._tags = None

    def digest(self):
        if self._digest: return self._digest

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

    def metadata(self):
        r = {'digest': self.digest()}
        if self.tags(): r['tags'] = self._tags
        return r

    def tags(self):
        if self._tags: return self._tags
        try:
            self._tags = mutagen.File(self.name)
            return self._tags
        except (
            mutagen.mp4.MP4StreamInfoError,
            mutagen.mp3.HeaderNotFoundError,
            mutagen.musepack.MusepackHeaderError
            ) as exc:
            warn("%s %s"%(self.name, exc))
        return None
