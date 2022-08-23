#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 #--------------#
# Author:  @npvq #
# Licence: GPLv3 #
 #--------------#

 #===================#
# FourPartChords File #
 #===================#

# ----- SYSTEM IMPORTS -----

from fractions import Fraction
from itertools import permutations
from copy import deepcopy

# Debugging/Logging
import time

# ----- 3RD PARTY IMPORTS -----

# from music21 import (
#   pitch, chord, roman, key, interval, # MUSIC21 fundamentals
# )
import music21 as mus # unfortunately it is necessary

# ----- LOCAL IMPORTS -----

from fourpart import do_nothing, octaveAbove, octaveBelow, nextOctaveDown, dominantScaleDegrees, tonicScaleDegrees
from fourpart.base import FourPartBaseObject

# ------------------------------ #


class FourPartChords(FourPartBaseObject):
    """\
    FourPart problem solving utilities where the given is chords (Key + RomanNumerals)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _get_chordCostFunction(self):
        """\
        Overrides FourPartBassObject._get_chordCostFunction().

        Factory function to provide a fast and static chordCost function stored as a class method.
        Runs once during object initialization. Uses closure to store config as local variables.
        """

        # stores needed configurations as local variables for speed optimization
        _midi_ranges = [[p.midi for p in v] for v in self.ranges]
        _config = {k:v for k,v in self.config.items() if k.startswith('ch_')} # 'ch_': chord cost configs

        # output function is static (class configured and class independent)
        def _chordCost(chord, rm, last_chord=False):
            """This method computes the cost of chord voicing infractions and is run once on every chord.
               Its purpose is to encourage some voicings over others."""
            # Note to reader: this function should only discriminate between the different voicings of a particular chord (the chord has already been decided and locked-in).
            cost = 0
            _set_size = len(set(chord.pitchClasses))

            # encourage full chord voicings, prefer root doubling.

            if rm.containsSeventh(): # SEVENTH CHORD
                if _set_size < 4:
                    if chord.pitchClasses.count(rm.root().pitchClass) == 2:
                        cost += _config['ch_seventh_inc_doubled_root']
                    else:
                        cost += _config['ch_seventh_inc_doubled_third']
            else: # TRIAD
                if rm.inversion() != 2 and chord.pitchClasses.count(rm.root().pitchClass) < 2:
                        cost += _config['ch_triad_did_not_double_root']
                if _set_size < 3:
                    # incomplete chord should only be last chord (it is guaranteed by voiceChord that they are also RP chords)
                    if chord.pitchClasses.count(rm.root().pitchClass) == 3:
                        cost += _config['ch_triad_inc_tripled_root_last'] if last_chord else _config['ch_triad_inc_tripled_root']
                    else:
                        cost += _config['ch_triad_inc_doubled_third_last'] if last_chord else _config['ch_triad_inc_doubled_third']
            
            # check for voice-range vilations or deductions.
            for i in range(4):
                if _midi_ranges[i][0] <= chord[i].pitch.midi <= _midi_ranges[i][1]:
                    continue
                elif _midi_ranges[i][2] <= chord[i].pitch.midi <= _midi_ranges[i][3]:
                    cost += _config['ch_voice_outside_common_range']
                else:
                    cost += _config['ch_voice_outside_range'] # not permissible (high penalty by default)

            # slightly prefer authentic cadences (soprano doubles root)
            if last_chord and rm.figure in {'i', 'I'} and chord[3].pitch.name != rm.root().name:
                if (chord[3].pitch.name == rm.third.name):
                    cost += _config['ch_last_not_authentic_third']
                else:
                    cost += _config['ch_last_not_authentic_fifth']
            return cost

        return _chordCost

    def _get_voiceLeadingCostFunction(self, rm1, rm2):
        """\
        Factory function for voiceLeadingCost pre-loaded with roman numerals.
        Executed once for every chord pair in DP. Uses closure to load config as local variables.
        """
        
        # Stategy: precomputes chord data, returns one function with no recursive calls.
        # Alternatively we could return different functions based on chord information, but that seems unnecessary and possibly counterintuitive right now.

        # OVERHEAD (Non-voicing-dependent information on chords, used later)
        _rm1_key = rm1.secondaryRomanNumeralKey if rm1.secondaryRomanNumeral else rm1.key
        _rm2_key = rm2.secondaryRomanNumeralKey if rm2.secondaryRomanNumeral else rm2.key
        # Functional
        # NOTE: outdated. Should be replaced with new chord-based function model soon.
        func1 = (lambda n: n[1].modifier+str(n[0]) if n[1] else str(n[0]))(rm1.scaleDegreeWithAlteration)
        func2 = (lambda n: n[1].modifier+str(n[0]) if n[1] else str(n[0]))(rm2.scaleDegreeWithAlteration)
        _rm1_is_dominant = func1 in dominantScaleDegrees[_rm1_key.mode]
        _rm2_is_dominant = func2 in dominantScaleDegrees[_rm2_key.mode]
        _rm2_is_tonic = func2 in tonicScaleDegrees[_rm2_key.mode]
        # rm1 might resolve to rm2 as a secondary dominant rather than a cadence.
        _resolves = _rm1_is_dominant and (_rm1_key.tonic.name == _rm2_key.getDominant().name if rm1.secondaryRomanNumeral else _rm2_is_tonic)
        # Scale/pitch related
        _rm1_scale = _rm1_key.getPitches()
        _LT = _rm1_key.getLeadingTone().name # ti->do leading tone (WARNING: _rm1_scale[6] returns natural 7th degree in minor mode.)
        _FT = _rm1_scale[3].name # fa->mi tendency tone
        # Resolution tones (local variable shortcut optimizations)
        _DO = _rm1_scale[0]
        _SOL = _rm1_scale[4]
        _MI = _rm1_scale[2]
        # make local function reference (save reference): optimization... is it really necessary?
        _above = octaveAbove
        _below = octaveBelow

        # preload configs ('vl_': voice leading configs)
        _config = {k:v for k,v in self.config.items() if k.startswith('vl_')}
        # NOTE: might be a little slower than manually preloading config variables as local variables, but this way is much more maintainable (and preserves sanity)

        def _voiceLeadingCost(chord1, chord2):
            """\
            This method computes the costs of voice leading infractions/violations
            and is run on every adjacent chord pair in a phrase.
            """
            
            cost = 0
            # helper/shorthands
            pchord1 = chord1.pitches
            pchord2 = chord2.pitches
            
            # (FUNCTION SPECIFIC)
            if _rm1_is_dominant:
                # ti->ti or ti->do (ti->sol)
                if _LT in chord1.pitchNames:
                    lt_idx = chord1.pitchNames.index(_LT) # leadingtone_index : there can only be one.
                    if ( pchord2[lt_idx] not in (pchord1[lt_idx], mus.pitch.Pitch(_DO, octave=_above(_DO, pchord1[lt_idx])))
                    and (lt_idx != 0 or chord2[0].name not in {_LT, _DO.name}) ): #ForgiveBass if it is *not* at all possible to resolve/sustain
                        
                        # FRUSTRATED LEADING TONE (inner voice)
                        if lt_idx in {1, 2} and mus.pitch.Pitch(_SOL, octave=_below(_SOL, chord1[lt_idx])):
                            cost += _config['vl_frustrated_lt_dominant']
                        else: 
                            cost += _config['vl_lt_violation_dominant'] * (_config['vl_lt_tt_violation_cadential_multiplier'] if _resolves else 1)
                # fa->mi
                if not _rm2_is_dominant: # alternate condition: if _resolves. Note: even in resolution, Dom/V -> i64 can have the "fa" held/sustained before resolving to "mi."
                    if _FT in chord1.pitchNames: # possibly more than one
                        for ft_idx, p in enumerate(chord1.pitchNames):
                            if ( p == _FT and pchord2[ft_idx] not in (chord1[ft_idx].pitch, mus.pitch.Pitch(_MI, octave=_below(_MI, pchord1[ft_idx]))) 
                            and (ft_idx != 0 or chord2[ft_idx].name == _MI.name) ): #ForgiveBass

                                cost += _config['vl_dominant_tt_not_resolved'] * (_config['vl_lt_tt_violation_cadential_multiplier'] if _resolves else 1)
            
            else: # rm1 not dominant
                # ti->ti or ti->do (ti->sol)
                if _LT in chord1.pitchNames:
                    lt_idx = chord1.pitchNames.index(_LT) # leadingtone_index : there can only be one.
                    if ( pchord2[lt_idx] not in (pchord1[lt_idx], mus.pitch.Pitch(_DO, octave=_above(_DO, pchord1[lt_idx])))
                    and (lt_idx != 0 or chord2[0].name not in {_LT, _DO.name}) ): #ForgiveBass if it is *not* at all possible to resolve/sustain
                        
                        # FRUSTRATED LEADING TONE (inner voice)
                        if lt_idx in {1, 2} and mus.pitch.Pitch(_SOL, octave=_below(_SOL, chord1[lt_idx])): 
                            cost += _config['vl_frustrated_lt']
                        else:
                            cost += _config['vl_lt_violation']

                # non-dominant 7 resolution
                if rm1.containsSeventh():
                    seventh = chord1.seventh
                    seven_idx = pchord1.index(seventh) # (seventh cannot be doubled, so is unique)
                    # Resolutions have to go down a m2 or M2.
                    if ( not (seventh == pchord2[seven_idx] or mus.interval.Interval(noteStart=chord2[seven_idx], noteEnd=chord1[seven_idx]).name in {'m2','M2'})
                    and (seven_idx != 0 or (seventh.pitchClass + 12 - pchord2[seven_idx].pitchClass)%12 > 2) ): #ForgiveBass
                        
                        cost += _config['vl_nd7_not_resolved']

            # non-dominant 7 preparation
            if not _rm2_is_dominant and rm2.containsSeventh():
                seventh = chord2.seventh
                seven_idx = pchord2.index(seventh)

                if ( pchord1[seven_idx] != seventh
                and (seven_idx != 0 or chord1[seven_idx].name == seventh.name) ): #ForgiveBass && does not allow enharmonic equivalent (respelling) preparation.
                    
                    cost += _config['vl_nd7_not_prepared']
            
            # (GENERIC)
            # VOICE CROSSING
            cost += _config['vl_voice_crossing'] * ((chord1[0]>chord2[1])+(chord1[1]<chord2[0]) + (chord1[1]>chord2[2])+(chord1[2]<chord2[1]) + (chord1[2]>chord2[3])+(chord1[3]<chord2[2]))
            
            # LEAPS: Avoid big leaps (generally). Octave leaps in bass is ok. Extra penalty for dissonant leaps, semitone-steps are not considered dissonant leaps (d2s not yet considered)
            diffs = [ (abs(i.generic.value), not(i.specifier in {mus.interval.Specifier.PERFECT, mus.interval.Specifier.MAJOR, mus.interval.Specifier.MINOR} or i.generic.value==1))
                      for i in (mus.interval.Interval(noteStart=chord1[j], noteEnd=chord2[j]) for j in range(4)) ]
            cost += ((0 if diffs[0][0] <= 5 or diffs[0][0] == 8               else                                                                              _config['vl_bass_leap_gt5']    if diffs[0][0] <  8 else _config['vl_bass_leap_gt8'])    + _config['vl_bass_leap_dissonant']    * diffs[0][1]  # Bass
                    + (0 if diffs[1][0]<= 2 else _config['vl_tenor_leap_3']   if diffs[1][0] == 3 else _config['vl_tenor_leap_4to5']   if diffs[1][0] <= 5 else _config['vl_tenor_leap_gt5']   if diffs[1][0] <= 8 else _config['vl_tenor_leap_gt8'])   + _config['vl_tenor_leap_dissonant']   * diffs[1][1]  # Tenor
                    + (0 if diffs[2][0]<= 2 else _config['vl_alto_leap_3']    if diffs[2][0] == 3 else _config['vl_alto_leap_4to5']    if diffs[2][0] <= 5 else _config['vl_alto_leap_gt5']    if diffs[2][0] <= 8 else _config['vl_alto_leap_gt8'])    + _config['vl_alto_leap_dissonant']    * diffs[2][1]  # Alto
                    + (0 if diffs[3][0]<= 2 else _config['vl_soprano_leap_3'] if diffs[3][0] == 3 else _config['vl_soprano_leap_4to5'] if diffs[3][0] <= 5 else _config['vl_soprano_leap_gt5'] if diffs[3][0] <= 8 else _config['vl_soprano_leap_gt8']) + _config['vl_soprano_leap_dissonant'] * diffs[3][1]) # Soprano
            
            # prefer bass leaping down octave over bass leaping up.
            if diffs[0][0]==8 and mus.interval.Interval(noteStart=chord1[0],noteEnd=chord2[0]).direction.value==1:
                cost += _config['vl_bass_leaps_octave_up']
            
            # SPECIAL CASE (REPEATED CHORD)
            if rm1==rm2 and diffs[3][0]==1 and diffs[2][0]==1 and diffs[1][0]==1:
                cost += _config['vl_repeated_chord_static']
            
            # PARALLELISMS
            for i in range(3): # the i=3 (range(4)) case is degenerate.
                i1, i2 = pchord1[i].midi, pchord2[i].midi
                if i1 == i2: continue # oblique motion
                for j in range(i+1, 4):
                    j1, j2 = pchord1[j].midi, pchord2[j].midi
                    
                    # Parallel or Contrary fifths or octaves check.
                    if (j1-i1)%12 == (j2-i2)%12 and (j1-i1)%12 in {0, 7}:
                        cost += _config['vl_parallelism_outer'] if (i==0 and j==3) else _config['vl_parallelism']
                    
                    # Unequal 5ths. Bass & another voice has a º5 -> P5. (double not oblique voices)
                    if i == 0 and j1 != j2 and (j1-i1)%12==6 and (j2-i2)%12==7:
                        cost += _config['vl_unequal_5_outer'] if j==3 else _config['vl_unequal_5']
            
            # DIRECT/HIDDEN: Outer voices move in similar motion into P5 or P8 and soprano has a leap.
            s1, s2, b1, b2 = pchord1[3].midi, pchord2[3].midi, pchord1[0].midi, pchord2[0].midi
            if abs(s2-s1) > 2 and (s2-b2)%12 in {0,7}:
                cost += _config['vl_direct_parallelism']
            
            # Static melody in soprano
            if s2 == s1:
                cost += _config['vl_melody_static']
            
            # OUTER VOICES SHOULD NOT SIMILAR MOTION (should be incontrary motion instead)
            if mus.interval.Interval(noteStart=chord1[3], noteEnd=chord2[3]).direction.value * mus.interval.Interval(noteStart=chord1[0], noteEnd=chord2[0]).direction.value == 1:
                cost += _config['vl_outer_voices_similar_motion']
            
            return cost

        return _voiceLeadingCost


    def _get_voiceLeadingCostFunction_Debug(self, rm1, rm2):
        """\
        Debug Version of Factory function for voiceLeadingCost pre-loaded with roman numerals.
        Executed once for every chord pair in DP. Uses closure to load config as local variables.
        """
        
        # Stategy: precomputes chord data, returns one function with no recursive calls.
        # Alternatively we could return different functions based on chord information, but that seems unnecessary and possibly counterintuitive right now.

        # OVERHEAD (Non-voicing-dependent information on chords, used later)
        _rm1_key = rm1.secondaryRomanNumeralKey if rm1.secondaryRomanNumeral else rm1.key
        _rm2_key = rm2.secondaryRomanNumeralKey if rm2.secondaryRomanNumeral else rm2.key
        # Functional
        # NOTE: outdated. Should be replaced with new chord-based function model soon.
        func1 = (lambda n: n[1].modifier+str(n[0]) if n[1] else str(n[0]))(rm1.scaleDegreeWithAlteration)
        func2 = (lambda n: n[1].modifier+str(n[0]) if n[1] else str(n[0]))(rm2.scaleDegreeWithAlteration)
        _rm1_is_dominant = func1 in dominantScaleDegrees[_rm1_key.mode]
        _rm2_is_dominant = func2 in dominantScaleDegrees[_rm2_key.mode]
        _rm2_is_tonic = func2 in tonicScaleDegrees[_rm2_key.mode]
        # rm1 might resolve to rm2 as a secondary dominant rather than a cadence.
        _resolves = _rm1_is_dominant and (_rm1_key.tonic.name == _rm2_key.getDominant().name if rm1.secondaryRomanNumeral else _rm2_is_tonic)
        # Scale/pitch related
        _rm1_scale = _rm1_key.getPitches()
        _LT = _rm1_key.getLeadingTone().name # ti->do leading tone (WARNING: _rm1_scale[6] returns natural 7th degree in minor mode.)
        _FT = _rm1_scale[3].name # fa->mi tendency tone
        # Resolution tones (local variable shortcut optimizations)
        _DO = _rm1_scale[0]
        _SOL = _rm1_scale[4]
        _MI = _rm1_scale[2]
        # make local function reference (save reference): optimization... is it really necessary?
        _above = octaveAbove
        _below = octaveBelow

        # preload configs ('vl_': voice leading configs)
        _config = {k:v for k,v in self.config.items() if k.startswith('vl_')}
        # NOTE: might be a little slower than manually preloading config variables as local variables, but this way is much more maintainable (and preserves sanity)

        # debug tools:
        class counter(object):
            def __init__(self, value):
                self.count = value

            def __str__(self):
                return str(self.count)

            def __repr__(self):
                return f"<{type(self).__module__}.{type(self).__qualname__} object at {hex(id(self))} with value {self.count}>"

            def __iadd__(self, other):
                self.count += other
                self.log(f"total_cost:{self.count} (added:{other})")
                return self

        _log = self.log

        def _voiceLeadingCost_Debug(chord1, chord2):
            """\
            This method computes the costs of voice leading infractions/violations
            and is run on every adjacent chord pair in a phrase.
            """
            cost = counter(0)
            
            # helper/shorthands
            pchord1 = chord1.pitches
            pchord2 = chord2.pitches
            
            # (FUNCTION SPECIFIC)
            if _rm1_is_dominant:
                # ti->ti or ti->do (ti->sol)
                if _LT in chord1.pitchNames:
                    lt_idx = chord1.pitchNames.index(_LT) # leadingtone_index : there can only be one.
                    if ( pchord2[lt_idx] not in (pchord1[lt_idx], mus.pitch.Pitch(_DO, octave=_above(_DO, pchord1[lt_idx])))
                    and (lt_idx != 0 or chord2[0].name not in {_LT, _DO.name}) ): #ForgiveBass if it is *not* at all possible to resolve/sustain
                        
                        # FRUSTRATED LEADING TONE (inner voice)
                        if lt_idx in {1, 2} and mus.pitch.Pitch(_SOL, octave=_below(_SOL, chord1[lt_idx])): 
                            _log(f"VL: frustrated LT (dominant) voice:{lt_idx} cost:{_config['vl_frustrated_lt_dominant']}")
                            cost += _config['vl_frustrated_lt_dominant']
                        else: 
                            _log(f"VL: LT violation (dominant) voice:{lt_idx} cost:{_config['vl_lt_violation_dominant']}, multiplier:{_config['vl_lt_tt_violation_cadential_multiplier'] if _resolves else 1}")
                            cost += _config['vl_lt_violation_dominant'] * (_config['vl_lt_tt_violation_cadential_multiplier'] if _resolves else 1)
                # fa->mi
                if not _rm2_is_dominant: # alternate condition: if _resolves. Note: even in resolution, Dom/V -> i64 can have the "fa" held/sustained before resolving to "mi."
                    if _FT in chord1.pitchNames: # possibly more than one
                        for ft_idx, p in enumerate(chord1.pitchNames):
                            if ( p == _FT and pchord2[ft_idx] not in (chord1[ft_idx].pitch, mus.pitch.Pitch(_MI, octave=_below(_MI, pchord1[ft_idx])))
                            and (ft_idx != 0 or chord2[ft_idx].name == _MI.name) ): #ForgiveBass
                                
                                _log(f"VL: fa->mi TT violation voice:{ft_idx} cost:{_config['vl_dominant_tt_not_resolved']}, multiplier:{_config['vl_lt_tt_violation_cadential_multiplier'] if _resolves else 1}")
                                cost += _config['vl_dominant_tt_not_resolved'] * (_config['vl_lt_tt_violation_cadential_multiplier'] if _resolves else 1)
            
            else: # rm1 not dominant
                # ti->ti or ti->do (ti->sol)
                if _LT in chord1.pitchNames:
                    lt_idx = chord1.pitchNames.index(_LT) # leadingtone_index : there can only be one.
                    if ( pchord2[lt_idx] not in (pchord1[lt_idx], mus.pitch.Pitch(_DO, octave=_above(_DO, pchord1[lt_idx])))
                    and (lt_idx != 0 or chord2[0].name not in {_LT, _DO.name}) ): #ForgiveBass if it is *not* at all possible to resolve/sustain
                        
                        # FRUSTRATED LEADING TONE (inner voice)
                        if lt_idx in {1, 2} and mus.pitch.Pitch(_SOL, octave=_below(_SOL, chord1[lt_idx])): 
                            _log(f"VL: frustrated LT (nondominant) voice:{lt_idx} cost:{_config['vl_frustrated_lt']}")
                            cost += _config['vl_frustrated_lt']
                        else:
                            _log(f"VL: LT violation (nondominant) voice:{lt_idx} cost:{_config['vl_lt_violation']}")
                            cost += _config['vl_lt_violation']

                # non-dominant 7 resolution
                if rm1.containsSeventh():
                    seventh = chord1.seventh
                    seven_idx = pchord1.index(seventh) # (seventh cannot be doubled, so is unique)
                    # Resolutions have to go down a m2 or M2.
                    if ( not (seventh == pchord2[seven_idx] or mus.interval.Interval(noteStart=chord2[seven_idx], noteEnd=chord1[seven_idx]).name in {'m2','M2'})
                    and (seven_idx != 0 or (seventh.pitchClass + 12 - pchord2[seven_idx].pitchClass)%12 > 2) ): #ForgiveBass
                        
                        _log(f"VL: Nondominant Seven not resolved (R of PSR) voice:{seven_idx} cost:{_config['vl_nd7_not_resolved']}")
                        cost += _config['vl_nd7_not_resolved']

            # non-dominant 7 preparation
            if not _rm2_is_dominant and rm2.containsSeventh():
                seventh = chord2.seventh
                seven_idx = pchord2.index(seventh)
                if ( pchord1[seven_idx] != seventh
                and (seven_idx != 0 or chord1[seven_idx].name == seventh.name) ): #ForgiveBass && does not allow enharmonic equivalent (respelling) preparation.
                    _log(f"VL: Nondominant Seven not prepared (S or PSR) voice:{seven_idx} cost:{_config['vl_nd7_not_prepared']}")
                    cost += _config['vl_nd7_not_prepared']
            
            # (GENERIC)
            # VOICE CROSSING
            dbgtemp = (chord1[0]>chord2[1])+(chord1[1]<chord2[0]) + (chord1[1]>chord2[2])+(chord1[2]<chord2[1]) + (chord1[2]>chord2[3])+(chord1[3]<chord2[2])
            if dbgtemp: _log(f"DBG: Voice crossing: {dbgtemp} voices.")
            cost += _config['vl_voice_crossing'] * ((chord1[0]>chord2[1])+(chord1[1]<chord2[0]) + (chord1[1]>chord2[2])+(chord1[2]<chord2[1]) + (chord1[2]>chord2[3])+(chord1[3]<chord2[2]))
            
            # LEAPS: Avoid big leaps (generally). Octave leaps in bass is ok. Extra penalty for dissonant leaps, semitone-steps are not considered dissonant leaps (d2s not yet considered)
            diffs = [ (abs(i.generic.value), not(i.specifier in {mus.interval.Specifier.PERFECT, mus.interval.Specifier.MAJOR, mus.interval.Specifier.MINOR} or i.generic.value==1))
                      for i in (mus.interval.Interval(noteStart=chord1[j], noteEnd=chord2[j]) for j in range(4)) ]
            _log("LEAPS: diffs=", diffs)
            _log(f"Bass:{(0 if diffs[0][0] <= 5 or diffs[0][0] == 8 else _config['vl_bass_leap_gt5'] if diffs[0][0] <  8 else _config['vl_bass_leap_gt8'])} ::",
                f"Tenor:{(0 if diffs[1][0]<= 2   else _config['vl_tenor_leap_3']   if diffs[1][0] == 3 else _config['vl_tenor_leap_4to5']   if diffs[1][0] <= 5 else _config['vl_tenor_leap_gt5']   if diffs[1][0] <= 8 else _config['vl_tenor_leap_gt8'])}, TChrom:{_config['vl_tenor_leap_dissonant'] * diffs[1][1]},",
                f"Alto:{(0 if diffs[2][0]<= 2    else _config['vl_alto_leap_3']    if diffs[2][0] == 3 else _config['vl_alto_leap_4to5']    if diffs[2][0] <= 5 else _config['vl_alto_leap_gt5']    if diffs[2][0] <= 8 else _config['vl_alto_leap_gt8'])}, AChrom:{_config['vl_alto_leap_dissonant'] * diffs[2][1]},",
                f"Soprano:{(0 if diffs[3][0]<= 2 else _config['vl_soprano_leap_3'] if diffs[3][0] == 3 else _config['vl_soprano_leap_4to5'] if diffs[3][0] <= 5 else _config['vl_soprano_leap_gt5'] if diffs[3][0] <= 8 else _config['vl_soprano_leap_gt8'])}, SChrom:{_config['vl_soprano_leap_dissonant'] * diffs[3][1]}")
            cost += ((0 if diffs[0][0] <= 5 or diffs[0][0] == 8               else                                                                              _config['vl_bass_leap_gt5']    if diffs[0][0] <  8 else _config['vl_bass_leap_gt8'])    + _config['vl_bass_leap_dissonant']    * diffs[0][1]  # Bass
                    + (0 if diffs[1][0]<= 2 else _config['vl_tenor_leap_3']   if diffs[1][0] == 3 else _config['vl_tenor_leap_4to5']   if diffs[1][0] <= 5 else _config['vl_tenor_leap_gt5']   if diffs[1][0] <= 8 else _config['vl_tenor_leap_gt8'])   + _config['vl_tenor_leap_dissonant']   * diffs[1][1]  # Tenor
                    + (0 if diffs[2][0]<= 2 else _config['vl_alto_leap_3']    if diffs[2][0] == 3 else _config['vl_alto_leap_4to5']    if diffs[2][0] <= 5 else _config['vl_alto_leap_gt5']    if diffs[2][0] <= 8 else _config['vl_alto_leap_gt8'])    + _config['vl_alto_leap_dissonant']    * diffs[2][1]  # Alto
                    + (0 if diffs[3][0]<= 2 else _config['vl_soprano_leap_3'] if diffs[3][0] == 3 else _config['vl_soprano_leap_4to5'] if diffs[3][0] <= 5 else _config['vl_soprano_leap_gt5'] if diffs[3][0] <= 8 else _config['vl_soprano_leap_gt8']) + _config['vl_soprano_leap_dissonant'] * diffs[3][1]) # Soprano
            
            # prefer bass leaping down octave over bass leaping up.
            if diffs[0][0]==8 and mus.interval.Interval(noteStart=chord1[0],noteEnd=chord2[0]).direction.value==1:
                _log(f"Bass leaps octave up, cost:{_config['vl_bass_leaps_octave_up']}")
                cost += _config['vl_bass_leaps_octave_up']
            
            # SPECIAL CASE (REPEATED CHORD)
            if rm1==rm2 and diffs[3][0]==1 and diffs[2][0]==1 and diffs[1][0]==1: cost += _config['vl_repeated_chord_static']
            
            # PARALLELISMS
            for i in range(3): # the i=3 (range(4)) case is degenerate.
                i1, i2 = pchord1[i].midi, pchord2[i].midi
                if i1 == i2: continue # oblique motion
                for j in range(i+1, 4):
                    j1, j2 = pchord1[j].midi, pchord2[j].midi
                    
                    # Parallel or Contrary fifths or octaves check.
                    if (j1-i1)%12 == (j2-i2)%12 and (j1-i1)%12 in {0, 7}:
                        _log(f"Parallelism, voices:{i}&{j} cost:{_config['vl_parallelism']} outer_cost:{_config['vl_parallelism_outer']} outer:{i==0 and j==3}")
                        cost += _config['vl_parallelism_outer'] if (i==0 and j==3) else _config['vl_parallelism']
                    
                    # Unequal 5ths. Bass & another voice has a º5 -> P5. (double not oblique voices)
                    if i == 0 and j1 != j2 and (j1-i1)%12==6 and (j2-i2)%12==7:
                        _log(f"Unequal Fifth, voices:{i}&{j} cost:{_config['vl_unequal_5']}, outer_cost:{_config['vl_unequal_5_outer']} outer:{j==3}")
                        cost += _config['vl_unequal_5_outer'] if j==3 else _config['vl_unequal_5']
            
            # DIRECT/HIDDEN: Outer voices move in similar motion into P5 or P8 and soprano has a leap.
            s1, s2, b1, b2 = pchord1[3].midi, pchord2[3].midi, pchord1[0].midi, pchord2[0].midi
            if abs(s2-s1) > 2 and (s2-b2)%12 in {0,7}:
                _log(f"Direct fifth/octave in outer voices, cost:{_config['vl_direct_parallelism']}")
                cost += _config['vl_direct_parallelism']

            # Static melody in soprano
            if s2 == s1:
                _log(f"Melody Static, cost:{_config['vl_melody_static']}")
                cost += _config['vl_melody_static']

            # OUTER VOICES SHOULD NOT SIMILAR MOTION (should be incontrary motion instead)
            if mus.interval.Interval(noteStart=chord1[3], noteEnd=chord2[3]).direction.value * mus.interval.Interval(noteStart=chord1[0], noteEnd=chord2[0]).direction.value == 1:
                _log(f"Outer voices in similar motion, cost:{_config['vl_outer_voices_similar_motion']}")
                cost += _config['vl_outer_voices_similar_motion']
            
            return cost.count

        return _voiceLeadingCost_Debug

    def _voiceLeadingCostDebug(self, chord1, rm1, chord2, rm2):
        """\
        Simplifying construct for voiceLeadingCost
        """
        return self._get_voiceLeadingCostFunction_Debug(rm1, rm2)(chord1, chord2)


    def _generateVoicings(self, chordMembers):
        """\
        Helper function for voiceChord

        Given four notes to voice, try to voice using self.voices
        Also tasked to handle voicing rules. dist SA, AT < 8ve, dist TB < 2-8ves
        """

        assert len(chordMembers) == 4

        # Strategy: try a random Soprano octave to start,
        # for Alto and Tenor there is basically only one correct choice; we are locked in.
        bass = chordMembers.pop(0)
        # sn,an,tn,bass: note names of chord members. s,a,t,b are pitches
        for sn, an, tn in permutations(chordMembers, 3):
            for s in self._generatePitches(mus.pitch.Pitch(sn), lb=self.ranges[3][2], ub=self.ranges[3][3]):
                a = mus.pitch.Pitch(an)
                a.octave = nextOctaveDown(an, s)
                t = mus.pitch.Pitch(tn)
                t.octave = nextOctaveDown(tn, a)
                if not (self.ranges[2][2]<=a<=self.ranges[2][3] and self.ranges[1][2]<=t<=self.ranges[1][3]):
                    continue # make sure Alto and Tenor are in range
                for b in self._generatePitches(mus.pitch.Pitch(bass), lb=max(self.ranges[0][2], t.transpose('-d15')), ub=min(self.ranges[0][3], t.transpose('-m2'))):
                    yield mus.chord.Chord(deepcopy([b,t,a,s]))

    def voiceChord(self, rm):
        """\
        Overrides FourPartBaseObject.voiceChord(); only takes one argument (Roman Numeral).

        Generates possible 4-part voicings for a triad or seventh chord.
        Secondary dominants should be given in the key they tonicize, rather than the home key of the progression.
        """

        # Decides what set (multiset) of notes to use, hands off to _generateVoicings to determine potential voicings.

        # This step mostly determines doubling and avoids doubling leading/tendency tones.
        # Seventh chords can have incompelete voicings, but the fa->mi (aka the seventh) of seventh chords cannot be doubled (PSR Rule)

        # LT for secondary dominants are adjusted to the LT in the secondary key.
        if rm.secondaryRomanNumeral:
            LT = rm.secondaryRomanNumeralKey.getLeadingTone().name
        else:
            LT = rm.key.getLeadingTone().name # Leading Tone
        
        # WARNING: make sure the first element in the list is the root

        if rm.containsSeventh():
            # SEVENTH CHORD
            yield from self._generateVoicings([p.name for p in rm.pitches])
            # Incomplete chord: Try omitting fifth if chord is in root position, unless chord is diminished (+half diminished)
            if rm.inversion() == 0 and rm.quality != 'diminished':
                # double root
                if rm.root().name != LT:
                    yield from self._generateVoicings([rm.root().name]*2 + [rm.third.name, rm.seventh.name])
                # double third
                if rm.third.name != LT:
                    yield from self._generateVoicings([rm.root().name, rm.seventh.name] + [rm.third.name]*2)
        else:
            # TRIAD
            chordMembers = [p.name for p in rm.pitches]
            if rm.inversion() == 2:
                # 64 chord must double fifth
                yield from self._generateVoicings(chordMembers + [rm.fifth.name])
            else:
                # double root
                if rm.root().name != LT:
                    yield from self._generateVoicings(chordMembers + [rm.root().name])
                    # Incomplete chord: Try omitting fifth if chord is in root position, unless chord is diminished
                    if rm.inversion() == 0 and rm.quality != 'diminished':
                        # tripled root
                        yield from self._generateVoicings([rm.root().name]*3 + [rm.third.name])
                        # doubled root and doubled third
                        if rm.third.name != LT:
                            yield from self._generateVoicings([rm.root().name]*2 + [rm.third.name]*2)
                # double third
                if rm.third.name != LT:
                    yield from self._generateVoicings(chordMembers + [rm.third.name])
                # double fifth
                if rm.fifth.name != LT:
                    yield from self._generateVoicings(chordMembers + [rm.fifth.name])

    # "Chord Mode"-Specific 4Part Writing Functions
    @staticmethod
    def parseProgression(prog): # chord progression: str
        """\
        Chord Progression Parser
        Format Guideline for FourPartChords:
        [keysig for M21] : [RomanNumeral chords]
        RomanNumerals: 0 -> ø, chord!rhythm, rhythm in quarterLengths
        """
        prog = [l.strip().split(":") for l in prog.replace("0", "ø").split("\n") if l.strip() and not l.strip().startswith('//')]
        phrases = []
        for key, chords in prog:
            phrase_key = mus.key.Key(key)
            phrase = []
            rhythm = []
            # listcomp is technically faster, but a pain to write/read/maintain. This operation is only done once, no need to optimize!
            # phrases.append([(lambda clist: (RomanNumeral(clist[0], phrase_key), rhythm.append(eval(clist[1])) if len(clist) > 1 and isinstance(eval(clist[1]), int) else rhythm.append(1))[0] )(chord.split('!')) for chord in filter(None, chords.split())])
            for chord in chords.split(' '):
                if not chord:
                    continue
                clist = chord.split('!')
                phrase.append( (mus.roman.RomanNumeral(clist[0], phrase_key),) ) # as a singleton tuple
                if len(clist) > 1 and clist[1]:
                    try:
                        rhythm.append(Fraction(clist[1]))
                    except ValueError:
                        self.log("PARSER: Value Error for an Rhythm Element... ignoring and adding 1q instead...")
                        rhythm.append(1)
                else:
                    rhythm.append(1)
            phrases.append((phrase, rhythm))

        return phrases
