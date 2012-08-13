#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pdb

import io
import mutagen
import os
import os.path
import re
import shutil

class MergeConflict(Exception):
    pass

def generate_name(metadata,file_type):
    if file_type != mutagen.mp3.MP3:
        return None
    
    if 'TCMP' in metadata and metadata['TCMP']:
        return generate_compilation_name(metadata)

    album = str(metadata['TALB'])
    artist = str(metadata['TPE1'])
    try:
        track = int(re.match('\d+',str(metadata['TRCK'])).group())
    except KeyError:
        return generate_non_track_name(metadata,file_type)
    title = str(metadata['TIT2'])
    return os.path.join(artist, album, ("%02d - %s.mp3" % (track, title)))

def generate_non_track_name(metadata,file_type):
    if file_type != mutagen.mp3.MP3:
        return None
    
    if 'TCMP' in metadata and metadata['TCMP']:
        return generate_compilation_name(metadata)

    album = str(metadata['TALB'])
    artist = str(metadata['TPE1'])
    title = str(metadata['TIT2'])
    return os.path.join(artist, album, ("%s.mp3" % (title,)))

def generate_compilation_name(metadata):
    album = str(metadata['TALB'])
    artist = str(metadata['TPE1'])
    try:
        track = int(re.match('\d+',str(metadata['TRCK'])).group())
    except KeyError:
        return generate_non_track_name(metadata,file_type)
    title = str(metadata['TIT2'])
    return os.path.join('Various Artists', album, ("%02d - %s - %s.mp3" % (track, artist, title)))

def merge_file_metadata(file_names):
    """merge_file_metadata

    given a list of files with the same digest
    create a new file with the same digest and merged metadata
    or raise an exception if there is a merge conflict
    """
    metadatas = [mutagen.File(file_name) for file_name in file_names]
    try:
        merged_metadata_dict = merge(metadatas)
        if merged_metadata_dict is None:
            return None
    except MergeConflict as exc:
        print exc
        return None
    new_file_name=generate_name(merged_metadata_dict,type(metadatas[0]))
    try:
        os.makedirs(os.path.dirname(new_file_name))
    except OSError:
        pass
    shutil.copy(file_names[0], new_file_name)
    print "copying to ",new_file_name,
    replace_metadata(new_file_name, merged_metadata_dict)
    print " done."

def merge(metadatas):
    """merge
    
    given a list of metadatas
    return a dictionary of the union of all of them
    raise an exception if there is a conflict
    """
    all_items = []
    for metadata in metadatas:
        try:
            all_items += metadata.items()
        except AttributeError:
            continue
    if all_items == []:
        return None
    all_items.sort()
    cur_item = all_items[0]
    for item in all_items:
        if cur_item == item:
            continue
        if cur_item[0] == item[0]:
            raise MergeConflict(cur_item, item)
        cur_item = item
    return dict(all_items)

def replace_metadata(file_name, new_metadata_dict):
    """replace_metadata
    
    given a file and a set of new metadata
    completely replace the file's metadata with the new metadata
    """
    old_metadata = mutagen.File(file_name)
    old_metadata.delete()
    for k,v in new_metadata_dict.iteritems():
        old_metadata[k] = v
    old_metadata.save()
    old_metadata = mutagen.File(file_name)
    if sorted(old_metadata.items()) != sorted(new_metadata_dict.items()):
        raise Exception(sorted(old_metadata.items()), sorted(new_metadata_dict.items()))
