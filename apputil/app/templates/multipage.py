#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 #--------------#
# Author:  @npvq #
# Licence: GPLv3 #
 #--------------#

 #====================#
# MultiPageWindow File #
 #====================#

# ----- SYSTEM IMPORTS ----- #



# ----- 3RD PARTY IMPORTS ----- #

import PySimpleGUI as sg

# ----- LOCAL IMPORTS ----- #

import app

# ------------------------------ #

class MultiPageWindow(object):
    """\
    A PySimpleGUI versatile multi-paged window implementation. Designed to plug nicely into WindowManager.
    """

    def __init__(self, window_name, names=[], layouts=[], extra_buttons=[], inner_func=app.do_nothing, master=False, initial_state=1, separator=False, disabled_button_color=None, finalize=False):
        """\
        layouts: layout list objects
        names: corresponds to layouts. If not provided, will simply use an integer.
        inner_function: logic after multipage/switcher processing
        master: bool -- is master window (if so, will close all other windows upon exiting this window.)

        extra_buttons: more buttons placed between default buttons: (Loop, layout buttons) [extra buttons here] (Exit button)
        separator: bool -- adds an hseparator between buttons and layout content
        disabled_button_color: color for button of current screen (which is disabled).

        finalize: bool -- adds a finalize parameter during window creation, see comment below at sg.Window(...)
        initial_state: states go from 1 to no# of pages. initial state allows the window to begin on a different state.
        """

        if not layouts:
            raise IndexError

        # master layout
        layout_buttons = [sg.Button('🔁', key='-VIEWCYCLE-')]
        layout_body = []

        self.state = initial_state
        self.states = len(layouts)

        for i,page in enumerate(layouts):
            try:
                _name = names[i]
            except IndexError:
                _name = i+1

            layout_buttons.append( sg.Button(_name, key=str(i+1), disabled_button_color=disabled_button_color, disabled=(self.state == i+1)) )
            layout_body.append( sg.Column(page, key=f'-COL{i+1}-', visible=(self.state == i+1)) )

        layout_buttons.extend(extra_buttons)
        layout_buttons.append( sg.Button('❌', key=("WINDOW_MANAGER_EXIT_ALL" if master else "Exit")) )

        self.layout = [layout_buttons]
        if separator:
            self.layout.append([sg.HSeparator()])
        self.layout.append(layout_body)

        self.window_name = window_name
        # finalize=True in case window needs updating before event loop gets to it.
        self.window = sg.Window(self.window_name, self.layout, finalize=finalize, resizable=True)

        self.inner_func = inner_func

        self.stateQueue = None


    def func(self, WM, window, event, values):

        # Exit button is managed by WindowManager

        # 🔁
        if event == '-VIEWCYCLE-':
            window[f'-COL{self.state}-'].update(visible=False)
            window[f'{self.state}'].update(disabled=False)
            self.state = (self.state % self.states) + 1
            window[f'-COL{self.state}-'].update(visible=True)
            window[f'{self.state}'].update(disabled=True)

        # change state
        elif event and event.isdigit() and 1 <= int(event) <= self.states:
            window[f'-COL{self.state}-'].update(visible=False)
            window[f'{self.state}'].update(disabled=False)
            self.state = int(event)
            window[f'-COL{self.state}-'].update(visible=True)
            window[f'{self.state}'].update(disabled=True)

        else:
            self.inner_func(WM, window, event, values)

    def setInnerFunc(self, inner_func):
        """\
        In case you want to overrwite the inner function given to a MultiPageWindow object by another program.
        """
        self.inner_func = inner_func

    def processQueues(self, WM, window):
        """\
        The queue function fed into window manager.
        The only thing to process is a change of state, i.e., if another window calls on this window to change the page it is on.
        """
        if self.stateQueue:
            assert((isinstance(self.stateQueue, int) or self.stateQueue.isdigit()) and 1 <= int(self.stateQueue) <= self.states)
            window[f'-COL{self.state}-'].update(visible=False)
            window[f'{self.state}'].update(disabled=False)
            self.state = int(self.stateQueue)
            window[f'-COL{self.state}-'].update(visible=True)
            window[f'{self.state}'].update(disabled=True)
            self.stateQueue = None

    def changeState(self, new_state):
        """\
        The backend way to change the current state (page) that the window is on.
        Note: code is not reused by processQueue.
        """
        assert((isinstance(new_state, int) or new_state.isdigit()) and 1 <= int(new_state) <= self.states)
        self.window[f'-COL{self.state}-'].update(visible=False)
        self.window[f'{self.state}'].update(disabled=False)
        self.state = int(new_state)
        self.window[f'-COL{self.state}-'].update(visible=True)
        self.window[f'{self.state}'].update(disabled=True)

    def queueStateChange(self, new_state):
        self.stateQueue = new_state

    def registerWith(self, WM, alias=None, disabled=False):
        """\
        Attaches to WindowManager object.
        Returns reference to self (helpful construct for chaining).
        """
        if not alias:
            alias = self.window_name

        if WM.running:
            WM.queueRegister(alias, self.window, self.func, disabled=disabled, queue=self.processQueues)
        else:
            WM.register(alias, self.window, self.func, disabled=disabled, queue=self.processQueues)
        return self # helpful construct for chaining.
