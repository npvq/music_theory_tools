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

# === Ancillary ===
_run_alg = {'-FPCHORD-RUN-': fpchord_run, '-FPFIGBASS-RUN-': fpfigbass_run, '-FPMELODY-RUN-': fpmelody_run}

# ======= MAIN LAYOUT =======

# ======= FORMATTING =======
formatting_help = None

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

WM.register('icon-setup', sg.Window('icon', [[]], visible=False), do_nothing, queue=_setIcon)

MultiPageWindow('4Part Algorithm Viewer', master=True, names=['Chords', 'Figured Bass', 'Melody'], layouts=main_layouts, inner_func=main_window_process, extra_buttons=[sg.Button('⚙️', key="-SETTINGS-")], disabled_button_color=theme_darker_button).registerWith(WM, alias='main')

if __name__ == "__main__":
	DOM['FP_CHORD_ENGINE'] = FourPartChords()

	WM.start()

