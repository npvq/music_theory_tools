import PySimpleGUI as sg
from collections import defaultdict

from fourpart import FourPartChords
from fourpart_utils import FPChordsQuery
from settings import default_config

DOM = defaultdict(None)
def DOM_init():
    DOM['FP_CHORD_ENGINE'] = FourPartChords()

global_font_family = 'Avenir Next'
global_font_size = 14
sg.set_options(font=(global_font_family, global_font_size))

sg.set_options(suppress_raise_key_errors=False, suppress_error_popups=True, suppress_key_guessing=True)

sg.theme('LightBlue') # https://www.pysimplegui.org/en/latest/#themes-automatic-coloring-of-your-windows

_theme_button_color = '#4f79d3'
_theme_button_color_darker = '#283d6a'

og_button_color = ('white', _theme_button_color)
disabled_button_color = ('white', _theme_button_color_darker)
mouseover_button_color = ('black', 'white')

def pad(s, width=1):
    return " "*width+s+" "*width

# ----------- Layouts -----------

# auxillary windows to pop up and display information
# not much logic, non-modal as well.
info_helper_windows = {}
def open_info_window(ctx):
    layout = [
        [sg.Text(ctx.get('title', 'Info:'),font=(global_font_family, 22, 'bold'))],
        [sg.HSeparator()],
        [sg.Text(ctx.get('message', '[NULL]'),size=(60,None))],
        [sg.Push(), sg.Button(pad(ctx.get('button', 'Exit')),key='Exit')]
    ]
    window = sg.Window("Information", layout, modal=False)
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

    window.close()

action_functions = {}

# Settings Window

def settingsWindow(event, values, mainWindow):
    pass

action_functions['-SETTINGS-'] = settingsWindow

# FourPartChord ================================================

fpchord_formatting = """[key]: [chord!duration...]\n(use 0 for ø, and // for comments)"""

info_helper_windows['-WINDOW-FPCHORD-FORMATTING-HELP-'] = {'title': "4P-Chords Formatting Help", 
'message': """Chord progressions are divided up into individual "Phrases," each taking up one line of input, which typically end in a cadence. Voice leading rules are not enforced between phrases.
\nPlease use the following format for each phrase: begin by specifying a key, capital letters A-G indicate major and lowercase letters a-g indicate minor, and use '#' to indicate 'sharp,' and either 'b' or '-' to indicate flat. Then, add a ':' (colon), and then write out the chord progression using Roman Numeral Analysis format. Optionally specify the duration of the chord in Quarter Note Lengths by appending an '!' and then the duration as a integer or fraction. only use spaces to separate different chords.
\nIndicate half-diminished seventh chords using either 0 or ø (ALT+o). Rewrite suspensions as separate chords. Use '//' for comments.
\nExample:\nC: I!1/2 I6!1/2 IV V V7 vi!4\na: i!3/2 ii07!3/2 V7 VI!3 V65/III III!4"""}

fpchord_input = [
    [sg.Text("Formatting:", font=(global_font_family, 18))],
    [sg.Text(fpchord_formatting, size=(40,None))],
    [sg.Text("Formatting Help:", font=(global_font_family, 12)), sg.Button('ℹ️', key='-WINDOW-FPCHORD-FORMATTING-HELP-',font=(global_font_family, 12))],
    [sg.Text("Time Signature:"), sg.Input('4/4',key="-FPCHORD-TS-",size=(5, None))],
    [sg.Multiline("b-: i ii07 V42 V7 i!4", size=(40, 10), key="-FPCHORD-INPUT-", autoscroll=True)],
]

fpchord_output = [
    [sg.Button('Run', key='-FPCHORD-RUN-')]
]

def fpchord_run(event, values, mainWindow):
    mainWindow['-FPCHORD-RUN-'].update(text="Rerun")
    DOM['FP_CHORD_QUERY'] = FPChordsQuery(DOM['FP_CHORD_ENGINE'], values["-FPCHORD-INPUT-"], ts=values["-FPCHORD-TS-"])
    DOM['FP_CHORD_QUERY_CHOICES'] = [0 for _ in DOM['FP_CHORD_QUERY'].length]

action_functions['-FPCHORD-RUN-'] = fpchord_run

layout1 = [
    [sg.Text('FourPart from Chords Generator')],
    [sg.HSeparator()],
    [sg.Column(fpchord_input),
     sg.VSeperator(),
     sg.Column(fpchord_output),],
]

# FourPartFiguredBass ==========================================

fpfigbass_input = [
    '1'
]

fpfigbass_output = [
    '1'
]

layout2 = [
    [sg.Text('FourPart from Figured Bass Generator')],
    [sg.Input(key='-IN-')],
    [sg.Input(key='-IN2-')]
]

# FourPartChordMelody ==========================================

fpmelody_input = [
    '1'
]

fpmelody_output = [
    '1'
]

layout3 = [
    [sg.Text('FourPart from Chords and Melody Generator')],
    *[[sg.CB(f'Checkbox {i}')] for i in range(5)],
    *[[sg.R(f'Radio {i}', 1)] for i in range(8)]
]



# ----------- Master Layout
layout = [
    [
        sg.Button('🔁', key='-VIEWCYCLE-'), 
        sg.Button('Chords', key='-VIEW1-', disabled_button_color=disabled_button_color, disabled=True), # button_color=og_button_color not necessary?
        sg.Button('Figured Bass', key='-VIEW2-', disabled_button_color=disabled_button_color),
        sg.Button('Melody', key='-VIEW3-', disabled_button_color=disabled_button_color), 
        sg.Button('⚙️', key="-SETTINGS-"),
        sg.Button('❌', key="Exit"),
    ],
    [sg.Column(layout1, key='-COL1-'), sg.Column(layout2, visible=False, key='-COL2-'), sg.Column(layout3, visible=False, key='-COL3-')],
]

view_buttons = ['-VIEW1-', '-VIEW2-', '-VIEW3-']

def main():
    DOM_init()

    window = sg.Window('4Part Algorithm Viewer', layout)
    state = 1  # The currently visible layout/state

    while True:
        event, values = window.read()
        print(event, values)
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        
        # 🔁
        elif event == '-VIEWCYCLE-':
            window[f'-COL{state}-'].update(visible=False)
            window[f'-VIEW{state}-'].update(disabled=False)
            state = ((state) % 3) + 1
            window[f'-COL{state}-'].update(visible=True)
            window[f'-VIEW{state}-'].update(disabled=True)
        
        # change state
        elif event in view_buttons:
            window[f'-COL{state}-'].update(visible=False)
            window[f'-VIEW{state}-'].update(disabled=False)
            state = view_buttons.index(event)+1
            window[f'-COL{state}-'].update(visible=True)
            window[f'-VIEW{state}-'].update(disabled=True)

        # Info Windows
        elif event in info_helper_windows.keys():
            open_info_window(info_helper_windows[event])

        # Action Buttons (connect to a function)
        elif event in action_functions.keys():
            action_functions[event](event, values, window)

    window.close()

# Event Loop to process "events" and get the "values" of the inputs
# while True:
#     event, values = window.read()
#     if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
#         break
#     print('You entered ', values[0])

if __name__ == "__main__":
    main()

