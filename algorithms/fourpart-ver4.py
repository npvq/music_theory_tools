from itertools import permutations
from copy import deepcopy
# from fractions import Fraction
# from enum import IntEnum

from music21.note import Note
from music21.pitch import Pitch, Accidental
from music21.chord import Chord
from music21.roman import RomanNumeral
from music21.key import Key
from music21.interval import Interval, Specifier

from music21.meter import TimeSignature
from music21.clef import BassClef, TrebleClef
from music21.instrument import Piano
from music21.stream import Part, Score, Voice

from settings import default_config

# for more implementation details, see previous versions! (especially ver2)

DEBUG = True
import time
def dbg(*msg):
	if DEBUG:
		print("DBG:", " ".join([i.__str__() for i in msg]))

# alternative to pitchClass, returns 0..6 for C..B (for comparison purposes)
scale_value = lambda n : {'C':0,'D':1,'E':2,'F':3,'G':4,'A':5,'B':6}[n[0]]

# helper to fetch resolution target notes (ignore return value) [also note strict inequality >/<]
aboveOctave = lambda t_p, p: p.octave if scale_value(t_p.name) > scale_value(p.name) else p.octave+1 # (target pitch and reference pitch)
belowOctave = lambda t_p, p: p.octave if scale_value(t_p.name) < scale_value(p.name) else p.octave-1

# class Solfege(IntEnum):
# 	DO = 0
# 	RE = 1
# 	MI = 2
# 	FA = 3
# 	SOL = 4
# 	LA = 5
# 	TI = 6

# temp: there should be a better solution, but this one will do for now.
_dominant = {'major': ['5', '7'], 'minor': ['5', '#7']}
_tonic = {'major': ['1', '6'], 'minor': ['1', '6']}

class SATB(object):

	def __init__(self, **kwargs):
		self.config = default_config
		self.config.update(kwargs)

		self.ranges = [[self.config['bass_range_min'], self.config['bass_range_max'], self.config['bass_range_min_allowable'], self.config['bass_range_max_allowable']],
					   [self.config['tenor_range_min'], self.config['tenor_range_max'], self.config['tenor_range_min_allowable'], self.config['tenor_range_max_allowable']],
					   [self.config['alto_range_min'], self.config['alto_range_max'], self.config['alto_range_min_allowable'], self.config['alto_range_max_allowable']],
					   [self.config['soprano_range_min'], self.config['soprano_range_max'], self.config['soprano_range_min_allowable'], self.config['soprano_range_max_allowable']]]

		self.chordCost = self._get_chordCost()

	@staticmethod
	def _generate_pitches(query, lb=Pitch('A0'), ub=Pitch('C8')): # lower & upper bounds
		"""Query all notes in range of a certain pitch-class. Those outside the common range will be assigned a cost."""
		
		# We start checking from the same octave as the lower bound
		query.octave = lb.octave
		
		while (query.midi <= ub.midi):
			if (query.midi >= lb.midi):
				yield query
			query.octave += 1

	def _generate_voicings(self, chordMembers):
		"""Given four notes to voice, try to voice using self.voices
		   Also tasked to handle voicing rules. dist SA, AT < 8ve, dist TB < 2-8ves"""
		
		assert len(chordMembers) == 4

		# fetches appropriate octave value one voice down. (prevents overlapping and spacing errors)
		# note: same note twice means go an octave down, hence the strict inequality (<)
		nextOctaveDown = lambda new_name, last_pitch: last_pitch.octave if scale_value(new_name) < scale_value(last_pitch.name) else last_pitch.octave-1

		# Strategy: try a random Soprano note and use spacing rules to go down,
		# for Alto and Tenor there is basically only one correct choice; we are locked in.
		bass = chordMembers.pop(0)
		# sn,an,tn,bass: note names of chord members. s,a,t,b: actual pitches
		for sn, an, tn in permutations(chordMembers, 3):
			for s in self._generate_pitches(Pitch(sn), lb=self.ranges[3][2], ub=self.ranges[3][3]):
				a = Pitch(an)
				a.octave = nextOctaveDown(an, s)
				t = Pitch(tn)
				t.octave = nextOctaveDown(tn, a)
				if not (self.ranges[2][2]<=a<=self.ranges[2][3] and self.ranges[1][2]<=t<=self.ranges[1][3]):
					continue # make sure Alto and Tenor are in range
				for b in self._generate_pitches(Pitch(bass), lb=max(self.ranges[0][2], t.transpose('-d15')), ub=min(self.ranges[0][3], t.transpose('-m2'))):
					yield Chord(deepcopy([b,t,a,s]))

	def voiceChord(self, rm): # roman numeral
		"""Generates possible 4-part voicings for a triad or seventh chord.
		   Secondary dominants should be given in the key they tonicize, rather than the home key of the progression"""

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
			yield from self._generate_voicings([pitch.name for pitch in rm.pitches])
			# Incomplete chord: Try omitting fifth if chord is in root position
			if rm.inversion() == 0:
				# double root
				if rm.root().name != LT:
					yield from self._generate_voicings([rm.root().name]*2 + [rm.third.name, rm.seventh.name])
				# double third
				if rm.third.name != LT:
					yield from self._generate_voicings([rm.root().name, rm.seventh.name] + [rm.third.name]*2)
		else:
			# TRIAD
			chordMembers = [pitch.name for pitch in rm.pitches]
			if rm.inversion() == 2:
				# 64 chord must double fifth
				yield from self._generate_voicings(chordMembers + [rm.fifth.name])
			else:
				# double root
				if rm.root().name != LT:
					yield from self._generate_voicings(chordMembers + [rm.root().name])
					# Incomplete chord: Try omitting fifth if chord is in root position
					if rm.inversion() == 0:
						# tripled root
						yield from self._generate_voicings([rm.root().name]*3 + [rm.third.name])
						# doubled root and doubled third
						if rm.third.name != LT:
							yield from self._generate_voicings([rm.root().name]*2 + [rm.third.name]*2)
				# double third
				if rm.third.name != LT:
					yield from self._generate_voicings(chordMembers + [rm.third.name])
				# double fifth
				if rm.fifth.name != LT:
					yield from self._generate_voicings(chordMembers + [rm.fifth.name])

	def _get_chordCost(self):

		_midi_ranges = [[p.midi for p in v] for v in self.ranges]
		_ch_voice_outside_common_range = self.config['ch_voice_outside_common_range']
		_ch_voice_outside_range = self.config['ch_voice_outside_range']
		_ch_triad_did_not_double_root = self.config['ch_triad_did_not_double_root']
		_ch_triad_inc_tripled_root = self.config['ch_triad_inc_tripled_root']
		_ch_triad_inc_doubled_third = self.config['ch_triad_inc_doubled_third']
		_ch_triad_inc_tripled_root_last = self.config['ch_triad_inc_tripled_root_last']
		_ch_triad_inc_doubled_third_last = self.config['ch_triad_inc_doubled_third_last']
		_ch_seventh_inc_doubled_root = self.config['ch_seventh_inc_doubled_root']
		_ch_seventh_inc_doubled_third = self.config['ch_seventh_inc_doubled_third']
		_ch_last_not_authentic_third = self.config['ch_last_not_authentic_third']
		_ch_last_not_authentic_fifth = self.config['ch_last_not_authentic_fifth']

		def _chordCost(chord, rm, last_chord=False):
			"""This method computes the cost of chord voicing infractions and is run once on every chord.
			   Its purpose is to encourage some voicings over others."""
			# Note to reader: this function should only discriminate between the different voicings of a particular chord as the chord itself has already been decided.
			cost = 0
			_set_size = len(set(chord.pitchClasses))
			# encourage full chord voicings, prefer root doubling.
			if rm.containsSeventh(): # SEVENTH CHORD
				if _set_size < 4:
					if chord.pitchClasses.count(rm.root().pitchClass) == 2:
						cost += _ch_seventh_inc_doubled_root
					else:
						cost += _ch_seventh_inc_doubled_third
			else: # TRIAD
				if rm.inversion() != 2 and chord.pitchClasses.count(rm.root().pitchClass) < 2:
						cost += _ch_triad_did_not_double_root
				if _set_size < 3:
					# incomplete chord should be last chord (should also be RP, but not going to check.)
					if chord.pitchClasses.count(rm.root().pitchClass) == 3:
						cost += _ch_triad_inc_tripled_root_last if last_chord else _ch_triad_inc_tripled_root
					else:
						cost += _ch_triad_inc_doubled_third_last if last_chord else _ch_triad_inc_doubled_third
			# check voice ranges:
			for i in range(4):
				if _midi_ranges[i][0] <= chord[i].pitch.midi <= _midi_ranges[i][1]:
					continue
				elif _midi_ranges[i][2] <= chord[i].pitch.midi <= _midi_ranges[i][3]:
					cost += _ch_voice_outside_common_range
				else:
					cost += _ch_voice_outside_range # not permissible
			# slightly prefer authentic cadences (soprano doubles root)
			if last_chord and rm.figure in {'i', 'I'} and chord[3].pitch.name != rm.root().name:
				if (chord[3].pitch.name == rm.third.name):
					cost += _ch_last_not_authentic_third
				else:
					cost += _ch_last_not_authentic_fifth
			return cost

		return _chordCost

	def _get_voiceLeadingCostFunction(self, rm1, rm2):
		"""This method provides a voiceLeadingCost function pre-loaded with roman numerals."""
		# Strategy: separate out into rm1-dominant, rm1-nondominan, and either-way groups??

		# OVERHEAD
		_rm1_key = rm1.secondaryRomanNumeralKey if rm1.secondaryRomanNumeral else rm1.key
		_rm2_key = rm2.secondaryRomanNumeralKey if rm2.secondaryRomanNumeral else rm2.key
		# Functional
		func1 = (lambda n: n[1].modifier+str(n[0]) if n[1] else str(n[0]))(rm1.scaleDegreeWithAlteration)
		func2 = (lambda n: n[1].modifier+str(n[0]) if n[1] else str(n[0]))(rm2.scaleDegreeWithAlteration)
		_rm1_is_dominant = func1 in _dominant[_rm1_key.mode]
		_rm2_is_dominant = func2 in _dominant[_rm2_key.mode]
		_rm2_is_tonic = func2 in _tonic[_rm2_key.mode]
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
		# make local function: optimization
		_above = aboveOctave
		_below = belowOctave

		# generic settings
		_vl_voice_crossing = self.config['vl_voice_crossing']
		_vl_bass_leap_gt5 = self.config['vl_bass_leap_gt5']
		_vl_bass_leap_gt8 = self.config['vl_bass_leap_gt8']
		_vl_bass_leap_dissonant = self.config['vl_bass_leap_dissonant']
		_vl_tenor_leap_3 = self.config['vl_tenor_leap_3']
		_vl_tenor_leap_4to5 = self.config['vl_tenor_leap_4to5']
		_vl_tenor_leap_gt5 = self.config['vl_tenor_leap_gt5']
		_vl_tenor_leap_gt8 = self.config['vl_tenor_leap_gt8']
		_vl_tenor_leap_dissonant = self.config['vl_tenor_leap_dissonant']
		_vl_alto_leap_3 = self.config['vl_alto_leap_3']
		_vl_alto_leap_4to5 = self.config['vl_alto_leap_4to5']
		_vl_alto_leap_gt5 = self.config['vl_alto_leap_gt5']
		_vl_alto_leap_gt8 = self.config['vl_alto_leap_gt8']
		_vl_alto_leap_dissonant = self.config['vl_alto_leap_dissonant']
		_vl_soprano_leap_3 = self.config['vl_soprano_leap_3']
		_vl_soprano_leap_4to5 = self.config['vl_soprano_leap_4to5']
		_vl_soprano_leap_gt5 = self.config['vl_soprano_leap_gt5']
		_vl_soprano_leap_gt8 = self.config['vl_soprano_leap_gt8']
		_vl_soprano_leap_dissonant = self.config['vl_soprano_leap_dissonant']
		_vl_bass_leaps_octave_up = self.config['vl_bass_leaps_octave_up']
		_vl_parallelism = self.config['vl_parallelism']
		_vl_parallelism_outer = self.config['vl_parallelism_outer']
		_vl_unequal_5 = self.config['vl_unequal_5']
		_vl_unequal_5_outer = self.config['vl_unequal_5_outer']
		_vl_direct_parallelism = self.config['vl_direct_parallelism']
		_vl_melody_static = self.config['vl_melody_static']
		_vl_outer_voices_similar_motion = self.config['vl_outer_voices_similar_motion']
		_vl_repeated_chord_static = self.config['vl_repeated_chord_static']

		# function-specific settings
		_vl_lt_violation = self.config['vl_lt_violation']
		_vl_lt_violation_dominant = self.config['vl_lt_violation_dominant']
		_vl_frustrated_lt = self.config['vl_frustrated_lt']
		_vl_frustrated_lt_dominant = self.config['vl_frustrated_lt_dominant']
		_vl_dominant_tt_not_resolved = self.config['vl_dominant_tt_not_resolved']
		_vl_lt_tt_violation_cadential_multiplier = self.config['vl_lt_tt_violation_cadential_multiplier']
		_vl_nd7_not_prepared = self.config['vl_nd7_not_prepared']
		_vl_nd7_not_resolved = self.config['vl_nd7_not_resolved']

		def _voiceLeadingCost(chord1, chord2):
			"""This method computes the costs of voice leading infractions/violations
			   and is run on every adjacent chord pair in a phrase."""
			cost = 0
			# helper
			pchord1 = chord1.pitches
			pchord2 = chord2.pitches
			# FUNCTION SPECIFIC
			if _rm1_is_dominant:
				# ti->ti or ti->do (ti->sol)
				if _LT in chord1.pitchNames:
					lt_idx = chord1.pitchNames.index(_LT) # leadingtone_index : there can only be one.
					if pchord2[lt_idx] not in (pchord1[lt_idx], Pitch(_DO, octave=_above(_DO, pchord1[lt_idx]))) and (lt_idx != 0 or chord2[0].name not in {_LT, _DO.name}): #ForgiveBass if it is *not* at all possible to resolve/sustain
						# FRUSTRATED LEADING TONE (inner voice)
						if lt_idx in {1, 2} and Pitch(_SOL, octave=_below(_SOL, chord1[lt_idx])): cost += _vl_frustrated_lt_dominant
						else: cost += _vl_lt_violation_dominant * (_vl_lt_tt_violation_cadential_multiplier if _resolves else 1)
				# fa->mi
				if not _rm2_is_dominant: #(or _resolves) Note: even in resolution, Dom/V -> i64 can have the "fa" held/sustained before resolving to "mi."
					if _FT in chord1.pitchNames: # possibly more than one
						for ft_idx, p in enumerate(chord1.pitchNames):
							if p == _FT and pchord2[ft_idx] not in (chord1[ft_idx].pitch, Pitch(_MI, octave=_below(_MI, pchord1[ft_idx]))) and (ft_idx != 0 or chord2[ft_idx].name == _MI.name): #ForgiveBass
									cost += _vl_dominant_tt_not_resolved * (_vl_lt_tt_violation_cadential_multiplier if _resolves else 1)
			else: # rm1 not dominant
				# ti->ti or ti->do (ti->sol)
				if _LT in chord1.pitchNames:
					lt_idx = chord1.pitchNames.index(_LT) # leadingtone_index : there can only be one.
					if pchord2[lt_idx] not in (pchord1[lt_idx], Pitch(_DO, octave=_above(_DO, pchord1[lt_idx]))) and (lt_idx != 0 or chord2[0].name not in {_LT, _DO.name}): #ForgiveBass if it is *not* at all possible to resolve/sustain
						# FRUSTRATED LEADING TONE (inner voice)
						if lt_idx in {1, 2} and Pitch(_SOL, octave=_below(_SOL, chord1[lt_idx])): cost += _vl_frustrated_lt
						else: cost += _vl_lt_violation
				# non-dominant 7 resolution
				if rm1.containsSeventh():
					seventh = chord1.seventh
					seven_idx = pchord1.index(seventh) # (seventh cannot be doubled, so is unique)
					# Resolutions have to go down a m2 or M2.
					if not (seventh == pchord2[seven_idx] or Interval(noteStart=chord2[seven_idx], noteEnd=chord1[seven_idx]).name in {'m2','M2'}) and (seven_idx != 0 or (seventh.pitchClass + 12 - chord2[seven_idx].pitchClass)%12 > 2): # second (): #ForgiveBass
						cost += _vl_nd7_not_resolved

			# non-dominant 7 preparation
			if not _rm2_is_dominant and rm2.containsSeventh():
				seventh = chord2.seventh
				seven_idx = pchord2.index(seventh)
				if pchord1[seven_idx] != seventh and (seven_idx != 0 or chord1[seven_idx].name == seventh.name): #ForgiveBass && does not allow enharmonic equivalent (respelling) preparation.
					cost += _vl_nd7_not_prepared
			# GENERIC
			# VOICE CROSSING
			cost += _vl_voice_crossing * ((chord1[0]>chord2[1])+(chord1[1]<chord2[0]) + (chord1[1]>chord2[2])+(chord1[2]<chord2[1]) + (chord1[2]>chord2[3])+(chord1[3]<chord2[2]))
			# LEAPS: Avoid big leaps (generally). Octave leaps in bass is ok. Extra penalty for dissonant leaps, semitone-steps are not considered dissonant leaps
			diffs = [ (abs(i.generic.value), not(i.specifier in {Specifier.PERFECT, Specifier.MAJOR, Specifier.MINOR} or i.generic.value==1)) for i in (Interval(noteStart=chord1[i], noteEnd=chord2[i]) for i in range(4)) ]
			cost += ((0 if diffs[0][0] <= 5 or diffs[0][0] == 8     else                                                                    _vl_bass_leap_gt5    if diffs[0][0] <  8 else _vl_bass_leap_gt8)    + _vl_bass_leap_dissonant    * diffs[0][1]  # Bass
					+ (0 if diffs[1][0]<= 2 else _vl_tenor_leap_3   if diffs[1][0] == 3 else _vl_tenor_leap_4to5   if diffs[1][0] <= 5 else _vl_tenor_leap_gt5   if diffs[1][0] <= 8 else _vl_tenor_leap_gt8)   + _vl_tenor_leap_dissonant   * diffs[1][1]  # Tenor
					+ (0 if diffs[2][0]<= 2 else _vl_alto_leap_3    if diffs[2][0] == 3 else _vl_alto_leap_4to5    if diffs[2][0] <= 5 else _vl_alto_leap_gt5    if diffs[2][0] <= 8 else _vl_alto_leap_gt8)    + _vl_alto_leap_dissonant    * diffs[2][1]  # Alto
					+ (0 if diffs[3][0]<= 2 else _vl_soprano_leap_3 if diffs[3][0] == 3 else _vl_soprano_leap_4to5 if diffs[3][0] <= 5 else _vl_soprano_leap_gt5 if diffs[3][0] <= 8 else _vl_soprano_leap_gt8) + _vl_soprano_leap_dissonant * diffs[3][1]) # Soprano
			# prefer bass leaping down octave over bass leaping up.
			if diffs[0][0]==8 and Interval(noteStart=chord1[0],noteEnd=chord2[0]).direction.value==1: cost += _vl_bass_leaps_octave_up
			# SPECIAL CASE (REPEATED CHORD)
			if rm1==rm2 and diffs[3][0]==1 and diffs[2][0]==1 and diffs[1][0]==1: cost += _vl_repeated_chord_static
			# PARALLELISMS
			for i in range(3): # the i=3 (range(4)) case is degenerate.
				i1, i2 = pchord1[i].midi, pchord2[i].midi
				if i1 == i2: continue # oblique motion
				for j in range(i+1, 4):
					j1, j2 = pchord1[j].midi, pchord2[j].midi
					# Parallel or Contrary fifths or octaves check.
					if (j1-i1)%12 == (j2-i2)%12 and (j1-i1)%12 in {0, 7}:
						cost += _vl_parallelism_outer if (i==0 and j==3) else _vl_parallelism
					# Unequal 5ths. Bass & another voice has a º5 -> P5. (double not oblique voices)
					if i == 0 and j1 != j2 and (j1-i1)%12==6 and (j2-i2)%12==7:
						cost += _vl_unequal_5_outer if j==3 else _vl_unequal_5
			# DIRECT/HIDDEN: Outer voices move in similar motion into P5 or P8 and soprano has a leap.
			s1, s2, b1, b2 = pchord1[3].midi, pchord2[3].midi, pchord1[0].midi, pchord2[0].midi
			if abs(s2-s1) > 2 and (s2-b2)%12 in {0,7}: cost += 80
			# Static melody in soprano
			if s2 == s1: cost += _vl_melody_static
			# OUTER VOICES SHOULD NOT SIMILAR MOTION (should be incontrary motion instead)
			if Interval(noteStart=chord1[3], noteEnd=chord2[3]).direction.value * Interval(noteStart=chord1[0], noteEnd=chord2[0]).direction.value == 1: cost += _vl_outer_voices_similar_motion
			return cost

		return _voiceLeadingCost

	def _voiceLeadingCostDebug(self, chord1, rm1, chord2, rm2):
		"""This method provides a voiceLeadingCost function pre-loaded with roman numerals."""
		# Strategy: separate out into rm1-dominant, rm1-nondominan, and either-way groups??

		# OVERHEAD
		_rm1_key = rm1.secondaryRomanNumeralKey if rm1.secondaryRomanNumeral else rm1.key
		_rm2_key = rm2.secondaryRomanNumeralKey if rm2.secondaryRomanNumeral else rm2.key
		# Functional
		func1 = (lambda n: n[1].modifier+str(n[0]) if n[1] else str(n[0]))(rm1.scaleDegreeWithAlteration)
		func2 = (lambda n: n[1].modifier+str(n[0]) if n[1] else str(n[0]))(rm2.scaleDegreeWithAlteration)
		_rm1_is_dominant = func1 in _dominant[_rm1_key.mode]
		_rm2_is_dominant = func2 in _dominant[_rm2_key.mode]
		_rm2_is_tonic = func2 in _tonic[_rm2_key.mode]
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
		# make local function: optimization
		_above = aboveOctave
		_below = belowOctave

		# generic settings
		_vl_voice_crossing = self.config['vl_voice_crossing']
		_vl_bass_leap_gt5 = self.config['vl_bass_leap_gt5']
		_vl_bass_leap_gt8 = self.config['vl_bass_leap_gt8']
		_vl_bass_leap_dissonant = self.config['vl_bass_leap_dissonant']
		_vl_tenor_leap_3 = self.config['vl_tenor_leap_3']
		_vl_tenor_leap_4to5 = self.config['vl_tenor_leap_4to5']
		_vl_tenor_leap_gt5 = self.config['vl_tenor_leap_gt5']
		_vl_tenor_leap_gt8 = self.config['vl_tenor_leap_gt8']
		_vl_tenor_leap_dissonant = self.config['vl_tenor_leap_dissonant']
		_vl_alto_leap_3 = self.config['vl_alto_leap_3']
		_vl_alto_leap_4to5 = self.config['vl_alto_leap_4to5']
		_vl_alto_leap_gt5 = self.config['vl_alto_leap_gt5']
		_vl_alto_leap_gt8 = self.config['vl_alto_leap_gt8']
		_vl_alto_leap_dissonant = self.config['vl_alto_leap_dissonant']
		_vl_soprano_leap_3 = self.config['vl_soprano_leap_3']
		_vl_soprano_leap_4to5 = self.config['vl_soprano_leap_4to5']
		_vl_soprano_leap_gt5 = self.config['vl_soprano_leap_gt5']
		_vl_soprano_leap_gt8 = self.config['vl_soprano_leap_gt8']
		_vl_soprano_leap_dissonant = self.config['vl_soprano_leap_dissonant']
		_vl_bass_leaps_octave_up = self.config['vl_bass_leaps_octave_up']
		_vl_parallelism = self.config['vl_parallelism']
		_vl_parallelism_outer = self.config['vl_parallelism_outer']
		_vl_unequal_5 = self.config['vl_unequal_5']
		_vl_unequal_5_outer = self.config['vl_unequal_5_outer']
		_vl_direct_parallelism = self.config['vl_direct_parallelism']
		_vl_melody_static = self.config['vl_melody_static']
		_vl_outer_voices_similar_motion = self.config['vl_outer_voices_similar_motion']
		_vl_repeated_chord_static = self.config['vl_repeated_chord_static']

		# function-specific settings
		_vl_lt_violation = self.config['vl_lt_violation']
		_vl_lt_violation_dominant = self.config['vl_lt_violation_dominant']
		_vl_frustrated_lt = self.config['vl_frustrated_lt']
		_vl_frustrated_lt_dominant = self.config['vl_frustrated_lt_dominant']
		_vl_dominant_tt_not_resolved = self.config['vl_dominant_tt_not_resolved']
		_vl_lt_tt_violation_cadential_multiplier = self.config['vl_lt_tt_violation_cadential_multiplier']
		_vl_nd7_not_prepared = self.config['vl_nd7_not_prepared']
		_vl_nd7_not_resolved = self.config['vl_nd7_not_resolved']

		# debug tools:
		class counter(object):
			def __init__(self, value):
				self.count = value

			def __str__(self):
				return str(self.count)

			def __iadd__(self, other):
				self.count += other
				dbg(f"total_cost:{self.count} (added:{other})")
				return self

		def _voiceLeadingCost(chord1, chord2):
			"""This method computes the costs of voice leading infractions/violations
			   and is run on every adjacent chord pair in a phrase."""
			cost = counter(0)
			# helper
			pchord1 = chord1.pitches
			pchord2 = chord2.pitches
			# FUNCTION SPECIFIC
			if _rm1_is_dominant:
				# ti->ti or ti->do (ti->sol)
				if _LT in chord1.pitchNames:
					lt_idx = chord1.pitchNames.index(_LT) # leadingtone_index : there can only be one.
					if pchord2[lt_idx] not in (pchord1[lt_idx], Pitch(_DO, octave=_above(_DO, pchord1[lt_idx]))) and (lt_idx != 0 or chord2[0].name not in {_LT, _DO.name}): #ForgiveBass if it is *not* at all possible to resolve/sustain
						# FRUSTRATED LEADING TONE (inner voice)
						if lt_idx in {1, 2} and Pitch(_SOL, octave=_below(_SOL, chord1[lt_idx])): 
							dbg(f"VL: frustrated LT (dominant) voice:{lt_idx} cost:{_vl_frustrated_lt_dominant}")
							cost += _vl_frustrated_lt_dominant
						else: 
							dbg(f"VL: LT violation (dominant) voice:{lt_idx} cost:{_vl_lt_violation_dominant}, multiplier:{_vl_lt_tt_violation_cadential_multiplier if _resolves else 1}")
							cost += _vl_lt_violation_dominant * (_vl_lt_tt_violation_cadential_multiplier if _resolves else 1)
				# fa->mi
				if not _rm2_is_dominant: # alternate condition: if _resolves. Note: even in resolution, Dom/V -> i64 can have the "fa" held/sustained before resolving to "mi."
					if _FT in chord1.pitchNames: # possibly more than one
						for ft_idx, p in enumerate(chord1.pitchNames):
							if p == _FT and pchord2[ft_idx] not in (chord1[ft_idx].pitch, Pitch(_MI, octave=_below(_MI, pchord1[ft_idx]))) and (ft_idx != 0 or chord2[ft_idx].name == _MI.name): #ForgiveBass
									dbg(f"VL: fa->mi TT violation voice:{ft_idx} cost:{_vl_dominant_tt_not_resolved}, multiplier:{_vl_lt_tt_violation_cadential_multiplier if _resolves else 1}")
									cost += _vl_dominant_tt_not_resolved * (_vl_lt_tt_violation_cadential_multiplier if _resolves else 1)
			else: # rm1 not dominant
				# ti->ti or ti->do (ti->sol)
				if _LT in chord1.pitchNames:
					lt_idx = chord1.pitchNames.index(_LT) # leadingtone_index : there can only be one.
					if pchord2[lt_idx] not in (pchord1[lt_idx], Pitch(_DO, octave=_above(_DO, pchord1[lt_idx]))) and (lt_idx != 0 or chord2[0].name not in {_LT, _DO.name}): #ForgiveBass if it is *not* at all possible to resolve/sustain
						# FRUSTRATED LEADING TONE (inner voice)
						if lt_idx in {1, 2} and Pitch(_SOL, octave=_below(_SOL, chord1[lt_idx])): 
							dbg(f"VL: frustrated LT (nondominant) voice:{lt_idx} cost:{_vl_frustrated_lt}")
							cost += _vl_frustrated_lt
						else:
							dbg(f"VL: LT violation (nondominant) voice:{lt_idx} cost:{_vl_lt_violation}")
							cost += _vl_lt_violation

				# non-dominant 7 resolution
				if rm1.containsSeventh():
					seventh = chord1.seventh
					seven_idx = pchord1.index(seventh) # (seventh cannot be doubled, so is unique)
					# Resolutions have to go down a m2 or M2.
					if not (seventh == pchord2[seven_idx] or Interval(noteStart=chord2[seven_idx], noteEnd=chord1[seven_idx]).name in {'m2','M2'}) and (seven_idx != 0 or (seventh.pitchClass + 12 - chord2[seven_idx].pitchClass)%12 > 2): # second (): #ForgiveBass
						dbg(f"VL: Nondominant Seven not resolved (R of PSR) voice:{seven_idx} cost:{_vl_nd7_not_resolved}")
						cost += _vl_nd7_not_resolved

			# non-dominant 7 preparation
			if not _rm2_is_dominant and rm2.containsSeventh():
				seventh = chord2.seventh
				seven_idx = pchord2.index(seventh)
				if pchord1[seven_idx] != seventh and (seven_idx != 0 or chord1[seven_idx].name == seventh.name): #ForgiveBass && does not allow enharmonic equivalent (respelling) preparation.
					dbg(f"VL: Nondominant Seven not prepared (S or PSR) voice:{seven_idx} cost:{_vl_nd7_not_prepared}")
					cost += _vl_nd7_not_prepared
			# GENERIC
			# VOICE CROSSING
			dbgtemp = (chord1[0]>chord2[1])+(chord1[1]<chord2[0]) + (chord1[1]>chord2[2])+(chord1[2]<chord2[1]) + (chord1[2]>chord2[3])+(chord1[3]<chord2[2])
			if dbgtemp: print(f"DBG: Voice crossing: {dbgtemp} voices.")
			cost += _vl_voice_crossing * ((chord1[0]>chord2[1])+(chord1[1]<chord2[0]) + (chord1[1]>chord2[2])+(chord1[2]<chord2[1]) + (chord1[2]>chord2[3])+(chord1[3]<chord2[2]))
			# LEAPS: Avoid big leaps (generally). Octave leaps in bass is ok. Extra penalty for dissonant leaps, semitone-steps are not considered dissonant leaps (d2s not yet considered)
			diffs = [ (abs(i.generic.value), not(i.specifier in {Specifier.PERFECT, Specifier.MAJOR, Specifier.MINOR} or i.generic.value==1)) for i in (Interval(noteStart=chord1[i], noteEnd=chord2[i]) for i in range(4)) ]
			dbg("LEAPS: diffs=", diffs)
			dbg(f"Bass:{(0 if diffs[0][0] <= 5 or diffs[0][0] == 8 else _vl_bass_leap_gt5 if diffs[0][0] <  8 else _vl_bass_leap_gt8)} ::",
				f"Tenor:{(0 if diffs[1][0]<= 2 else _vl_tenor_leap_3   if diffs[1][0] == 3 else _vl_tenor_leap_4to5   if diffs[1][0] <= 5 else _vl_tenor_leap_gt5   if diffs[1][0] <= 8 else _vl_tenor_leap_gt8)}, TChrom:{_vl_tenor_leap_dissonant * diffs[1][1]},",
				f"Alto:{(0 if diffs[2][0]<= 2 else _vl_alto_leap_3    if diffs[2][0] == 3 else _vl_alto_leap_4to5    if diffs[2][0] <= 5 else _vl_alto_leap_gt5    if diffs[2][0] <= 8 else _vl_alto_leap_gt8)}, AChrom:{_vl_alto_leap_dissonant * diffs[2][1]},",
				f"Soprano:{(0 if diffs[3][0]<= 2 else _vl_soprano_leap_3 if diffs[3][0] == 3 else _vl_soprano_leap_4to5 if diffs[3][0] <= 5 else _vl_soprano_leap_gt5 if diffs[3][0] <= 8 else _vl_soprano_leap_gt8)}, SChrom:{_vl_soprano_leap_dissonant * diffs[3][1]}")
			cost += ((0 if diffs[0][0] <= 5 or diffs[0][0] == 8     else                                                                    _vl_bass_leap_gt5    if diffs[0][0] <  8 else _vl_bass_leap_gt8)    + _vl_bass_leap_dissonant    * diffs[0][1]  # Bass
					+ (0 if diffs[1][0]<= 2 else _vl_tenor_leap_3   if diffs[1][0] == 3 else _vl_tenor_leap_4to5   if diffs[1][0] <= 5 else _vl_tenor_leap_gt5   if diffs[1][0] <= 8 else _vl_tenor_leap_gt8)   + _vl_tenor_leap_dissonant   * diffs[1][1]  # Tenor
					+ (0 if diffs[2][0]<= 2 else _vl_alto_leap_3    if diffs[2][0] == 3 else _vl_alto_leap_4to5    if diffs[2][0] <= 5 else _vl_alto_leap_gt5    if diffs[2][0] <= 8 else _vl_alto_leap_gt8)    + _vl_alto_leap_dissonant    * diffs[2][1]  # Alto
					+ (0 if diffs[3][0]<= 2 else _vl_soprano_leap_3 if diffs[3][0] == 3 else _vl_soprano_leap_4to5 if diffs[3][0] <= 5 else _vl_soprano_leap_gt5 if diffs[3][0] <= 8 else _vl_soprano_leap_gt8) + _vl_soprano_leap_dissonant * diffs[3][1]) # Soprano
			# prefer bass leaping down octave over bass leaping up.
			if diffs[0][0]==8 and Interval(noteStart=chord1[0],noteEnd=chord2[0]).direction.value==1:
				dbg("Bass leaps octave up, cost:_vl_bass_leaps_octave_up")
				cost += _vl_bass_leaps_octave_up
			# SPECIAL CASE (REPEATED CHORD)
			if rm1==rm2 and diffs[3][0]==1 and diffs[2][0]==1 and diffs[1][0]==1: cost += _vl_repeated_chord_static
			# PARALLELISMS
			for i in range(3): # the i=3 (range(4)) case is degenerate.
				i1, i2 = pchord1[i].midi, pchord2[i].midi
				if i1 == i2: continue # oblique motion
				for j in range(i+1, 4):
					j1, j2 = pchord1[j].midi, pchord2[j].midi
					# Parallel or Contrary fifths or octaves check.
					if (j1-i1)%12 == (j2-i2)%12 and (j1-i1)%12 in {0, 7}:
						dbg(f"Parallelism, voices:{i}&{j} cost:{_vl_parallelism} outer_cost:{_vl_parallelism_outer} outer:{i==0 and j==3}")
						cost += _vl_parallelism_outer if (i==0 and j==3) else _vl_parallelism
					# Unequal 5ths. Bass & another voice has a º5 -> P5. (double not oblique voices)
					if i == 0 and j1 != j2 and (j1-i1)%12==6 and (j2-i2)%12==7:
						dbg(f"Unequal Fifth, voices:{i}&{j} cost:{_vl_unequal_5}, outer_cost:{_vl_unequal_5_outer} outer:{j==3}")
						cost += _vl_unequal_5_outer if j==3 else _vl_unequal_5
			# DIRECT/HIDDEN: Outer voices move in similar motion into P5 or P8 and soprano has a leap.
			s1, s2, b1, b2 = pchord1[3].midi, pchord2[3].midi, pchord1[0].midi, pchord2[0].midi
			if abs(s2-s1) > 2 and (s2-b2)%12 in {0,7}:
				dbg(f"Direct fifth/octave in outer voices, cost:{_vl_direct_parallelism}")
				cost += _vl_direct_parallelism
			# Static melody in soprano
			if s2 == s1:
				dbg(f"Melody Static, cost:{_vl_melody_static}")
				cost += _vl_melody_static
			# OUTER VOICES SHOULD NOT SIMILAR MOTION (should be incontrary motion instead)
			if Interval(noteStart=chord1[3], noteEnd=chord2[3]).direction.value * Interval(noteStart=chord1[0], noteEnd=chord2[0]).direction.value == 1:
				dbg(f"Outer voices in similar motion, cost:{_vl_outer_voices_similar_motion}")
				cost += _vl_outer_voices_similar_motion
			return cost

		return _voiceLeadingCost(chord1, chord2)

	def voiceLeadingCost(self, chord1, rm1, chord2, rm2):
		return self._get_voiceLeadingCostFunction(rm1, rm2)(chord1, chord2)

	def voicePhraseDP(self, phrase): # phrase: one phrase of roman numerals (presumably with some sort of cadence)
		# stc = 3 # store top choices (not yet implemented, mess around with other pathfinding algs and optimize)

		# O(L^2 N), L = max number of voicings per chord (~120), N = number of chords in phrase.
		# the most expensive operation is progressionCost

		L = len(phrase)
		V = [list(self.voiceChord(rm)) for rm in phrase]
		DP = [[None for _ in range(len(V[i]))] for i in range(L)]
		Mask = [[True for _ in range(len(V[i]))] for i in range(L)] # DP MASK

		# localizing class variables: optimization
		_confidence = self.config['dp_confidence']
		_buffer = self.config['dp_buffer']
		
		# first layer i=0, only chord cost, and no back reference.
		dbg(f"DP: Setting up first chord...")
		for j in range(len(V[0])):
			DP[0][j] = (self.chordCost(V[0][j], phrase[0]), None)
		# Mask updating (pruning)
		# pruning first chord options greatly decrease bottleneck during second chord
		bar = _confidence * ( min(DP[0])[0] + self.config['dp_first_buffer']//(len(V[0])*len(V[1])) )
		for j in range(len(V[0])):
			if DP[0][j][0] > bar:
				Mask[0][j] = False

		# subsequent layers i=1..L-1
		for i in range(1, L):
			dbg_temp_count = sum(Mask[i-1]) #### temp
			dbg(f"DP: running {i+1}(th) chord (of {L} total)... (({dbg_temp_count} of {len(V[i-1])})x{len(V[i])}={dbg_temp_count*len(V[i])} pairs to run)")
			start_time = time.time()

			voiceLeadingCost = self._get_voiceLeadingCostFunction(phrase[i-1], phrase[i])
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
					DP[i][j] = (best[0] + self.chordCost(V[i][j], phrase[i], last_chord=True), best[1])
				else:
					DP[i][j] = (best[0] + self.chordCost(V[i][j], phrase[i]), best[1])

			# Mask updating (pruning)
			bar = _confidence * (min(DP[i])[0] + _buffer) 
			for j in range(len(V[i])):
				if DP[i][j][0] > bar:
					Mask[i][j] = False
			
			total_time = time.time() - start_time
			dbg(f"DP:         took {total_time} seconds total ({total_time/(dbg_temp_count*len(V[i]))}) seconds per pair)")

		# retrace the best solution
		dbg(f"DP: Done! Retracing solution...")
		op = DP[-1].index(min(DP[-1])) # op (optimal): always points to the optimal choice at phrase[i].
		dbg(f"Total Cost: {DP[-1][op][0]}")
		sol = []
		for i in reversed(range(L)):
			sol.append(Chord(V[i][op], lyric=phrase[i].figure))
			op = DP[i][op][1] # set op to op's backreference (to the last optimal element)

		sol.reverse()
		return sol


# Note: RomanNumeral.figure

def parseProgression(prog): # chord progression: str
	prog = [l.strip().split(":") for l in prog.split("\n") if l.strip()]
	phrases = []
	rhythm = []
	for key, chords in prog:
		phrase_key = Key(key)
		phrases.append([(lambda clist: (RomanNumeral(clist[0], phrase_key), rhythm.append(eval(clist[1])) if len(clist) > 1 and isinstance(eval(clist[1]), int) else rhythm.append(1))[0] )(chord.split('!')) for chord in filter(None, chords.split())])
	return phrases, rhythm


# credits to Eric Zhang @ github
def generateScore(chords, rhythm=None, ts="4/4"):
    """Generates a four-part score from a sequence of chords.
    Soprano and alto parts are displayed on the top (treble) clef, while tenor
    and bass parts are displayed on the bottom (bass) clef, with correct stem
    directions.
    """
    if rhythm is None:
        rhythm = [1 for _ in chords]
    else: 
    	while len(rhythm) < len(chords):
    		rhythm.extend(rhythm) # lengths is a pattern
    voices = [Voice([Piano()]) for _ in range(4)]
    for chord, duration in zip(chords, rhythm):
        bass, tenor, alto, soprano = [
            Note(p, quarterLength=duration) for p in chord.pitches
        ]
        bass.addLyric(chord.lyric)
        bass.stemDirection = alto.stemDirection = "down"
        tenor.stemDirection = soprano.stemDirection = "up"
        voices[0].append(soprano)
        voices[1].append(alto)
        voices[2].append(tenor)
        voices[3].append(bass)

    SA = Part([TrebleClef(), TimeSignature(ts), voices[0], voices[1]])
    TB = Part([BassClef(), TimeSignature(ts), voices[2], voices[3]])
    score = Score([SA, TB])
    return score


def generateChorale(chorale, rhythm=None, ts="4/4"):
	phrases, rhythm_def = parseProgression(chorale)
	if rhythm:
		rhythm_def = rhythm
	engine = SATB()
	chord_progression = []
	i = 0 ####
	ttt = time.time()
	dbg(f"##### CONFIDENCE VALUE = {engine.config['dp_confidence']}")
	for phrase in phrases:
		tt = time.time()
		i += 1 ####
		dbg(f"PHRASE {i} ====================")
		chord_progression.extend(engine.voicePhraseDP(phrase))
		dbg(f"PHRASE TOTAL TIME: {time.time() - tt} seconds")

	dbg(f"++++++++++ TOTAL TIME ++++++++++ {time.time() - ttt} seconds ++++++++++")

	score = generateScore(chord_progression, rhythm=rhythm_def, ts=ts)
	score.show()
	return chord_progression


def analysis(chorale):
	cp = generateChorale(chorale)
	p = parseProgression(chorale)[0][0]

	for i in range(len(p)-1):
		dbg(f"=========CHORD {i+1} & {i+2}=========")
		x._voiceLeadingCostDebug(cp[i], p[i], cp[i+1], p[i+1])

	return "DONE"


# Extra Utils
def chordProgressionToText(cp):
	print("+S+ +A+ +T+ +B+")
	for chord in cp:
		print("{} {} {} {}".format(chord[3].nameWithOctave, chord[2].nameWithOctave, chord[1].nameWithOctave, chord[0].nameWithOctave))


def textToChordProgression(txt):
	pass


# Unit Tests (temp)
x = SATB()
ar = RomanNumeral('V7','C')
br = RomanNumeral('I','C')
a = list(x.voiceChord(ar))
b = list(x.voiceChord(br))
print(f"a len: {len(a)}, b len: {len(b)}")
ch = """D: I vi I6 IV I64 V I!2
 D: I6 V64 I IV6 V I6 V!2
 D: I IV6 I6 IV I64 V7 vi!2
 D: I6 V43 I I6 ii65 V I!2
 A: I IV64 I vi ii6 V7 I!2
 b: iv6 i64 iv iio6 i64 V7 i!2
 A: IV IV V I6 ii V65 I!2
 D: IV6 I V65 I ii65 V7 I!2"""
chsh = "D: I IV V V7 I!4"
chbach = """Bb: I vi V/vi vi V6/V V/V V I IV7/V V/V V!2
Bb: I V7!2 V7/vi vi IV6 V7 I IV V I!2
Bb: I IV6 IV ii V!2 V6 V7/IV!3 IV!2 vi V6/V V/V V6/V V!2
Bb: V42 I6 I I6 IV!2 viio6 I6 IV ii6!1/2 ii!1/2 I6!2 I ii6 ii V7 I!2"""

