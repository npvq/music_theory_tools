#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 #--------------#
# Author:  @npvq #
# Licence: GPLv3 #
 #--------------#

 #==================#
# Module Description #
 #==================#
"""\
__init__ program for FourPart package containing algorithms using music21.
"""

# ----- SYSTEM IMPORTS ----- #

# from copy import deepcopy
# from enum import IntEnum

# DEBUG
# import time
# import os

# ----- 3RD PARTY IMPORTS ----- #

# --MUSIC21
# from music21 import (
#   note, pitch, chord, roman, key, interval, # MUSIC21 fundamentals
#   meter, clef, instrument, stream # for exporting
# )
# from music21.note import Note
# from music21.pitch import Pitch, Accidental
# from music21.chord import Chord
# from music21.roman import RomanNumeral
# from music21.key import Key, KeySignature
# from music21.interval import Interval, Specifier

# --MUSIC21 for exporting
# from music21.meter import TimeSignature
# from music21.clef import BassClef, TrebleClef
# from music21.instrument import Piano
# from music21.stream import Part, Score, Voice

# ----- LOCAL IMPORTS ----- #

from fourpart.settings import default_config

# ------------------------------ #

# utility function
do_nothing = lambda *args, **kwargs : None

# alternative to pitchClass, returns 0..6 for C..B (for comparison purposes)
scale_value = lambda n : {'C':0,'D':1,'E':2,'F':3,'G':4,'A':5,'B':6}[n[0]]

# helper to fetch resolution target notes (ignore return value) [also note strict inequality >/<]
octaveAbove = lambda t_p, p: p.octave if scale_value(t_p.name) > scale_value(p.name) else p.octave+1 # (target pitch and reference pitch)
octaveBelow = lambda t_p, p: p.octave if scale_value(t_p.name) < scale_value(p.name) else p.octave-1
# fetches appropriate octave value one voice down. (prevents overlapping and spacing errors). NOTE: same note twice means go an octave down, hence the strict inequality (<)
nextOctaveDown = lambda new_name, last_pitch: last_pitch.octave if scale_value(new_name) < scale_value(last_pitch.name) else last_pitch.octave-1

# abandoned solution: see below
dominantScaleDegrees = {'major': ['5', '7'], 'minor': ['5', '#7']}
tonicScaleDegrees = {'major': ['1', '6'], 'minor': ['1', '6']}

# Function: a simplified view of harmonic function, by listing roman numerals of chords that have to serve certain function.
#TODO: a better version should be implemented in the future
figureOut = lambda rm : (rm, rm+'6', rm+'64')
figureOutSeventh = lambda rm : (rm+'7', rm+'65', rm+'43', rm+'42')

tonicChords = {
    'major': [],
    'minor': [],
}
tonicChords['major'].extend(figureOut('I'))
tonicChords['major'].extend(figureOut('vi'))
tonicChords['major'].extend(figureOutSeventh('vi'))
tonicChords['major'].extend(figureOut('i')) # i : minor-mode borrowing (mixture)
tonicChords['minor'].extend(figureOut('i'))
tonicChords['minor'].extend(figureOut('VI'))
tonicChords['minor'].extend(figureOutSeventh('VI'))
tonicChords['minor'].extend(figureOut('I')) # I : picardy third (major-mode borrowing/mixture)

dominantChords = {
    'major': [],
    'minor': [],
}

dominantChords['major'].extend(figureOut('V'))
dominantChords['major'].extend(figureOutSeventh('V'))
dominantChords['major'].extend(figureOut('viio'))
dominantChords['major'].extend(figureOutSeventh('viiø'))
dominantChords['minor'].extend(figureOut('V'))
dominantChords['minor'].extend(figureOutSeventh('V'))
dominantChords['minor'].extend(figureOut('viio'))
dominantChords['minor'].extend(figureOutSeventh('viio'))
