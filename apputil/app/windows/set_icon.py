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
A temp window to set the icon and then close itself.
"""

# ----- SYSTEM IMPORTS ----- #



# ----- 3RD PARTY IMPORTS ----- #

import PySimpleGUI as sg

# ----- LOCAL IMPORTS ----- #

import app

# ------------------------------ #

def queue(WM, window):
    window.set_icon(pngbase64=app.icon)
    WM.queueUnregister('icon-setup') # quits immediately

def registerSelf(WM): # no options here!
    WM.register('icon-setup', sg.Window('icon', [[]], alpha_channel=0), app.do_nothing, queue=queue)

