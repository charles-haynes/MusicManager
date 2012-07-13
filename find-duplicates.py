#! /usr/bin/env python

# convert to python
# use unicode data
# compare metadata to filenames using normalized unicode
# NFC is "composed" normalization, NFD is "decomposed"
# some mac apps (filesystem?) prefer NFD
# unicodedata.normalize('NFC', str)


translate = function(s, t1, t2) {
    t={};
    for (i=0; i<t1.length; i++)
	t[t1.charAt(i)] = t2.charAt(i);
    return [(t[c]||c) for each (c in s.split(""))].join("");
};

getPath = function (n) {
    p = "";
    for( ; n.parent; n=db.files.findOne({_id: n.parent})) {
      p="/"+n.name+p;
    }
    return p;
};

def compare_normalized(s1, s2) {
    return unicode.compare(unicodedata.normalize('NFC', s1), unicodedata.normalize('NFC', s2))
}

m = function() { emit(this.digest, 1) };

r = function(k, v) { return Array.sum(v) };

db.mp3.mapReduce(m, r, {out: "mp3_dups"}, {sort: {digest: 1}});

forEachDupMp3 = function(dup_mp3) {
//   merge any tags
//   pick one to delete
//     delete it
//   save merged tags
    dup_file = db.files.findOne({_id: dup_mp3.file_id});
    print(getPath(dup_file));
};

forEachMp3 = function(mp3) {
    file = db.files.findOne({_id: mp3.file_id});

    // compare track name to file name
    if (mp3.TRCK && mp3.TIT2) {
	track_title = mp3.TRCK+" "+mp3.TIT2+".mp3";
	if (translate(track_title,":/?\"'", "_____") != file.name)
	    print(mp3.TRCK+" "+mp3.TIT2+", "+file.name);
    }

    // compare album name to parent file name
    parent = db.files.findOne({_id: file.parent});
    if (mp3.TALB && mp3.TALB != parent.name)
	print("TALB: "+mp3.TALB+", "+parent.name);

    // compare artist name to grandparent file name
    grandparent = db.files.findOne({_id: parent.parent});
    if (mp3.TPE2 && mp3.TPE2 != grandparent.name)
	print("TPE2: "+mp3.TPE2+", "+grandparent.name);
};

forEachDup = function(dup_digest) {
    db.mp3.find({digest: dup_digest._id}).forEach(forEachDupMp3);
    print();
};

// for each mp3 file
db.mp3.find({}).forEach(forEachMp3);

// for each duplicate file
// db.mp3_dups.find({value: {$gt: 1}}).forEach(forEachDup);

// for each mp3 file
// if doesn't have musicbrainz tags
//   look up in musicbrainz
//   tag with musicbrainz tags
