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
This module is for testing purposes.
Run in python interactive mode and test out the classes written in this package.
"""

# ----- SYSTEM IMPORTS ----- #

import time

# ----- 3RD PARTY IMPORTS ----- #

from music21 import (
    note, chord, key, # MUSIC21 fundamentals
    meter, clef, layout, instrument, stream, # for exporting
)

# --MUSIC21 for exporting
from music21.stream import Part, Score, Voice

# ----- LOCAL IMPORTS ----- #

from fourpart.fpchords import FourPartChords

# ------------------------------ #

def getInstrument():
    instr = instrument.Piano()
    instr.instrumentName = ""
    return instr

def TEST_FPCHORDS_GETBEST(chordprogression, ts="4/4", engine=None):
    if not engine:
        engine = FourPartChords() # default configuration
    chprog = engine.parseProgression(chordprogression)
    sols = []

    phrase_no = 0 ####
    ttt = time.time()
    engine.log(f"##### CONFIDENCE VALUE = {engine.config['dp_confidence']}")
    for phrase, _ in chprog: # ignore rhythms
        tt = time.time()
        phrase_no += 1 ####
        engine.log(f"PHRASE {phrase_no} ====================")

        engine.log("Phrase: ", phrase)
        DP, V = engine.DP_MemoizePhrasePrune(phrase)
        engine.log(f"DP: Done! Retracing solution...")
        op = DP[-1].index(min(DP[-1])) # op (optimal): always points to the optimal choice at phrase[i].
        engine.log(f"Total Cost: {DP[-1][op][0]}")
        sol = []
        for i in reversed(range(len(phrase))):
            sol.append(chord.Chord(V[i][op], lyric=phrase[i][0].figure))
            op = DP[i][op][1] # set op to op's backreference (to the last optimal element)
        sol.reverse()

        sols.append(sol)
        engine.log(f"PHRASE {phrase_no} TOTAL TIME: {time.time() - tt} seconds")

    engine.log(f"++++++++++ TOTAL TIME ++++++++++ {time.time() - ttt} seconds ++++++++++")

    engine.log(f"generating score...")
    voices = [stream.Voice([getInstrument()]) for _ in range(4)]
    current_key = None

    SA = stream.Part([clef.TrebleClef(), voices[0], voices[1]]) # Q: do we need to setup time signature here?
    TB = stream.Part([clef.BassClef(), voices[2], voices[3]])

    for (phrase, rhythm), chords in zip(chprog, sols):
        for i, (chordinfo, duration, voicing) in enumerate(zip(phrase, rhythm, chords)):
            rm = chordinfo[0]

            bass, tenor, alto, soprano = [
                note.Note(p, quarterLength=duration) for p in voicing.pitches
            ]
            if i == 0:
                if rm.key != current_key:
                    bass.addLyric(rm.key.tonicPitchNameWithCase.replace('#','♯').replace('-','♭')+': '+rm.figure)
                if not current_key or rm.key not in {current_key, current_key.relative}:
                    ks = key.KeySignature(rm.key.sharps)
                    SA.append(ks)
                    TB.append(ks)
            else:
                bass.addLyric(rm.figure)

            bass.stemDirection = alto.stemDirection = "down"
            tenor.stemDirection = soprano.stemDirection = "up"
            voices[0].append(soprano)
            voices[1].append(alto)
            voices[2].append(tenor)
            voices[3].append(bass)

    # https://web.mit.edu/music21/doc/moduleReference/moduleLayout.html?highlight=staff#music21.layout.Staff
    score = stream.Score([SA, TB], meter.TimeSignature(ts))
    score.insert(0, layout.StaffGroup([SA, TB], symbol='brace', barTogether='Mensurstrich'))

    score.show()
    return chords


def analysis(chorale):
    cp = generateChorale(chorale)
    p = parseProgression(chorale)[0][0]

    for i in range(len(p)-1):
        #engine.log(f"=========CHORD {i+1} & {i+2}=========")
        x._voiceLeadingCostDebug(cp[i], p[i], cp[i+1], p[i+1])

    return "DONE"


ch = """D: I vi I6 IV I64 V I!2
D: I6 V64 I IV6 V I6 V!2
D: I IV6 I6 IV I64 V7 vi!2
D: I6 V43 I I6 ii65 V I!2
A: I IV64 I vi ii6 V7 I!2
b: iv6 i64 iv iio6 i64 V7 i!2
A: IV IV V I6 ii V65 I!2
D: IV6 I V65 I ii65 V7 I!2"""
chsh = "D: I IV V V7 I!4\nE: I IV V V7 I!4"
chbach = """Bb: I vi V/vi vi V6/V V/V V I IV7/V V/V V!2
Bb: I V7!2 V7/vi vi IV6 V7 I IV V I!2
Bb: I IV6 IV ii V!2 V6 V7/IV!3 IV!2 vi V6/V V/V V6/V V!2
Bb: V42 I6 I I6 IV!2 viio6 I6 IV ii6!1/2 ii!1/2 I6!2 I ii6 ii V7 I!2"""


helpstr = """\
FourPart Unit Tests

TEST_FPCHORDS_GETBEST( chordprogression, ts="4/4", engine=None )
    chordprogression: a standard notation object (see FourPartChords
                      specification)
    ts: the accompanying time signature for chordprogression
        defaults to "4/4"
    engine: a preconfigured FourPartChords engine could be provided.
            If not, a new one will be created.

* ---------------------------------------- *
"""

if __name__ == "__main__":
    print(helpstr)
