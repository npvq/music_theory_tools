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

from itertools import permutations
from copy import deepcopy
from fractions import Fraction
# from enum import IntEnum

# DEBUG
# import time
# import os

# ----- 3RD PARTY IMPORTS ----- #

from music21.note import Note
from music21.pitch import Pitch, Accidental
from music21.chord import Chord
from music21.roman import RomanNumeral
from music21.key import Key, KeySignature
from music21.interval import Interval, Specifier

# from music21.meter import TimeSignature
from music21.clef import BassClef, TrebleClef
from music21.instrument import Piano
from music21.stream import Part, Score, Voice

# ----- LOCAL IMPORTS ----- #

from fourpart.settings import default_config

# ------------------------------ #

# utility function
do_nothing = lambda *args, **kwargs : None

# alternative to pitchClass, returns 0..6 for C..B (for comparison purposes)
scale_value = lambda n : {'C':0,'D':1,'E':2,'F':3,'G':4,'A':5,'B':6}[n[0]]

# helper to fetch resolution target notes (ignore return value) [also note strict inequality >/<]
aboveOctave = lambda t_p, p: p.octave if scale_value(t_p.name) > scale_value(p.name) else p.octave+1 # (target pitch and reference pitch)
belowOctave = lambda t_p, p: p.octave if scale_value(t_p.name) < scale_value(p.name) else p.octave-1

# temp: there should be a better solution, but this one will do for now.
dominantScaleDegrees = {'major': ['5', '7'], 'minor': ['5', '#7']}
tonicScaleDegrees = {'major': ['1', '6'], 'minor': ['1', '6']}
