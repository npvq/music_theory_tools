import PySimpleGUI as sg
from collections import defaultdict
import shutil
# from pathlib import Path

from app.windowmanager import WindowManager
from app.MultiPageWindow

from fourpart import FourPartChords
from fourpart.utils import FPChordsQuery
# from settings import default_config

# ----------- Window Manager Setup -----------

WM = WindowManager(timeout=500)

# ----------- Windows and Layouts Setup -----------

DOM = {}

# ======= MAIN WINDOW =======

# === FourPartChord ===




# === Ancillary ===
_run_alg = {'-FPCHORD-RUN-': fpchord_run, '-FPFIGBASS-RUN-': fpfigbass_run, '-FPMELODY-RUN-': fpmelody_run}

# ======= MAIN LAYOUT =======

# ======= FORMATTING =======

_window_formatting_help = ('-WINDOW-FORMATTING-HELP-FPCHORD-', '-WINDOW-FORMATTING-HELP-FPFIGBASS-', '-WINDOW-FORMATTING-HELP-FPMELODY-')

# ----------- Main Window Logic & Program Start -----------


# ----------- Registration & Program Start -----------

MultiPageWindow('4Part Algorithm Viewer', master=True, names=['Chords', 'Figured Bass', 'Melody'], layouts=main_layouts, inner_func=main_window_process, extra_buttons=[sg.Button('⚙️', key="-SETTINGS-")], disabled_button_color=theme_darker_button).registerWith(WM, alias='main')

if __name__ == "__main__":
    DOM['FP_CHORD_ENGINE'] = FourPartChords()

    WM.start()

