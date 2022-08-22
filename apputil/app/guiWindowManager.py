import PySimpleGUI as sg

do_nothing = lambda *args, **kwargs: None

class WindowManager(object):

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

	def queueUnregister(self, alias):
		self._unregister_queue.append(alias)

	def queueRegister(self, alias, window, func, queue=None, disabled=False):
		self._register_queue.append((alias, (window, func, queue, disabled)))

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
					self.quit_all()
					break

				if event == sg.WIN_CLOSED or event.startswith('Exit'): # 'Exit', 'Exit-2', 'Exit-alt' will all work.
					self.queueUnregister(alias)

				if obj['disabled']:
					continue

				obj['func'](obj['window'], event, values)
		# ----------- End of Main Event Loop -----------

		self.running = False


class MultiPageWindow(object):

	def __init__(self, window_name, names=[], layouts=[], extra_buttons=[], inner_func=do_nothing, master=False, initial_state=1, separator=False, disabled_button_color=None, finalize=False):
		"""
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


	def func(self, window, event, values):

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
			self.inner_func(window, event, values)

	def processQueues(self, window):
		if self.stateQueue:
			assert((isinstance(self.stateQueue, int) or self.stateQueue.isdigit()) and 1 <= int(self.stateQueue) <= self.states)
			window[f'-COL{self.state}-'].update(visible=False)
			window[f'{self.state}'].update(disabled=False)
			self.state = int(self.stateQueue)
			window[f'-COL{self.state}-'].update(visible=True)
			window[f'{self.state}'].update(disabled=True)
			self.stateQueue = None

	def changeState(self, new_state):
		assert((isinstance(new_state, int) or new_state.isdigit()) and 1 <= int(new_state) <= self.states)
		self.window[f'-COL{self.state}-'].update(visible=False)
		self.window[f'{self.state}'].update(disabled=False)
		self.state = int(new_state)
		self.window[f'-COL{self.state}-'].update(visible=True)
		self.window[f'{self.state}'].update(disabled=True)

	def queueStateChange(self, new_state):
		self.stateQueue = new_state

	def registerWith(self, WM, alias=None, disabled=False):
		if not alias:
			alias = self.window_name

		if WM.running:
			WM.queueRegister(alias, self.window, self.func, disabled=disabled, queue=self.processQueues)
		else:
			WM.register(alias, self.window, self.func, disabled=disabled, queue=self.processQueues)
		return self



