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
Shows interactive result window for FPChords computation.
"""

# ----- SYSTEM IMPORTS ----- #

import gc # garbage collection

# ----- 3RD PARTY IMPORTS ----- #

import PySimpleGUI as sg
import shutil

# ----- LOCAL IMPORTS ----- #

import app
from fourpart.fpchords import FourPartChords
from fourpart.utils import FPChordsQuery

# ------------------------------ #


# NO! This is a mess
# Implement a file caching system. 
# make sure it works with py2app
#TODO:!
CACHE = {
    'phrase': {
        'score': {},
        'midi': {},
        'png': {},
    },
    'solution': {
        'score': {},
        'midi': {},
        'png': {},
    },
}

def resetCache():
    global CACHE
    del CACHE
    gc.collect()
    CACHE = {
        'phrase': {
            'score': {},
            'midi': {},
            'png': {},
        },
        'solution': {
            'score': {},
            'midi': {},
            'png': {},
        },
    }



getLayout = lambda choices, solution_info, length: [
    [ # State 1: tweak/adjust solution mode
        [
            sg.Col([
                [sg.Text("Adjust Result:", font=(app.global_font_family, 18))],
                *[[
                    sg.Text(f"Phrase {i+1}:", font=(app.global_font_family, 12, 'bold')),
                    sg.Spin([j+1 for j in range(solution_info[i][0])], initial_value=choices[i]+1, key=f'choice:{i+1}', enable_events=True),
                    sg.Text(f"Cost: {solution_info[i][1][choices[i]]} (Solution {choices[i]+1} of {solution_info[i][0]})     ", key=f'choicetext:{i+1}', font=(app.global_font_family, 12))]
                for i in range(length)],
            ],expand_y=True,scrollable=True,vertical_scroll_only=True),
            sg.VSeperator(),
            sg.Col([
                [sg.Button("Regenerate", key='-regenerate-solution-')],
                [
                    sg.Image(source=img_path,key='-display-music-png-',pad=(5, 5),subsample=_subsample_ratio,tooltip="MusicXML Generated PNG Score Image",
                             right_click_menu=['&Right', ['&Regenerate::musicxml_score_png', '&Save Image As...::musicxml_score_png']]
                )],
                [sg.VPush()],
                [sg.Text("Midi Playback:", font=(app.global_font_family, 16))],
            ],expand_y=True)
        ]
    ],
    [ # State 2: Midi player and export options

    ],
]

# Task: create a new window and integrate with solution-picker in fourpart_utils.
def _results(window, event, values):

    print(event)
    nonlocal img_path

    if isinstance(event, str) and event.startswith("choice:"):
        i = event.split(':')[1]
        if i.isdigit() and 1 <= int(i) <= query.length:
            i = int(i) # i is one-indexed
            choices[i-1] = values[event]-1
            window[f'choicetext:'].update(value=f"Cost: {solution_info[i-1][1][choices[i-1]]} (Solution {choices[i-1]+1} of {solution_info[i-1][0]})")

    elif event == "-regenerate-solution-" or event == "Regenerate::musicxml_score_png":
        # fp=None results in termporary file.
        img_path = str(query.generateSolution(choices).write(fmt='musicxml.png', fp=None))
        window['-display-music-png-'].update(source=str(img_path), subsample=_subsample_ratio)

    elif event == "Save Image As...::musicxml_score_png":
        filename = sg.popup_get_file('Choose file (PNG) to save to', save_as=True)
        print(filename)
        if filename:
            try:
                shutil.copyfile(img_path, filename)
            except Exception as e:
                print(e)
                # ignore exceptions


def fpchord_run(mainWindow, event, values):
    mainWindow['-FPCHORD-RUN-'].update(text="Rerun")

    # config
    temp_config = {}
    for k,v in values.items():
        if isinstance(k, str) and k.startswith("FPCHORDcfg:"):
            #TODO: not a sustainable setup if expanded!
            temp_config[k.split(':')[1]] = v if isinstance(v, bool) else float(v)

    print("temp.......",temp_config)
    DOM['FP_CHORD_ENGINE'].configure(**temp_config)

    query = FPChordsQuery(DOM['FP_CHORD_ENGINE'], values["-FPCHORD-INPUT-"], ts=values["-FPCHORD-TS-"], consoleOutput=mainWindow['-FPCHORD-CONSOLE-'].print)
    choices = [0 for _ in range(query.length)]
    solution_info = query.getSolutionInfo()

    img_path = str(query.generateSolution(choices).write(fmt='musicxml.png', fp=None))
    _subsample_ratio = 3
                
    MultiPageWindow('View Results', names=['🎚 Adjust', '💾 Save/Export'], inner_func=_results, disabled_button_color=theme_darker_button, separator=True, finalize=True,).registerWith(WM, alias='solution-view')

