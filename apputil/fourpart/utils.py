from music21.note import Note
from music21.pitch import Pitch, Accidental
from music21.chord import Chord
from music21.roman import RomanNumeral
from music21.key import Key, KeySignature
from music21.interval import Interval, Specifier

from music21.meter import TimeSignature
from music21.clef import BassClef, TrebleClef
from music21.layout import StaffGroup
from music21.instrument import Piano
from music21.stream import Part, Score, Voice

from fourpart import FourPartChords, do_nothing

""" Stuff is getting a bit out of hand here
Conventions:
- use `phr` to iterate through all phrases of data.
- use `ch` to iterate through the chords of a phrase when necessary.
"""

class FPChordsQuery(object):

	def __init__(self, engine, cp, ts='4/4', consoleOutput=do_nothing):
		self.engine = engine

		self.engine.logging = True
		self.engine.logStream = consoleOutput

		self.timeSignature = TimeSignature(ts)

		# organization: self.data['TYPE'][PHRASE_NO] then possibly [CHORD_NO]

		# for DP, it is [PHRASE_NO][CHORD_NO][VOICING_NO][0=Current Cost, 1=Best Previous Candidate]
		# for solutions, it is [PHRASE_NO][CHOICE][CHORD_NO][0=Chord Progression, 1=Cost]

		# remember, 'chords' is packed in singleton tuples for compatibility with other FP-Queries

		self.data = {'chords': [], 'rhythm': [], 'DP': [], 'voicings': [], 'solutions': []}

		# solve (DP Memoize)
		for p in self.engine.parseProgression(cp):
			p_chords, p_rhythm = p
			DP, V = engine.DP_MemoizePhrase(p_chords)
			self.data['chords'].append(p_chords)
			self.data['rhythm'].append(p_rhythm)
			self.data['DP'].append(DP)
			self.data['voicings'].append(V)

		# integrity check
		self.length = len(self.data['chords'])
		assert (self.length == len(self.data['rhythm']) == len(self.data['DP']) == len(self.data['voicings']))

		# choices: possible routes recovered from last chord. Cost <= max(99, 1.5*bestCost)
		self.data['solutions'] = [[] for _ in range(self.length)]
		for phr in range(self.length): # loop through every phrase
			final_chord_DP = self.data['DP'][phr][-1]
			finals = [(item[0], j) for j,item in enumerate(final_chord_DP)] #(cost, index), for alt-solution-search
			finals.sort() # sort by first item (cost)
			bestCost = finals[0][0]
			maxCost = max(99, 1.5*bestCost)

			# retrace all "valid" solutions
			for cost, op in finals: # op = "optimal" solution to trace backwards.
				if cost > maxCost:
					break # While loop breaking criteria. Precondition: sols is sorted.
				
				# retrace solution
				solution = []
				for ch in reversed(range(len(self.data['DP'][phr]))): # ch=chord number
					solution.append(Chord(self.data['voicings'][phr][ch][op]))
					op = self.data['DP'][phr][ch][op][1] # set op to op's backreference (to the last optimal element)
				solution.reverse()
				self.data['solutions'][phr].append((solution, cost))

	def generateSolution(self, choices):
		# Collapsed SATB score.

		instr = Piano()
		instr.instrumentName = ""

		voices = [Voice(instr) for _ in range(4)]
		current_key = None

		SA = Part([TrebleClef(), voices[0], voices[1]])
		TB = Part([BassClef(), voices[2], voices[3]])

		assert(len(choices) == self.length)
		# totalCost = 0

		for phr, choice in enumerate(choices): # choice = choice no# of solution, ch = chord no# of phrase
			# totalCost += self.data['solutions'][phr][choice][1]

			# remember, rm is wrapped.
			for ch, ((rm,), duration, voicing) in enumerate(zip(self.data['chords'][phr], self.data['rhythm'][phr], self.data['solutions'][phr][choice][0])):
				bass, tenor, alto, soprano = [
					Note(p, quarterLength=duration) for p in voicing.pitches
				]
				if ch == 0:
					if rm.key != current_key:
						bass.addLyric(rm.key.tonicPitchNameWithCase.replace('#','♯').replace('-','♭')+': '+rm.figure)
					if not current_key or rm.key not in {current_key, current_key.relative}:
						ks = KeySignature(rm.key.sharps)
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
		score = Score([SA, TB], self.timeSignature)
		score.insert(0, StaffGroup([SA, TB], symbol='brace', barTogether=True))

		return score

	def getSolutionInfo(self):
		return [[len(phrase_sol), [sol[1] for sol in phrase_sol]] for phrase_sol in self.data['solutions']]









# ----------- Extra Debugging Utilities -----------
def chordProgressionToText(cp):
	s = []
	s.append("+S+ +A+ +T+ +B+")
	for chord in cp:
		s.append("{} {} {} {}".format(chord[3].nameWithOctave, chord[2].nameWithOctave, chord[1].nameWithOctave, chord[0].nameWithOctave))
	return '\n'.join(s)


def textToChordProgression(txt):
	lines = txt.split('\n')
	if "+S+ +A+ +T+ +B+" in lines[0]:
		lines.pop(0)
	cp = [ Chord(line) for line in lines if len(line.split(" ")) == 4 ] # chord progression
	return cp


if __name__ == "__main__":
	# Unit Tests (temp)
	chsh = "D: I IV V V7 I!4\nE: I IV V V7 I!4"
	x = FourPartChords()
	y = FPChordsQuery(x, chsh, ts='4/4')


