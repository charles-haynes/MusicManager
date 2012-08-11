#!/usr/bin/env python
# -*- coding: utf-8 -*-

from hashlib import sha256
import mutagen
from mutagen.id3 import BitPaddedInt
import struct
import urllib
from warnings import warn

TEXT_ENCODING = 'utf8'

def hash_mp3(f, size):
    start=0
    end=size

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
    return sha256(buf).hexdigest()

def file_to_MP3_tags(file_name):
    try:
        return mutagen.File(file_name)
    except (
        mutagen.mp4.MP4StreamInfoError,
        mutagen.mp3.HeaderNotFoundError,
        mutagen.musepack.MusepackHeaderError
        ) as exc:
        warn("%s %s"%(file_name, exc))

    return None

def get_mp3_info(file_name, f_size):
    info=None
    with open(file_name, 'rb') as f:
        digest=hash_mp3(f, f_size)
        info = {'digest': digest}
        tags = file_to_MP3_tags(file_name)
        if tags:
            info['tags'] = tags
    return info
