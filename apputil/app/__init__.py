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
Logic to run the app. Exports runApp to the application script.
"""

# ----- SYSTEM IMPORTS ----- #



# ----- 3RD PARTY IMPORTS ----- #

import PySimpleGUI as sg

# ----- LOCAL IMPORTS ----- #

from app.guiWindowManager import WindowManager

# ------------------------------ #


do_nothing = lambda *args, **kwargs: None

# ========== Thematic Stuff ==========

global_font_family = 'Avenir Next'
global_font_size = 14
sg.set_options(font=(global_font_family, global_font_size))

sg.set_options(use_custom_titlebar=True, alpha_channel=0.8) # breaks "Resizable," https://github.com/PySimpleGUI/PySimpleGUI/issues/5252
# sg.set_options(icon='/Users/darren/github/bachtobaroque/algorithms/Static/favicon.png')
sg.set_options(suppress_raise_key_errors=False, suppress_error_popups=True, suppress_key_guessing=True)

# good themes: LightBlue and LightGrey2
sg.theme('LightGrey2') # https://www.pysimplegui.org/en/latest/#themes-automatic-coloring-of-your-windows

app_window_icon = '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'

_theme_button_color = sg.theme_button_color_background() # "#5079D3"
_theme_button_color_darker = '#283d6a'

og_button = sg.theme_button_color()
theme_darker_button = ('white', _theme_button_color_darker)
mouseover_button_color = ('black', 'white')

def pad(s, width=1):
	return " "*width+s+" "*width

# ========== Main Logic ==========

def runApp():
	pass
