import bge
from bge.logic import *
from bge.events import *
from mathutils import *
import aud
from math import *
import os, sys, time, threading

# network module
sys.path.append(bge.logic.expandPath('//../scripts'))
sys.path.append(bge.logic.expandPath('//../network'))
import client

# setup global variables
scene = bge.logic.getCurrentScene()
armature = scene.objects['armature']
cursor   = scene.objects['root_cursor']
sound_path = expandPath('//../sounds')
audio = aud.device()

active_element = 'root'
root_items = None
root_item_selected = 3


connect_label_color = scene.objects['connect_label'].color.copy()

# setup the scene
bge.render.showMouse(True)
setExitKey(0)

# animations
root_action_start     = (25, 34)
root_action_loop      = (34, 633)
title_start           = (11, 35)
settings_action_start = (701, 736)
settings_action_loop  = (736, 736)
settings_action_stop  = (736, 758)
settings_holo_loop    = (0, 140)
connect_action_start  = (879, 889)
connect_action_loop   = (889, 889)
connect_to_server     = (889, 900)
connect_download      = (900, 906)


def read_config():
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

def start_game(blenderoptions='', gameoptions=''):
	print('platform detected:', sys.platform)
	config = read_config()
	width = 1280
	if 'window_width' in config:  width = config['window_width']
	height = 800
	if 'window_height' in config : height = config['window_height']
	if sys.platform in ('linux', 'linux2'):
		f = open(bge.logic.expandPath('//../blenderplayer_path.txt'), 'r')
		blenderplayer = f.readlines()[0].rstrip('\n') +'/blenderplayer'
		f.close()
		command = '%s -w %d %d %s %s - %s -l %s -p %d' % (
			blenderplayer,
			width, height,
			bge.logic.expandPath('//main.blend'),
			blenderoptions, gameoptions,
			bge.logic.expandPath('//../backup-exemple.txt'),
			os.getpid(),
		)
		print(command)
		error = os.system(command)
			
	elif sys.platform in ('win', 'win32', 'win64'):
		f = open(bge.logic.expandPath('//..\\blenderplayer_path.txt'), 'r')
		blenderplayer = f.readlines()[0].rstrip('\n') +'\\blenderplayer'
		f.close()
		command = '%s -w %d %d %s %s - %s -l %s -p %d' % (
			blenderplayer,
			width, height,
			bge.logic.expandPath('//main.blend'),
			blenderoptions, gameoptions,
			bge.logic.expandPath('//..\\backup-exemple.txt'),
			os.getpid(),
		)
		print(command)
		os.system(command)
	else:
		print('Fatal error: unsupported platform.')

def start_online():
	# change label
	label    = scene.objects['connect_label']
	label['Text'] = 'connect to server . . .'
	label.color = connect_label_color
	# animate label
	armature.playAction('main', 
		connect_to_server[0], 
		connect_to_server[1], 
		layer=1, 
		play_mode=KX_ACTION_MODE_PLAY)
	armature.playAction('main', 
		connect_to_server[1], 
		connect_to_server[1], 
		layer=0,
		play_mode=KX_ACTION_MODE_LOOP)
	# try to connect to server
	address  = scene.objects['net_address']['Text']
	port     = scene.objects['net_port']['Text']
	username = scene.objects['net_user']['Text']
	password = scene.objects['net_password']['Text']
	reponse = client.try_login((address, int(port)), username, password)
	if not reponse:
		start_game(gameoptions = "-n %s %s '%s' '%s'" % (address, port, username, password))
		armature.playAction('main', 
			connect_to_server[1], 
			connect_to_server[0], 
			layer=1, 
			play_mode=KX_ACTION_MODE_PLAY)
		armature.playAction('main', 
			connect_action_loop[1], 
			connect_action_loop[1], 
			layer=0, 
			play_mode=KX_ACTION_MODE_LOOP)
		label['Text'] = 'enter server address'
		label.color = connect_label_color
	else:
		armature.playAction('main', 
			connect_to_server[1], 
			connect_to_server[0], 
			layer=1, 
			play_mode=KX_ACTION_MODE_PLAY)
		armature.playAction('main', 
			connect_action_loop[1], 
			connect_action_loop[1], 
			layer=0, 
			play_mode=KX_ACTION_MODE_LOOP)
		label['Text'] = reponse
		label.color = Vector((1, 0.2, 0.2, 1))



def do_not(): # just called on every logic step to assure that the threads will be actualized by the BGE
	pass

def mouse_rotate_interface(cont):
	owner = cont.owner
	mouse = cont.sensors[0]
	x = mouse.position[0] / bge.render.getWindowWidth() - 0.5
	y = mouse.position[1] / bge.render.getWindowHeight() - 0.5
	
	armature.worldOrientation = Euler((-pi/12 * y, 0, -pi/12 * x))

def mouse_over_item(cont):
	global root_item_selected, root_items
	mouseover = cont.sensors['Mouse']
	owner = cont.owner
	if mouseover.status == KX_SENSOR_JUST_ACTIVATED:
		root_item_selected = root_items.index(owner)
		active_element = 'root'
		cursor.setParent(owner)
		cursor.localPosition = (0.65, -0.01, 0)
		cursor.localOrientation = Euler((-pi/2, 0., 0.))
		# play sound
		sound = aud.Factory(sound_path+'/share/interface-rollover.mp3')
		audio.volume = 0.1
		audio.play(sound)
	if mouseover.status in (KX_SENSOR_JUST_ACTIVATED, KX_SENSOR_ACTIVE) and mouseover.getButtonStatus(LEFTMOUSE) == KX_INPUT_JUST_ACTIVATED:
		root_select()

def mouse_over_entry(cont):
	global active_element
	mouseover = cont.sensors['Mouse']
	if mouseover.status in (KX_SENSOR_JUST_ACTIVATED, KX_SENSOR_ACTIVE):
		if cont.owner.parent: 
			entry = cont.owner.parent
			active_element = entry.name
			cursor.setParent(entry)
			cursor.localOrientation = Euler((-pi/2, 0., 0.))
			cursor.localPosition = (entry['cursor']*0.5+0.4, 0, 0)    # for ubuntu condensed mono
			#cursor.localPosition = (entry['cursor']*0.6+0.5, 0, 0)   # for standard monopsaced font
		# play sound
		sound = aud.Factory(sound_path+'/share/interface-rollover.mp3')
		audio.volume = 0.1
		audio.play(sound)

def mouse_over_root(cont):
	global active_element
	mouseover = cont.sensors['Mouse']
	if mouseover.status in (KX_SENSOR_JUST_ACTIVATED, KX_SENSOR_ACTIVE) and mouseover.getButtonStatus(LEFTMOUSE) == KX_INPUT_JUST_ACTIVATED:
		root_deselect()



def root_select():
	global root_items, root_item_selected, active_element
	if active_element == 'root':		
		name = root_items[root_item_selected].name
		if name == "enter_local_grid":
			start_game()
		
		elif name == "connect_to_server":
			frame = armature.getActionFrame(0)
			active_element = 'net_address'
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
		# play sound
		sound = aud.Factory(sound_path+'/share/menu-button.mp3')
		audio.volume = 0.3
		audio.play(sound)

def root_deselect():
	global root_items, root_item_selected, active_element
	if active_element != 'root':		
		active_element = 'root'
		name = root_items[root_item_selected].name
		if name == 'connect_to_server':
			active_element = 'root'
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
		if name == 'configure_settings':
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
			# play sound
			sound = aud.Factory(sound_path+'/share/menu-button.mp3')
			audio.volume = 0.3
			audio.play(sound)


def keyboard(cont):
	global root_items, root_item_selected, active_element
	keyboard = cont.sensors[0]
	owner = cont.owner
	
	if active_element == 'root':
		# play sound
		sound = aud.Factory(sound_path+'/share/interface-rollover.mp3')
		audio.volume = 0.1
		audio.play(sound)
		# up and down keys are used to select items
		if keyboard.getKeyStatus(UPARROWKEY) == KX_INPUT_JUST_ACTIVATED:
			if root_item_selected < len(root_items)-1:  root_item_selected += 1
		
		if keyboard.getKeyStatus(DOWNARROWKEY) == KX_INPUT_JUST_ACTIVATED:
			if root_item_selected > 0:  root_item_selected -= 1
		
		if keyboard.getKeyStatus(ENTERKEY) == KX_INPUT_JUST_ACTIVATED:
			root_select()
				
		if len(root_items):
			cursor.setParent(root_items[root_item_selected])
			cursor.localPosition = (0.65,  -0.01,  0)
			cursor.localOrientation = Euler((-pi/2, 0., 0.))
		keyboard.reset()
	
	elif active_element == 'net_address':
		if [ESCKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events:
			active_element = 'root'
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
			active_element = 'net_port'
		else:
			text_enter(keyboard, owner, scene.objects['net_address'])
	
	elif active_element == 'net_port':
		if keyboard.getKeyStatus(ESCKEY) == KX_INPUT_JUST_ACTIVATED:
			active_element = 'root'
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
		elif [TABKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events and ([LEFTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events or [RIGHTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events):
			active_element = 'net_address'
		elif [ENTERKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events or [TABKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events:
			active_element = 'net_user'
		else:
			text_enter(keyboard, owner, scene.objects['net_port'])

	elif active_element == 'net_user':
		if keyboard.getKeyStatus(ESCKEY) == KX_INPUT_JUST_ACTIVATED:
			active_element = 'root'
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
		elif [TABKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events and ([LEFTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events or [RIGHTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events):
			active_element = 'net_port'
		elif [ENTERKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events or  [TABKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events:
			active_element = 'net_password'
		else:
			text_enter(keyboard, owner, scene.objects['net_user'])

	elif active_element == 'net_password':
		if keyboard.getKeyStatus(ESCKEY) == KX_INPUT_JUST_ACTIVATED:
			active_element = 'root'
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
			t = threading.Thread()
			t.run = start_online
			t.start()
		elif [TABKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events and ([LEFTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events or [RIGHTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events):
			active_element = 'net_user'
		elif [TABKEY, KX_INPUT_JUST_ACTIVATED] in keyboard.events:
			pass
		else:
			text_enter(keyboard, owner, scene.objects['net_password'])


def init(cont):
	global root_items, root_item_selected
	if root_items == None:
		# sort items by position on Y
		root_items = []
		for child in armature.children:
			if child != cursor and "root_item" in child and child["root_item"] :
				pos = child.localPosition.z
				place = False
				for i in range(len(root_items)):
					if pos < root_items[i].localPosition.z:
						root_items.insert(i, child)
						place = True
						break
				if not place:
					root_items.append(child)
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
	
	# load config
	global config
	config = read_config()
	scene.objects['net_address']['Text']  = config['network_address']
	scene.objects['net_port']['Text']     = config['network_port']
	scene.objects['net_user']['Text']     = config['network_user']
	scene.objects['net_password']['Text'] = config['network_password']
	

def text_enter(keyboard, cursor, entry):
	play_sound = False
	# arrow keys to change cursor location
	if keyboard.getKeyStatus(LEFTARROWKEY) == KX_INPUT_JUST_ACTIVATED:
		if entry['cursor'] > 0: entry['cursor'] -= 1
		play_sound = True
	
	elif keyboard.getKeyStatus(RIGHTARROWKEY) == KX_INPUT_JUST_ACTIVATED:
		if entry['cursor'] < len(entry['Text']): entry['cursor'] += 1
		play_sound = True

	# caps key must be enabled in the program, if activated before, it will not take effect here.
	elif keyboard.getKeyStatus(CAPSLOCKKEY) == KX_INPUT_JUST_ACTIVATED:
		cursor['capslock'] = not cursor['capslock']

	# erase characters in edition mode
	elif keyboard.getKeyStatus(BACKSPACEKEY) == KX_INPUT_JUST_ACTIVATED:
		play_sound = True
		place = entry['cursor']-1
		if place >= 0:
			text = entry['Text']
			entry['Text'] = text[:place] + text[place+1:]
			entry['cursor'] = place

	# erase characters in suppression mode
	elif keyboard.getKeyStatus(DELKEY) == KX_INPUT_JUST_ACTIVATED:
		play_sound = True
		place = entry['cursor']
		text = entry['Text']
		entry['Text'] = text[:place] + text[place+1:]
		entry['cursor'] = place

	# for french keyboard, ';' is shifted by '.' to type IP address
	elif [135, KX_INPUT_JUST_ACTIVATED] in keyboard.events and ([RIGHTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events or [LEFTSHIFTKEY, KX_INPUT_ACTIVE] in keyboard.events):
		play_sound = True
		place = entry['cursor']
		text = entry['Text']
		entry['Text'] = text[:place] + '.' + text[place:]
		entry['cursor'] += 1

	else: # threat all characters
		shift = cursor['capslock']
		for event in keyboard.events:
			if event[0] == RIGHTSHIFTKEY or event[0] == LEFTSHIFTKEY: shift = not shift
		for event in keyboard.events:
			if event[1] == KX_INPUT_JUST_ACTIVATED:
				char = EventToCharacter(event[0], shift)
				if char:
					play_sound = True
					place = entry['cursor']
					text = entry['Text']
					entry['Text'] = text[:place] + char + text[place:]
					entry['cursor'] += 1

	if entry != cursor.parent:
		cursor.setParent(entry)
		cursor.localOrientation = Euler((-pi/2, 0., 0.))
	cursor.localPosition = (entry['cursor']*0.5+0.4, 0, 0)    # for ubuntu condensed mono
	#cursor.localPosition = (entry['cursor']*0.6+0.5, 0, 0)   # for standard monopsaced font
	
	# play sound
	if play_sound:
		sound = aud.Factory(sound_path+'/share/interface-rollover.mp3')
		audio.volume = 0.1
		audio.play(sound)
