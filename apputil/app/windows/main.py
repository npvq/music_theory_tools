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
Main window for the GUI App
"""

# ----- SYSTEM IMPORTS ----- #



# ----- 3RD PARTY IMPORTS ----- #

import PySimpleGUI as sg

# ----- LOCAL IMPORTS ----- #

import app
from app.templates import MultiPageWindow
from app.windows import format_help

# ------------------------------ #

examples = [
    "b-: i ii07 I64 V7 i!4",
    "b-: B-2 C3(7) F3(6,4) F3(7) B-2!4",
    "b-: i ii07 V42 V7 i!4",
]

fpchord_left = lambda : [
    [sg.Text("Formatting:", font=(app.global_font_family, 18))],
    [sg.Text("[key]: [chord]![duration] (use 0 for ø, and // for comments)", font=(app.global_font_family, 12))],
    [sg.Text("Formatting Help & Guidelines:", font=(app.global_font_family, 12)), sg.Button('ℹ️', key='window:format_help:1',font=(app.global_font_family, 12))],
    [sg.VPush()],
    [sg.Text("Time Signature:"), sg.Input('4/4', key="fpchords:input:ts", size=(5, None), font=(app.mono_font_family))],
    [sg.Multiline(examples[0], key="fpchords:input:cp", size=(40, 10), font=(app.mono_font_family), autoscroll=True)],
]

fpchord_right = lambda : [
    [sg.Text("Configurations:", font=(app.global_font_family, 18))],
    # FPCHORDcfg:abc_def is FPCHORD config (FourPartChord.config(abc_def))...
    [sg.CB("Search Pruning",    key='fpchords:cfg:dp_pruning',     default=True, enable_events=True)],
    [sg.CB("Prune First Chord", key='fpchords:cfg:dp_prune_first', default=True, enable_events=True)],
    [sg.Text("Confidence Factor:"),  sg.Push(), sg.Input('1.2', key="fpchords:cfg:dp_confidence",  size=(5,None),justification='right')],
    [sg.Text("Buffer:"),             sg.Push(), sg.Input('10',  key="fpchords:cfg:dp_buffer",      size=(5,None),justification='right')],
    [sg.Text("First Chord Buffer:"), sg.Push(), sg.Input('5000',key="fpchords:cfg:dp_first_buffer",size=(7,None),justification='right')],
    [sg.Text("Console Output/Logs:", font=(app.global_font_family, 15, 'bold'))],
    [sg.Multiline("", size=(56, 10), key="fpchords:console", autoscroll=True, font=(app.mono_font_family, 8))],
    [sg.VPush()],
    [sg.Button('Run', key='run:fpchords'), sg.Button('Lock Input', key='dbg.lock'), sg.Button('Debug Input', key='dbg')],
]

fpfigbass_left = lambda : [
    [sg.Text("Formatting:", font=(app.global_font_family, 18))],
    [sg.Text("[key]: [pitch]([figures,])![duration]\n(use #/+ for raised figures, - or b for lowered figures,\nand // for comments)", font=(app.global_font_family, 12))],
    [sg.Text("Formatting Help:", font=(app.global_font_family, 12)), sg.Button('ℹ️', key='window:format_help:2',font=(app.global_font_family, 12))],
    [sg.Text("Time Signature:"), sg.Input('4/4', key="fpfigbass:input:ts", size=(5, None), font=(app.mono_font_family))],
    [sg.Multiline(examples[1], key="fpfigbass:input:?", size=(40, 10), font=(app.mono_font_family), autoscroll=True)],
]

fpfigbass_right = lambda : [
    [sg.Button('Run', key='run:fpfigbass')],
]

fpmelody_left = lambda : [
    [sg.Text("Formatting Help:", font=(app.global_font_family, 12)), sg.Button('ℹ️', key='window:format_help:3',font=(app.global_font_family, 12))],
    [sg.Text("Time Signature:"), sg.Input('4/4',key="fpmelody:input:ts",size=(5, None), font=(app.mono_font_family))],
    [sg.Multiline(examples[2], key="fpmelody:input:?", size=(40, 10), font=(app.mono_font_family), autoscroll=True)],
]

fpmelody_right = lambda : [
    [sg.Button('Run', key='run:fpmelody')],
    *[[sg.CB(f'Checkbox {i}')] for i in range(5)],
    *[[sg.R(f'Radio {i}', 1)] for i in range(8)],
]

# expand_y: https://github.com/PySimpleGUI/PySimpleGUI/issues/5648

getLayouts = lambda : [
    [   # State 1 -- FP Chord
        [sg.Text('FourPart from Chords Generator')],
        [sg.HSeparator()],
        [
            sg.Column(fpchord_left(), expand_y=True),
            sg.VSeperator(),
            sg.Column(fpchord_right(), expand_y=True),
        ],
    ],
    [   # State 2 -- FP FigBass
        [sg.Text('FourPart from Figured Bass Generator')],
        [sg.HSeparator()],
        [
            sg.Column(fpfigbass_left(), expand_y=True),
            sg.VSeperator(),
            sg.Column(fpfigbass_right(), expand_y=True),
        ],
    ],
    [   # State 3 -- FP Melody
        [sg.Text('FourPart from Melody Generator')],
        [sg.HSeparator()],
        [
            sg.Column(fpmelody_left(), expand_y=True),
            sg.VSeperator(),
            sg.Column(fpmelody_right(), expand_y=True),
        ],
    ],
]




# helper
_window_formatting_help = ('-WINDOW-FORMATTING-HELP-FPCHORD-', '-WINDOW-FORMATTING-HELP-FPFIGBASS-', '-WINDOW-FORMATTING-HELP-FPMELODY-')

# global variables
formatHelpWindow = None # stores reference to format_help's MultiPageWindow object.

def func(WM, window, event, values):

    print(event)

    if event.startswith('window:format_help:'):
        global formatHelpWindow
        _state = int(event.split(':')[2])
        if WM.check_alias('fp_formatting_help'):
            formatHelpWindow.queueStateChange(_state)
        else:
            formatHelpWindow = format_help.registerSelf(WM, alias='fp_formatting_help', initial_state=_state)

    # runs
    elif event.startswith('run:'):
        # check if already running a results window (hypothetical)
        if 'show-results' in WM.windows.keys():
            sg.popup_error("A result window is already open. Please close it before opening another one.")
        else:
            pass
            # run the window

    # FP Chord Logic
    elif event == "fpchords:cfg:dp_pruning":
        if values['fpchords:cfg:dp_pruning']:
            for element in ('fpchords:cfg:dp_prune_first', 'fpchords:cfg:dp_confidence', 'fpchords:cfg:dp_buffer'):
                window[element].update(disabled=False)
            if values['fpchords:cfg:dp_prune_first']:
                window['fpchords:cfg:dp_first_buffer'].update(disabled=False)
        else:
            for element in ('fpchords:cfg:dp_prune_first', 'fpchords:cfg:dp_confidence', 'fpchords:cfg:dp_buffer', 'fpchords:cfg:dp_first_buffer'):
                window[element].update(disabled=True)

    elif event == "fpchords:cfg:dp_prune_first":
        if values['fpchords:cfg:dp_prune_first']:
            for element in ('fpchords:cfg:dp_first_buffer',):
                window[element].update(disabled=False)
        else:
            for element in ('fpchords:cfg:dp_first_buffer',):
                window[element].update(disabled=True)

    # DEBUGGING
    # https://github.com/PySimpleGUI/PySimpleGUI/issues/5483
    elif event == 'dbg.lock':
        print('locking inputs...')
        window['-FPCHORD-INPUT-'].update(disabled=True)

    elif event == 'dbg':
        print('debugging inputs...')
        window['-FPCHORD-INPUT-'].update(disabled=False)
        window['dbg'].set_focus(force=True) # first move focus somewhere else
        #window['-FPCHORD-INPUT-'].set_focus(force=True) # is this needed?

# if alias is not set, MultiPageWindow will set it to MultiPageWindow.window_name automatically
def registerSelf(WM, alias=None, **kwargs):
    return MultiPageWindow('FourPart Algorithm Viewer', names=['Chords', 'Figured Bass', 'Melody'], layouts=getLayouts(), disabled_button_color=app.theme_darker_button, inner_func=func, master=True, **kwargs).registerWith(WM, alias=alias)
