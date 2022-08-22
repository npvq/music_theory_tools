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



# ----- 3RD PARTY IMPORTS ----- #

from music21.chord import Chord

# ----- LOCAL IMPORTS ----- #

from fourpart.fpchords import FourPartChords

# ------------------------------ #


def TEST_FPCHORDS_GETBEST(chordprogression, ts="4/4", engine=None):
    if not engine:
        engine = FourPartChords() # default configuration
    phrases = engine.parseProgression(chorale)
    chords = []
    rhythm = []

    i = 0 ####
    ttt = time.time()
    self.log(f"##### CONFIDENCE VALUE = {engine.config['dp_confidence']}")
    for phrase in phrases:
        tt = time.time()
        i += 1 ####
        self.log(f"PHRASE {i} ====================")

        self.log("Phrase: ", phrase)
        DP, V = engine.DP_MemoizePhrasePrune(phrase)
        self.log(f"DP: Done! Retracing solution...")
        op = DP[-1].index(min(DP[-1])) # op (optimal): always points to the optimal choice at phrase[i].
        self.log(f"Total Cost: {DP[-1][op][0]}")
        sol = []
        for i in reversed(range(len(phrase))):
            sol.append(Chord(V[i][op], lyric=phrase[i][0].figure))
            op = DP[i][op][1] # set op to op's backreference (to the last optimal element)
        sol.reverse()

        chord_progression.extend(sol)
        self.log(f"PHRASE TOTAL TIME: {time.time() - tt} seconds")

    self.log(f"++++++++++ TOTAL TIME ++++++++++ {time.time() - ttt} seconds ++++++++++")

    score = generateScore(chord_progression, rhythm=rhythm_def, ts=ts)
    score.show()
    return chord_progression



def analysis(chorale):
    cp = generateChorale(chorale)
    p = parseProgression(chorale)[0][0]

    for i in range(len(p)-1):
        self.log(f"=========CHORD {i+1} & {i+2}=========")
        x._voiceLeadingCostDebug(cp[i], p[i], cp[i+1], p[i+1])

    return "DONE"



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
