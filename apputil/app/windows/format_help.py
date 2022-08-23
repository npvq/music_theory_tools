# For normal files:

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
Formatting Help/Guidelines screen.

"""

# ----- SYSTEM IMPORTS ----- #



# ----- 3RD PARTY IMPORTS ----- #

import PySimpleGUI as sg

# ----- LOCAL IMPORTS ----- #

import app
from app.templates import MultiPageWindow

# ------------------------------ #

help_fpchords = """\
Chord progressions are divided up into individual "Phrases," each taking up one line of input, which typically end in a cadence. Voice leading rules are not enforced between phrases.

Please use the following format for each phrase: begin by specifying a key, capital letters A-G indicate major and lowercase letters a-g indicate minor, and use '#' to indicate 'sharp,' and either 'b' or '-' to indicate flat. Then, add a ':' (colon), and then write out the chord progression using Roman Numeral Analysis format. Optionally specify the duration of the chord in Quarter Note Lengths by appending an '!' and then the duration as a integer or fraction. only use spaces to separate different chords.

Indicate half-diminished seventh chords using either 0 or ø (ALT+o). Rewrite suspensions as separate chords. Use '//' for comments.

Example:\
"""

help_fpfigbass = """\
Figured bass works much like chord progressions, except the bass is now given, thus making it a restricted version of the FourPart Chords problem.

Likewise, for input, simply specify the pitch of each bassnote (like c#3 or C#3, and use - for flats e.g. B-2), and optionally add chord figures in parentheses, comma separated, before using the same '!' notation for rhythm.

In the figures, you can use # or + for sharps (raised) and - for flats (lowered). An accidental symbol alone always modifies the third of the chord.

Note that while you can use 'b' for flats in the key signature, you cannot use 'b' (yet) in the bassline pitch specification.

Example:\
"""

help_fpmelody1 = """\
A melody line is provided in addition to chords or figured bass, providing a further restriction to the FourPart problem. the pitch of the melody is added in square brackets '[]' after the chords/figured bass but before the duration/rhythmic information.

Notation for chords: add a '*' after a chord X or X7 if you want the algorithm to determine which inversion to use.
Example:\
"""
help_fpmelody2 = """\
Notation for figured bass: simply add the melody in '[]'. Unlike chords, the bassline here is predetermined.
Example:\
"""


getLayouts = lambda : [
    [
        [sg.Text('FourPart Chords - Formatting Help/Guidelines',font=(app.global_font_family, 22, 'bold'))],
        [sg.HSeparator()],
        [sg.Text(help_fpchords, size=(64,None))],
        [sg.Text("C: I!1/2 I6!1/2 IV V V7 vi!4\na: i!3/2 ii07!3/2 V7 VI!3 V65/III III!4", font=(app.mono_font_family, 14), background_color=app._theme_button_color)],
        [sg.Push(), sg.Button(app.pad('Exit'),key='Exit-1')],
    ],
    [
        [sg.Text('FourPart Figured Bass - Formatting Help/Guidelines',font=(app.global_font_family, 22, 'bold'))],
        [sg.HSeparator()],
        [sg.Text(help_fpfigbass, size=(64,None))],
        [sg.Text("E: E3 F#3(6,5) G#3(6) A3(6) B3(6,4)!2 B3!2 E3!3 E3(-7) A2!4", font=(app.mono_font_family, 14), background_color=app._theme_button_color)],
        [sg.Push(), sg.Button(app.pad('Exit'),key='Exit-2')],
    ],
    [
        [sg.Text('FourPart Melody - Formatting Help/Guidelines',font=(app.global_font_family, 22, 'bold'))],
        [sg.HSeparator()],
        [sg.Text(help_fpmelody1, size=(64,None))],
        [sg.Text("B-: I[D5] V7*[C5] vi*[B-4] ii*[C5] I64[D5] V7[E-5] I[D5]!2", font=(app.mono_font_family, 14), background_color=app._theme_button_color)],
        [sg.Text(help_fpmelody2, size=(64,None))],
        [sg.Text("B-: B-2[D5] F3(7)[C5] G3[B-4] E-3(6)[C5] F3(6,4)[D5] F3(7)[E-5] B-2[D5]", font=(app.mono_font_family, 14), background_color=app._theme_button_color)],
        [sg.Push(), sg.Button(app.pad('Exit'),key='Exit-3')],
    ],
]

# if alias is not set, MultiPageWindow will set it to MultiPageWindow.window_name automatically
def registerSelf(WM, alias=None, **kwargs):
    return MultiPageWindow('FourPart Formatting Help & Guidelines', names=['Chords', 'Figured Bass', 'Melody'], layouts=getLayouts(), disabled_button_color=app.theme_darker_button, **kwargs).registerWith(WM, alias=alias)
