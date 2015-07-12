import bge
from bge.logic import *
from bge.events import *
from mathutils import *
from math import *
import os, sys, time, threading

def read_config():
	## load global configuration file ##
	try: f = open(bge.logic.expandPath("//../config.txt"), 'r')
	except IOError:
		print('config.txt not found, use default values instead.')
		return {}
	else:
		lines = f.readlines()
		f.close()
		config = {}
		for line in lines:
			line = line.expandtabs()
			name = ""
			value = ""
			i = 0
			while line[i] != ' ':	i += 1
			name = line[:i]
			j = i
			while line[i] == ' ':	i += 1
			while line[j] != '\n':	j += 1
			value = line[i:j]
			config[name] = eval(value)
		return config

scene = bge.logic.getCurrentScene()
armature = scene.objects['armature']
cursor   = scene.objects['root_cursor']

connect_label_color = scene.objects['connect_label'].color

bge.render.showMouse(True)
setExitKey(0)

root_action_start = (25, 34)
root_action_loop = (34, 633)
title_start = (11, 35)
settings_action_start = (701, 736)
settings_action_loop = (736,736)
settings_action_stop = (736,758)
settings_holo_loop = (0,140)
connect_action_start = (879,889)
connect_action_loop = (889,889)


def goto_menu_root():
	armature.playAction('main', 
		root_action_start[0], 
		root_action_start[1], 
		layer=1, 
		play_mode=KX_ACTION_MODE_PLAY)
	armature.playAction('main', 
		root_action_loop[0], 
		root_action_loop[1], 
		layer=0, 
		play_mode=KX_ACTION_MODE_LOOP)
	armature.playAction('title', 
		title_start[0], 
		title_start[1], 
		layer=3, 
		play_mode=KX_ACTION_MODE_PLAY)	

def mouse_rotate_interface(cont):
	owner = cont.owner
	mouse = cont.sensors[0]
	x = mouse.position[0] / bge.render.getWindowWidth() - 0.5
	y = mouse.position[1] / bge.render.getWindowHeight() - 0.5
	
	armature.worldOrientation = Euler((-pi/12 * y, 0, -pi/12 * x))

def mouse_over_item(cont):
	mouseover = cont.sensors['Mouse']
	owner = cont.owner
	if mouseover.status == KX_SENSOR_JUST_ACTIVATED:
		cursor.localPosition.y = owner.localPosition.y

def start_game(blenderoptions='', gameoptions=''):
	print('platform detected:', sys.platform)
	config = read_config()
	width = 1280
	if 'window_width' in config:  width = config['window_width']
	height = 800
	if 'window_height' in config : height = config['window_height']
	if sys.platform in ('linux', 'linux2'):
		f = open(bge.logic.expandPath('//../blenderplayer_path.txt'), 'r')
		blenderplayer = f.read()[:-1] +'/blenderplayer'
		f.close()
		command = '%s -w %d %d %s  %s - %s -l %s' % (
			blenderplayer,
			width, height,
			blenderoptions, gameoptions,
			bge.logic.expandPath('//main.blend'),
			bge.logic.expandPath('//../backup-exemple.txt'),
		)
		print(command)
		os.system(command)
	elif sys.platform in ('win', 'win32', 'win64'):
		f = open(bge.logic.expandPath('//..\\blenderplayer_path.txt'), 'r')
		blenderplayer = f.read()[:-1] +'\\blenderplayer'
		f.close()
		command = '%s -w %d %d %s %s - %s -l %s' % (
			blenderplayer,
			width, height,
			blenderoptions, gameoptions,
			bge.logic.expandPath('//main.blend'),
			bge.logic.expandPath('//..\\backup-exemple.txt'),
		)
		print(command)
		os.system(command)
	else:
		print('Fatal error: unsupported platform.')

root_items = None
root_item_selected = 3

selected_root = 0
selected_net_address = 1
selected_net_port = 2
selected_properties = 3

def keyboard_item(cont):
	global root_items, root_item_selected
	keyboard = cont.sensors[0]
	owner = cont.owner
	
	if root_items == None:
		# sort items by position on Y
		root_items = []
		for child in armature.children:
			if child != owner and "root_item" in child and child["root_item"] :
				pos = child.localPosition.z
				place = False
				for i in range(len(root_items)):
					if pos < root_items[i].localPosition.z:
						root_items.insert(i, child)
						place = True
						break
				if not place:
					root_items.append(child)
	
	if owner['selection'] == selected_root:
		# up and down keys are used to select items
		if keyboard.getKeyStatus(UPARROWKEY) == KX_INPUT_JUST_ACTIVATED:
			if root_item_selected < len(root_items)-1:  root_item_selected += 1
		
		if keyboard.getKeyStatus(DOWNARROWKEY) == KX_INPUT_JUST_ACTIVATED:
			if root_item_selected > 0:  root_item_selected -= 1
		
		if keyboard.getKeyStatus(ENTERKEY) == KX_INPUT_JUST_ACTIVATED:
			name = root_items[root_item_selected].name
			if name == "enter_local_grid":
				start_game()
			elif name == "connect_to_server":
				frame = armature.getActionFrame(0)
				owner['selection'] = selected_net_address
				armature.playAction('main', 
					connect_action_start[0], 
					connect_action_start[1], 
					layer=1, 
					play_mode=KX_ACTION_MODE_PLAY)
				armature.playAction('main', 
					connect_action_loop[1], 
					connect_action_loop[1], 
					layer=0, 
					play_mode=KX_ACTION_MODE_LOOP)
				scene.objects['connect_label']['Text'] = "ENTER SERVER ADDRESS"
				scene.objects['connect_downloads'].visible = False
					
			elif name == "configure_settings":
				frame = armature.getActionFrame(0)
				if frame >= settings_action_loop[0] and frame <= settings_action_loop[1]:
					armature.playAction('main', 
						settings_action_stop[0], 
						settings_action_stop[1], 
						layer=1, 
						play_mode=KX_ACTION_MODE_PLAY)
					armature.playAction('main', 
						root_action_loop[0], 
						root_action_loop[1], 
						layer=0, 
						play_mode=KX_ACTION_MODE_LOOP)
					scene.objects['hologram triangle'].visible = False
				else:
					armature.playAction('main', 
						settings_action_start[0], 
						settings_action_start[1], 
						layer=1, 
						play_mode=KX_ACTION_MODE_PLAY)
					armature.playAction('main', 
						settings_action_loop[0],
						settings_action_loop[1],
						layer=0, 
						play_mode=KX_ACTION_MODE_LOOP)
					armature.playAction('holo',
						settings_holo_loop[0],
						settings_holo_loop[1],
						layer=4,
						play_mode=KX_ACTION_MODE_LOOP)
					scene.objects['hologram triangle'].visible = True
			elif name == "quit_tronr":
				bge.logic.endGame()
				
		if len(root_items):
			cursor.setParent(root_items[root_item_selected])
			cursor.localPosition = (
				0.65,
				0.06,
				0, #root_items[root_item_selected].localPosition.z
				)
			cursor.localOrientation = Euler((pi/2, 0., 0.))
		keyboard.reset()
	
	elif owner['selection'] == selected_net_address:
		if [ESCKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events:
			owner['selection'] = selected_root
			armature.playAction('main', 
				connect_action_start[1], 
				connect_action_start[0], 
				layer=1, 
				play_mode=KX_ACTION_MODE_PLAY)
			armature.playAction('main', 
				root_action_loop[0], 
				root_action_loop[1], 
				layer=0, 
				play_mode=KX_ACTION_MODE_LOOP)
		elif [ENTERKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events or [TABKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events:
			owner['selection'] = selected_net_port
		else:
			text_enter(keyboard, owner, scene.objects['label_net_address'])
	
	elif owner['selection'] == selected_net_port:
		if keyboard.getKeyStatus(ESCKEY) == KX_INPUT_JUST_ACTIVATED:
			owner['selection'] = selected_root
			armature.playAction('main', 
				connect_action_start[1], 
				connect_action_start[0], 
				layer=1, 
				play_mode=KX_ACTION_MODE_PLAY)
			armature.playAction('main', 
				root_action_loop[0], 
				root_action_loop[1], 
				layer=0, 
				play_mode=KX_ACTION_MODE_LOOP)
		elif [ENTERKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events:
			# launch game with network connexion
			label = scene.objects['connect_label']
			address = scene.objects['label_net_address']['Text']
			port = scene.objects['label_net_port']['Text']
			if not port.isnumeric():
				label['Text'] = 'bad port'
				label.color = (1, 0.2, 0.2, 1)
			else:
				label['Text'] = 'connect to server . . .'
				label.color = connect_label_color
				start_game(gameoptions = '-n %s %s' % (address, port))
		elif [TABKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events and ([LEFTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events or [RIGHTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events):
			owner['selection'] = selected_net_address
		elif [TABKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events:
			pass
		else:
			text_enter(keyboard, owner, scene.objects['label_net_port'])



def init(cont):
	goto_menu_root()
	

def text_enter(keyboard, cursor, entry):
	cursor.setParent(entry)
	cursor.localPosition = (entry['cursor']*0.5+0.4, 0, 0)    # for ubuntu condensed mono
	#cursor.localPosition = (entry['cursor']*0.6+0.5, 0, 0)   # for standard monopsaced font
	cursor.localOrientation = Euler((-pi/2, 0., 0.))
	# arrow keys to change cursor location
	if keyboard.getKeyStatus(LEFTARROWKEY) == KX_INPUT_JUST_ACTIVATED:
		if entry['cursor'] > 0: entry['cursor'] -= 1
	elif keyboard.getKeyStatus(RIGHTARROWKEY) == KX_INPUT_JUST_ACTIVATED:
		if entry['cursor'] < len(entry['Text']): entry['cursor'] += 1

	# caps key must be enabled in the program, if activated before, it will not take effect here.
	elif keyboard.getKeyStatus(CAPSLOCKKEY) == KX_INPUT_JUST_ACTIVATED:
		cursor['capslock'] = not cursor['capslock']

	# erase characters in edition mode
	elif keyboard.getKeyStatus(BACKSPACEKEY) == KX_INPUT_JUST_ACTIVATED:
		place = entry['cursor']-1
		if place >= 0:
			text = entry['Text']
			entry['Text'] = text[:place] + text[place+1:]
			entry['cursor'] = place

	# erase characters in suppression mode
	elif keyboard.getKeyStatus(DELKEY) == KX_INPUT_JUST_ACTIVATED:
		place = entry['cursor']
		text = entry['Text']
		entry['Text'] = text[:place] + text[place+1:]
		entry['cursor'] = place

	# for french keyboard, ';' is shifted by '.' to type IP address
	elif [135, KX_INPUT_JUST_ACTIVATED] in keyboard.events and ([RIGHTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events or [LEFTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events):
		place = entry['cursor']
		text = entry['Text']
		entry['Text'] = text[:place] + '.' + text[place:]
		entry['cursor'] += 1

	# else, type character, becarefull with unvisibe characters!
	elif keyboard.events[0][1] == KX_INPUT_JUST_ACTIVATED:
		shift = cursor['capslock']
		for event in keyboard.events:
			if event[0] == RIGHTSHIFTKEY or event[0] == LEFTSHIFTKEY: shift = not shift
		char = EventToCharacter(keyboard.events[0][0], shift)
		if char:
			place = entry['cursor']
			text = entry['Text']
			entry['Text'] = text[:place] + char + text[place:]
			entry['cursor'] += 1