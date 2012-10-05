#!/usr/bin/env python
# -*- coding: utf-8 -*-

import metadata
import mutagen
import os
import shutil

class MergeConflict(Exception):
    pass

class WriteVerificationFailed(Exception):
    pass

def merge_file_metadata(dup_dict, base_dir=''):
    """merge_file_metadata

    given a dictionary of file_names and file metadata
    of files that all have the same content
    create a new file with that content and merged metadata
    or raise an exception if there is a merge conflict
    """
    metadatas = dup_dict.values()
    old_file_name = dup_dict.keys()[0]
    try:
        merged_metadata_dict = merge(metadatas)
        if merged_metadata_dict is None:
            return None
    except MergeConflict as exc:
        print exc
        return None
    try:
        old_file = metadata.Metadata(old_file_name)
        new_file_name=os.path.join(base_dir, old_file.canonical_name)
    except file_with_metadata.NoCanonicalName:
        return
    try:
        os.makedirs(os.path.dirname(new_file_name))
    except OSError:
        pass
    shutil.copy(old_file_name, new_file_name)
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
        raise WriteVerificationFailed(
            sorted(old_metadata.items()),
            sorted(new_metadata_dict.items()))
