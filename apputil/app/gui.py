import PySimpleGUI as sg
from collections import defaultdict
import shutil
# from pathlib import Path

from app.guiWindowManager import WindowManager, MultiPageWindow

from fourpart import FourPartChords
from fourpart.utils import FPChordsQuery
# from settings import default_config

do_nothing = lambda *args, **kwargs: None

# ----------- Thematic Stuff -----------

global_font_family = 'Avenir Next'
global_font_size = 14
sg.set_options(font=(global_font_family, global_font_size))

sg.set_options(use_custom_titlebar=True, alpha_channel=0.8) # breaks "Resizable," https://github.com/PySimpleGUI/PySimpleGUI/issues/5252
sg.set_options(icon='/Users/darren/github/bachtobaroque/algorithms/Static/favicon.png')
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

# ----------- Window Manager Setup -----------

WM = WindowManager(timeout=500)

# ----------- Windows and Layouts Setup -----------

DOM = {}

# ======= MAIN WINDOW =======

# === FourPartChord ===

fpchord_input = [
	[sg.Text("Formatting:", font=(global_font_family, 18)), sg.Text("[key]: [chord!duration...]")],
	[sg.Text("(use 0 for ø, and // for comments)")],
	[sg.Text("Formatting Help & Guidelines:", font=(global_font_family, 12)), sg.Button('ℹ️', key='-WINDOW-FORMATTING-HELP-FPCHORD-',font=(global_font_family, 12))],
	[sg.Text("Time Signature:"), sg.Input('4/4',key="-FPCHORD-TS-",size=(5, None))],
	[sg.Multiline("b-: i ii07 V42 V7 i!4", size=(40, 10), key="-FPCHORD-INPUT-", autoscroll=True)],
]

# FPCHORDcfg:abc_def is FPCHORD config (FourPartChord.config(abc_def))...

fpchord_output = [
	[sg.Text("Configurations:", font=(global_font_family, 18))],
	[sg.CB("Search Pruning",    key='FPCHORDcfg:dp_pruning',     default=True, enable_events=True)],
	[sg.CB("Prune First Chord", key='FPCHORDcfg:dp_prune_first', default=True, enable_events=True)],
	[sg.Text("Confidence Factor:"),  sg.Push(), sg.Input('1.2', key="FPCHORDcfg:dp_confidence",  size=(5,None),justification='right')],
	[sg.Text("Buffer:"),             sg.Push(), sg.Input('10',  key="FPCHORDcfg:dp_buffer",      size=(5,None),justification='right')],
	[sg.Text("First Chord Buffer:"), sg.Push(), sg.Input('5000',key="FPCHORDcfg:dp_first_buffer",size=(7,None),justification='right')],
	[sg.Text("Console Output/Logs:", font=(global_font_family, 15, 'bold'))],
	[sg.Multiline("", size=(40, 10), key="-FPCHORD-CONSOLE-", autoscroll=True, font=('IBM 3720', 8))],
	[sg.VPush()],
	[sg.Button('Run', key='-FPCHORD-RUN-'), sg.Button('Lock Input', key='dbg.lock'), sg.Button('Debug Input', key='dbg')],
]

def fpchord_run(mainWindow, event, values):
	global DOM
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

	# Task: create a new window and integrate with solution-picker in fourpart_utils.
	def _results(window, event, values):

		print(event)
		nonlocal img_path

		if isinstance(event, str) and event.startswith("SPIN:"):
			i = event.split(':')[1]
			if i.isdigit() and 1 <= int(i) <= query.length:
				i = int(i) # i is one-indexed
				choices[i-1] = values[event]-1
				window[f'-spin-{i}-text-'].update(value=f"Cost: {solution_info[i-1][1][choices[i-1]]} (Solution {choices[i-1]+1} of {solution_info[i-1][0]})")

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
				
	MultiPageWindow('View Results', names=['🎚 Adjust', '💾 Save/Export'], inner_func=_results, disabled_button_color=theme_darker_button, separator=True, finalize=True,
		layouts=[
			[ # State 1: tweak/adjust solution mode
				[sg.Col([
					[sg.Text("Adjust Result:", font=(global_font_family, 18))],
					*[[sg.Text(f"Phrase {i+1}:", font=(global_font_family, 12, 'bold')), sg.Spin([j+1 for j in range(solution_info[i][0])], initial_value=choices[i]+1, key=f'SPIN:{i+1}', enable_events=True), sg.Text(f"Cost: {solution_info[i][1][choices[i]]} (Solution {choices[i]+1} of {solution_info[i][0]})     ", key=f'-spin-{i+1}-text-', font=(global_font_family, 12))] for i in range(query.length)],
				],expand_y=True,scrollable=True,vertical_scroll_only=True), sg.VSeperator(), sg.Col([
					[sg.Button("Regenerate", key='-regenerate-solution-')],
					[sg.Image(source=img_path,key='-display-music-png-',pad=(5, 5),subsample=_subsample_ratio,tooltip="MusicXML Generated PNG Score Image",right_click_menu=['&Right', ['&Regenerate::musicxml_score_png', '&Save Image As...::musicxml_score_png']])],
					[sg.VPush()],
					[sg.Text("Midi Playback:", font=(global_font_family, 16))],
				],expand_y=True)]
			],
			[ # State 2: Midi player and export options

			],
		]
	).registerWith(WM, alias='solution-view')




# === FourPartFiguredBass ===

fpfigbass_input = [
    
]

fpfigbass_output = [
    
]

def fpfigbass_run(mainWindow, event, values):
	pass

# === FourPartChordMelody ===

fpmelody_input = [
    
]

fpmelody_output = [
    
]

def fpmelody_run(mainWindow, event, values):
	pass

# === Ancillary ===
_run_alg = {'-FPCHORD-RUN-': fpchord_run, '-FPFIGBASS-RUN-': fpfigbass_run, '-FPMELODY-RUN-': fpmelody_run}

# ======= MAIN LAYOUT =======

main_layouts = [
	[	# State 1 -- FP Chord
		[sg.Text('FourPart from Chords Generator')],
		[sg.HSeparator()],
		[sg.Column(fpchord_input),
		 sg.VSeperator(),
		 sg.Column(fpchord_output, expand_y=True),], # expand_y: https://github.com/PySimpleGUI/PySimpleGUI/issues/5648
	],
	[	# State 2 -- FP FigBass
		[sg.Text('FourPart from Figured Bass Generator')],
		[sg.Text("Formatting Help:", font=(global_font_family, 12)), sg.Button('ℹ️', key='-WINDOW-FORMATTING-HELP-FPFIGBASS-',font=(global_font_family, 12))],
		[sg.Input(key='-IN-')],
		[sg.Input(key='-IN2-')],
		[sg.Button('Run', key='-FPFIGBASS-RUN-')],
	],
	[	# State 3 -- FP Melody
		[sg.Text('FourPart from Chords and Melody Generator')],
		[sg.Text("Formatting Help:", font=(global_font_family, 12)), sg.Button('ℹ️', key='-WINDOW-FORMATTING-HELP-FPMELODY-',font=(global_font_family, 12))],
		*[[sg.CB(f'Checkbox {i}')] for i in range(5)],
		*[[sg.R(f'Radio {i}', 1)] for i in range(8)],
		[sg.Button('Run', key='-FPMELODY-RUN-')],
	],
]

# ======= FORMATTING =======
formatting_help = None
get_formatting_help = lambda _initialState: MultiPageWindow('Formatting Help & Guidelines', names=['Chords', 'Figured Bass', 'Melody'], disabled_button_color=theme_darker_button, finalize=True, initial_state=_initialState,
	layouts = [
		[
			[sg.Text('FourPart Chords - Formatting Help/Guidelines',font=(global_font_family, 22, 'bold'))],
			[sg.HSeparator()],
			[sg.Text("""Chord progressions are divided up into individual "Phrases," each taking up one line of input, which typically end in a cadence. Voice leading rules are not enforced between phrases.\n\nPlease use the following format for each phrase: begin by specifying a key, capital letters A-G indicate major and lowercase letters a-g indicate minor, and use '#' to indicate 'sharp,' and either 'b' or '-' to indicate flat. Then, add a ':' (colon), and then write out the chord progression using Roman Numeral Analysis format. Optionally specify the duration of the chord in Quarter Note Lengths by appending an '!' and then the duration as a integer or fraction. only use spaces to separate different chords.\n\nIndicate half-diminished seventh chords using either 0 or ø (ALT+o). Rewrite suspensions as separate chords. Use '//' for comments.\n\nExample:\nC: I!1/2 I6!1/2 IV V V7 vi!4\na: i!3/2 ii07!3/2 V7 VI!3 V65/III III!4""", size=(64,None))],
			[sg.Push(), sg.Button(pad('Exit'),key='Exit-1')],
		],
		[
			[sg.Text('FourPart Figured Bass - Formatting Help/Guidelines',font=(global_font_family, 22, 'bold'))],
			[sg.HSeparator()],
			[sg.Text("""Lorem Ipsum""", size=(64,None))],
			[sg.Push(), sg.Button(pad('Exit'),key='Exit-2')],
		],
		[
			[sg.Text('FourPart Melody - Formatting Help/Guidelines',font=(global_font_family, 22, 'bold'))],
			[sg.HSeparator()],
			[sg.Text("""Lorem Ipsum""", size=(64,None))],
			[sg.Push(), sg.Button(pad('Exit'),key='Exit-3')],
		],
	]
)
_window_formatting_help = ('-WINDOW-FORMATTING-HELP-FPCHORD-', '-WINDOW-FORMATTING-HELP-FPFIGBASS-', '-WINDOW-FORMATTING-HELP-FPMELODY-')

# ----------- Main Window Logic & Program Start -----------

def main_window_process(window, event, values):

	print(event)

	if event in _window_formatting_help:
		global formatting_help
		_state = _window_formatting_help.index(event) + 1
		if WM.check_alias('fp_formatting_help'):
			formatting_help.queueStateChange(_state)
		else:
			formatting_help = get_formatting_help(_state).registerWith(WM, alias='fp_formatting_help')

	elif event in _run_alg.keys():
		_run_alg[event](window, event, values)

	# FP Chord Logic
	elif event == "FPCHORDcfg:dp_pruning":
		if values['FPCHORDcfg:dp_pruning']:
			for element in ('FPCHORDcfg:dp_prune_first', 'FPCHORDcfg:dp_confidence', 'FPCHORDcfg:dp_buffer'):
				window[element].update(disabled=False)
			if values['FPCHORDcfg:dp_prune_first']:
				window['FPCHORDcfg:dp_first_buffer'].update(disabled=False)
		else:
			for element in ('FPCHORDcfg:dp_prune_first', 'FPCHORDcfg:dp_confidence', 'FPCHORDcfg:dp_buffer', 'FPCHORDcfg:dp_first_buffer'):
				window[element].update(disabled=True)

	elif event == "FPCHORDcfg:dp_prune_first":
		if values['FPCHORDcfg:dp_prune_first']:
			for element in ('FPCHORDcfg:dp_first_buffer',):
				window[element].update(disabled=False)
		else:
			for element in ('FPCHORDcfg:dp_first_buffer',):
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

# ----------- Registration & Program Start -----------

# dummy icon window
def _setIcon(window):
	window.set_icon(pngbase64=app_window_icon)
	WM.queueUnregister('icon-setup') # quits immediately

WM.register('icon-setup', sg.Window('icon', [[]]), do_nothing, queue=_setIcon)

MultiPageWindow('4Part Algorithm Viewer', master=True, names=['Chords', 'Figured Bass', 'Melody'], layouts=main_layouts, inner_func=main_window_process, extra_buttons=[sg.Button('⚙️', key="-SETTINGS-")], disabled_button_color=theme_darker_button).registerWith(WM, alias='main')

if __name__ == "__main__":
	DOM['FP_CHORD_ENGINE'] = FourPartChords()

	WM.start()

