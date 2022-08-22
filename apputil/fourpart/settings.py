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
Settings for fourpart classes.
default_config canonically imported and used in FourPartBaseObject.
See Algorithm README for more information on config specification.
"""

# ----- SYSTEM IMPORTS ----- #



# ----- 3RD PARTY IMPORTS ----- #

# Note: only part used, imported like this for convenience.
from music21.pitch import Pitch

# ----- LOCAL IMPORTS ----- #



# ------------------------------ #

default_config = {
	# voice ranges
	'soprano_range_min': Pitch("E4"), # pitch.Pitch("C4"), # canonical, but a little too low and squishes other voices
	'soprano_range_max': Pitch("G5"),
	'soprano_range_min_allowable': Pitch("B3"),
	'soprano_range_max_allowable': Pitch("A5"),
	'alto_range_min': Pitch("G3"),
	'alto_range_max': Pitch("C5"),
	'alto_range_min_allowable': Pitch("G3"),
	'alto_range_max_allowable': Pitch("D5"),
	'tenor_range_min': Pitch("C3"),
	'tenor_range_max': Pitch("E4"), # pitch.Pitch("G4"), # canonical is G4, but limited to prevent tenor too high
	'tenor_range_min_allowable': Pitch("C3"),
	'tenor_range_max_allowable': Pitch("A4"),
	'bass_range_min': Pitch("E2"),
	'bass_range_max': Pitch("C4"),
	'bass_range_min_allowable': Pitch("D2"),
	'bass_range_max_allowable': Pitch("D4"),

	# DP settings
	'dp_pruning': True,
	'dp_prune_first': True,
	'dp_confidence': 1.3,
	'dp_buffer': 10,
	'dp_first_buffer': 5000,

	# chordCost costs/weights
	'ch_voice_outside_common_range': 4,
	'ch_voice_outside_range': 1e7,
	'ch_triad_did_not_double_root': 2,
	'ch_triad_inc_tripled_root': 8,
	'ch_triad_inc_doubled_third': 6,
	'ch_triad_inc_tripled_root_last': 1,
	'ch_triad_inc_doubled_third_last': 4,
	'ch_seventh_inc_doubled_root': 1,
	'ch_seventh_inc_doubled_third': 5,
	'ch_last_not_authentic_third': 3, # is not authentic (root), is a third instead
	'ch_last_not_authentic_fifth': 4, # is not authentic (root), is a fifth instead. These two settings can force the melody to "have some action"

	# voiceLeadingCost costs/weights
	'vl_lt_violation': 50,
	'vl_lt_violation_dominant': 200,
	'vl_frustrated_lt': 5,
	'vl_frustrated_lt_dominant': 15,
	'vl_dominant_tt_not_resolved': 100,
	'vl_lt_tt_violation_cadential_multiplier': 2,
	'vl_nd7_not_prepared': 20,
	'vl_nd7_not_resolved': 60,
	'vl_voice_crossing': 40,
	'vl_bass_leap_gt5': 30,
	'vl_bass_leap_gt8': 100,
	'vl_bass_leap_dissonant': 50,
	'vl_tenor_leap_3': 5,
	'vl_tenor_leap_4to5': 20,
	'vl_tenor_leap_gt5': 80,
	'vl_tenor_leap_gt8': 100,
	'vl_tenor_leap_dissonant': 50,
	'vl_alto_leap_3': 5,
	'vl_alto_leap_4to5': 20,
	'vl_alto_leap_gt5': 80,
	'vl_alto_leap_gt8': 100,
	'vl_alto_leap_dissonant': 50,
	'vl_soprano_leap_3': 3,
	'vl_soprano_leap_4to5': 15,
	'vl_soprano_leap_gt5': 60,
	'vl_soprano_leap_gt8': 150,
	'vl_soprano_leap_dissonant': 100,
	'vl_bass_leaps_octave_up': 5,
	'vl_parallelism': 100,
	'vl_parallelism_outer': 200,
	'vl_unequal_5': 75,
	'vl_unequal_5_outer': 150,
	'vl_direct_parallelism': 80,
	'vl_melody_static': 5,
	'vl_outer_voices_similar_motion': 1,
	'vl_repeated_chord_static': 50,
}
