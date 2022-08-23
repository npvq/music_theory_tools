#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 #--------------#
# Author:  @npvq #
# Licence: GPLv3 #
 #--------------#

 #==================#
# WindowManager File #
 #==================#

# ----- SYSTEM IMPORTS ----- #



# ----- 3RD PARTY IMPORTS ----- #

import PySimpleGUI as sg

# ----- LOCAL IMPORTS ----- #



# ------------------------------ #

class WindowManager(object):
	"""\
	A GUI Window Manager that allows for simultaneous windows in PySimpleGUI.
	This abstraction greatly simplifies the coding process and allows for dynamic adjustment (register/unregister) of windows.

	Modifications to the dictionary that stores registered windows cannot have its length modified during runtime/event loop iteration.
	That means register() and unregister() cannot not be used after start(). Use queueRegister and queueUnregister instead.

	A WindowManager object could theoretically be reused, but note that all the sg.Window objects are single use only.
	You would need to use said WindowManager object with new sg.Window(s).
	"""

	def __init__(self, timeout=100):
		self.windows = {}
		self.timeout = timeout

		self.running = False

		self._register_queue = [] # list of alias names
		self._unregister_queue = [] # list of alias names

	def register(self, alias, window, func, queue=None, disabled=False):
		"""
		alias:    'key' of window, for external/absolute access.
		window:   sg.Window() object
		func:     function for processing events
		queue:    function for processing internal queues (optional)
				  will be called when window gets "__TIMEOUT__" AND is not currently disabled.
		disabled: bool -- disables window from event/interactions
		"""

		if alias in self.windows.keys():
			raise IndexError("Window Alias clash: Alias values should be unique.")
		self.windows[alias] = {'window': window, 'func': func, 'disabled': disabled, 'queue': queue}
		print("registered", alias)

	def unregister(self, alias):
		_obj = self.windows.pop(alias, None)
		if _obj:
			_obj['window'].close()

	def queueRegister(self, alias, window, func, queue=None, disabled=False):
		"""\
		Function to register a window while the event loop is running,
		will unregister the function upon finishing the current iteration of the event loop.
		This prevents RuntimeError from changing dict size during iteration.
		"""
		self._register_queue.append((alias, (window, func, queue, disabled)))

	def queueUnregister(self, alias):
		"""\
		Function to unregister a window while the event loop is running,
		will unregister the function upon finishing the current iteration of the event loop.
		This prevents RuntimeError from changing dict size during iteration.
		"""
		self._unregister_queue.append(alias)

	def quit_all(self):
		for obj in self.windows.values():
			obj['window'].close()
		self.windows.clear()

	def check_alias(self, alias):
		return alias in self.windows.keys()

	def start(self):

		self.running = True

		# ----------- Main Event Loop -----------
		while self.windows:
			# ----------- Resolving Queues (Window Addition/Deletions) -----------
			if self._unregister_queue:
				for alias in self._unregister_queue:
					self.unregister(alias)
				self._unregister_queue.clear()
			if self._register_queue:
				for alias, (window, func, queue, disabled) in self._register_queue:
					self.register(alias, window, func, queue=queue, disabled=disabled)
				self._register_queue.clear()

			# ----------- Subloop Through Each Substituent Window -----------
			for alias, obj in self.windows.items():
				event, values = obj['window'].read(timeout=self.timeout)

				if event == "__TIMEOUT__":
					if (not obj['disabled']) and obj['queue']:
						# process/resolve internal queues.
						obj['queue'](obj['window'])
					continue
				
				if event == "WINDOW_MANAGER_EXIT_ALL":
					confirm = sg.popup_ok_cancel("Are you sure?",title='Exit All Windows',keep_on_top=True,modal=True,)#no_titlebar=True)
					if confirm != 'Cancel':
						self.quit_all()
						break
					continue

				if event == sg.WIN_CLOSED or event.startswith('Exit'): # 'Exit', 'Exit-2', 'Exit-alt' will all work.
					self.queueUnregister(alias)
					continue

				if obj['disabled']:
					continue

				obj['func'](obj['window'], event, values)
		# ----------- End of Main Event Loop -----------

		self.running = False



