# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the pythm for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" TODO: Module description """

"""
Helper functions for pythm
"""

import os,re
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC

# Audio file artist tag name.
TAG_NAME_ARTIST = "artist"
# Audion file album tag name.
TAG_NAME_TITLE = "title"
# File extension for mp3 files.
FILE_EXT_MP3 = ".mp3"
# File extension for ogg files.
FILE_EXT_OGG = ".ogg"
# File extension for flac files.
FILE_EXT_FLAC = ".flac"

# List of regexes for get_tags_from_file
_filematchers = []
_filematchers.append(".*-(?P<artist>.*)-(?P<title>.*)\..*")
_filematchers.append("(?P<artist>.*)-(?P<title>.*)\..*")
_filematchers.append("(?P<title>.*)\..*")

"""
" Determines if the given value is numeric or not.
" param val Value to test.
"""
def is_numeric(val):
    try:
        val + 1
        return True
    except Exception,e:
        return False

"""
" Formats a time value given in seconds to a string of the format
" MM:SS.
" param value Number to format.
"""
def format_time(value):
    if value < 0:
        return ""
    min = int(value / 60)
    sec = int(value) % 60
    if sec < 10:
        sec = "0" + str(sec)
    return str(min) + ":" + str(sec)

"""
" returns (artist,title) from regex filename match
" param file File name to parse.
"""
def get_tags_from_file(file):
    for r in _filematchers:
        m = re.match(r,os.path.basename(file))
        if(m):
            try:
                art = m.group("artist").strip()
            except:
                art = "unknown"
            try:
                tit = m.group("title").strip()
            except:
                tit = "unknown"
            return (art,tit)
    return ("",file)

"""
" Reads audio file tag data using mutagen.
" param entry Playlist entry. Will be filled with yummy data.
" param logger Reference to logger. None if no logger.
"""
def read_audio_tags(entry, logger):
    try:
        fn    = entry.id
        ext   = os.path.splitext(fn)[1].lower()
        audio = None

        if   (ext == FILE_EXT_MP3):  audio = MP3(fn, ID3=EasyID3)
        elif (ext == FILE_EXT_OGG):  audio = OggVorbis(fn)
        elif (ext == FILE_EXT_FLAC): audio = FLAC(fn)

        if (audio != None):
            entry.artist = audio[TAG_NAME_ARTIST][0]
            entry.title  = audio[TAG_NAME_TITLE][0]
            entry.length = audio.info.length

    except Exception, e:
        if (logger != None):
                logger.warn("Failed to read audio tag data: %s" % e)

