#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 #--------------#
# Author:  @npvq #
# Licence: GPLv3 #
 #--------------#

 #=======================#
# FourPartBaseObject File #
 #=======================#

# ----- SYSTEM IMPORTS ----- #

# Debugging/Logging
import time

# ----- 3RD PARTY IMPORTS ----- #

# from music21 import (
#   pitch, # MUSIC21 fundamentals
# )
import music21 as mus # unfortunately it is necessary (for consistency)

# ----- LOCAL IMPORTS ----- #

from fourpart import do_nothing
from fourpart.settings import default_config

# ------------------------------ #


class FourPartBaseObject(object):
    # Virtual Class (Don't Instantiate)

    def __init__(self, **kwargs):
        self.config = default_config
        self.config.update(kwargs)

        self._range_keys = [['bass_range_min',    'bass_range_max',    'bass_range_min_allowable',    'bass_range_max_allowable'   ],
                            ['tenor_range_min',   'tenor_range_max',   'tenor_range_min_allowable',   'tenor_range_max_allowable'  ],
                            ['alto_range_min',    'alto_range_max',    'alto_range_min_allowable',    'alto_range_max_allowable'   ],
                            ['soprano_range_min', 'soprano_range_max', 'soprano_range_min_allowable', 'soprano_range_max_allowable']]
        
        self.ranges = [[self.config[k] for k in voice] for voice in self._range_keys]

        self.DP_MemoizePhrase = self.DP_MemoizePhrasePrune if self.config['dp_pruning'] else self.DP_MemoizePhraseNoPruning

        self.chordCost = self._get_chordCostFunction() # this will break the program if you run __init__.

        # Debug/Logging. Non config-related.
        self.logging = True
        self.logStream = lambda s: print("DBG:",s) # or do_nothing

    def configure(self, **kwargs):
        """\
        Updates configurations and ensures that those updates take effect.
        Should be overridden by subclasses should more internal states be implemented."""

        self.config.update(kwargs)

        chord_cost_change = False

        if any("_range_" in key for key in kwargs.keys()):
            self.ranges = [[self.config[k] for k in voice] for voice in self._range_keys]
            chord_cost_change = True

        if chord_cost_change or any(key.startswith("ch_") for key in kwargs.keys()):
            self.chordCost = self._get_chordCostFunction() # this will break the program if you run __init__.

        if "dp_pruning" in kwargs.keys():
            self.DP_MemoizePhrase = self.DP_MemoizePhrasePrune if self.config['dp_pruning'] else self.DP_MemoizePhraseNoPruning

    def log(self, *args):
        self.logStream(" ".join([i.__str__() for i in args]))

    @staticmethod
    def _generatePitches(query, lb=mus.pitch.Pitch('A0'), ub=mus.pitch.Pitch('C8')): # lower & upper bounds
        """Query all notes in range of a certain pitch-class. Those outside the common range will be assigned a cost."""
        
        # We start checking from the same octave as the lower bound
        query.octave = lb.octave
        
        while (query.midi <= ub.midi):
            if (query.midi >= lb.midi):
                yield query
            query.octave += 1

    def _get_chordCostFunction(self):
        return NotImplementedError

    def _get_voiceLeadingCostFunction(self, rm1, rm2):
        return NotImplementedError

    def voiceChord(self, *args):
        """\
        Abstractable (reusable) construct: for each element of "phrase," let it be a tuple
        whose first element contains the roman numeral (with "Key" information).
        """
        return NotImplementedError

    def voiceLeadingCost(self, chord1, rm1, chord2, rm2):
        """Simplifying construct for voiceLeadingCost"""
        return self._get_voiceLeadingCostFunction(rm1, rm2)(chord1, chord2)

    def DP_MemoizePhraseNoPruning(self, phrase):
        """\

        Abstractable (reusable) construct: for each element of "phrase," let it be a tuple
        whose first element contains the roman numeral (with "Key" information).
        """

        # NOTE: chordCost and voiceLeadingCost do not take in "extra information" in these tuples. They only judge based on roman numeral and chord voicing (for now).

        # O(L^2 N), L = max number of voicings per chord (~120), N = number of chords in phrase.
        L = len(phrase)
        V = [list(self.voiceChord(*chordinfo)) for chordinfo in phrase]
        DP = [[None for _ in range(len(V[i]))] for i in range(L)]

        # first layer i=0, only chord cost, and no back reference.
        self.log(f"DP: Setting up first chord...")
        for j in range(len(V[0])):
            DP[0][j] = (self.chordCost(V[0][j], phrase[0][0]), None)
        # Mask updating (pruning)
        # pruning first chord options greatly decrease bottleneck during second chord
        bar = _confidence * ( min(DP[0])[0] + self.config['dp_first_buffer']//(len(V[0])*len(V[1])) )
        for j in range(len(V[0])):
            if DP[0][j][0] > bar:
                Mask[0][j] = False

        # subsequent layers i=1..L-1
        for i in range(1, L):
            if self.logging:
                self.log(f"DP: running {i+1}(th) chord (of {L} total)... ({len(V[i-1])}x{len(V[i])}={len(V[i-1])*len(V[i])} pairs to run)")
                start_time = time.time()

            voiceLeadingCost = self._get_voiceLeadingCostFunction(phrase[i-1][0], phrase[i][0])
            for j in range(len(V[i])):
                # Note: chord cost of current voicing added at the end.
                best = (1e9, None) # (totalCost, backReference)
                for k in range(len(V[i-1])):
                    current_cost = DP[i-1][k][0] + voiceLeadingCost(V[i-1][k], V[i][j]) # previous_cost + progression cost
                    if current_cost < best[0]:
                        best = (current_cost, k)

                if i+1 == L:
                    DP[i][j] = (best[0] + self.chordCost(V[i][j], phrase[i][0], last_chord=True), best[1])
                else:
                    DP[i][j] = (best[0] + self.chordCost(V[i][j], phrase[i][0]), best[1])
            
            if self.logging:
                total_time = time.time() - start_time
                self.log(f"DP:         took {total_time} seconds total ({total_time/(len(V[i-1])*len(V[i]))}) seconds per pair)")

        return DP, V # Return DP memoized tables, and the list of list of voicings.

    def DP_MemoizePhrasePrune(self, phrase):
        """\
        DP Algorithm where Pruning is enabled.
        Abstractable (reusable) construct: for each element of "phrase," let it be a tuple
        whose first element contains the roman numeral (with "Key" information).
        """

        # NOTE: chordCost and voiceLeadingCost do not take in "extra information" in these tuples. They only judge based on roman numeral and chord voicing (for now).

        # O(L^2 N), L = max number of voicings per chord (~120), N = number of chords in phrase.
        L = len(phrase)
        V = [list(self.voiceChord(*chordinfo)) for chordinfo in phrase]
        DP = [[None for _ in range(len(V[i]))] for i in range(L)]
        Mask = [[True for _ in range(len(V[i]))] for i in range(L)] # DP MASK

        # localizing class variables: optimization
        _confidence = self.config['dp_confidence']
        _buffer = self.config['dp_buffer']
        
        # first layer i=0, only chord cost, and no back reference.
        self.log(f"DP: Setting up first chord...")
        for j in range(len(V[0])):
            DP[0][j] = (self.chordCost(V[0][j], phrase[0][0]), None)
        # Mask updating (pruning)
        if self.config['dp_prune_first']:
            # pruning first chord options greatly decrease bottleneck during second chord
            bar = _confidence * ( min(DP[0])[0] + self.config['dp_first_buffer']//(len(V[0])*(len(V[1]) if len(V)>1 else 1)) )
            for j in range(len(V[0])):
                if DP[0][j][0] > bar:
                    Mask[0][j] = False

        # subsequent layers i=1..L-1
        for i in range(1, L):
            if self.logging:
                dbg_temp_count = sum(Mask[i-1]) #### DEBUG
                self.log(f"DP: running {i+1}(th) chord (of {L} total)... (({dbg_temp_count} of {len(V[i-1])})x{len(V[i])}={dbg_temp_count*len(V[i])} pairs to run)")
                start_time = time.time()

            voiceLeadingCost = self._get_voiceLeadingCostFunction(phrase[i-1][0], phrase[i][0])
            for j in range(len(V[i])):
                # Note: chord cost of current voicing added at the end.
                best = (1e9, None) # (totalCost, backReference)
                for k in range(len(V[i-1])):
                    if not Mask[i-1][k]:
                        continue
                    current_cost = DP[i-1][k][0] + voiceLeadingCost(V[i-1][k], V[i][j]) # previous_cost + progression cost
                    if current_cost < best[0]:
                        best = (current_cost, k)

                if i+1 == L:
                    DP[i][j] = (best[0] + self.chordCost(V[i][j], phrase[i][0], last_chord=True), best[1])
                else:
                    DP[i][j] = (best[0] + self.chordCost(V[i][j], phrase[i][0]), best[1])

            # Mask updating (pruning)
            bar = _confidence * (min(DP[i])[0] + _buffer) 
            for j in range(len(V[i])):
                if DP[i][j][0] > bar:
                    Mask[i][j] = False
            
            if self.logging:
                total_time = time.time() - start_time
                self.log(f"DP:         took {total_time} seconds total ({total_time/(dbg_temp_count*len(V[i]))}) seconds per pair)")

        return DP, V # Return DP memoized tables, and the list of list of voicings.
