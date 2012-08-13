#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import mutagen
import shutil

def merge_file_metadata(file_name_a, file_name_b):
    """merge_file_metadata

    given two files with the same digest
    create a new file with the same digest and merged metadata
    """
    metadata_a = mutagen.File(file_name_a)
    metadata_b = mutagen.File(file_name_b)
    new_file_name=file_name_a+".new"
    shutil.copy(file_name_a, new_file_name)
    merged_metadata = merge_metadata(metadata_a, metadata_b)
    replace_metadata(new_file_name, merged_metadata)

def merge_metadata(metadata_a, metadata_b):
    """merge_metadata
    
    given two sets of metadata
    return the merger of the two
    """
    return dict(metadata_a.items() + metadata_b.items())

def replace_metadata(file_name, new_metadata):
    """replace_metadata
    
    given a file and a set of new metadata
    completely replace the file's metadata with the new metadata
    """
    metadata_dict = dict(metadata)
    old_metadata = mutagen.File(file_name)
    old_metadata = metadata_dict
    old_metadata.save()
