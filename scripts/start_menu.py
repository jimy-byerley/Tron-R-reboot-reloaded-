import bge
from bge.logic import *
from bge.events import *
from mathutils import *
from math import *
import os
import sys


bge.render.showMouse(True)

root_action_start = (25, 34)
root_action_loop = (34, 633)
settings_action_start = (700, 719)
settings_action_loop = (719,719)

def goto_menu_root():
	scene = bge.logic.getCurrentScene()
	armature = scene.objects['Armature']
	armature.playAction('ArmatureAction', 
		root_action_start[0], 
		root_action_start[1], 
		layer=1, 
		play_mode=KX_ACTION_MODE_PLAY)
	armature.playAction('ArmatureAction', 
		root_action_loop[0], 
		root_action_loop[1], 
		layer=0, 
		play_mode=KX_ACTION_MODE_LOOP)	

def mouse_rotate_interface(cont):
	owner = cont.owner
	mouse = cont.sensors[0]
	x = mouse.position[0] / bge.render.getWindowWidth() - 0.5
	y = mouse.position[1] / bge.render.getWindowHeight() - 0.5
	
	scene = bge.logic.getCurrentScene()
	scene.objects['Armature'].worldOrientation = Euler((-pi/12 * y, 0, -pi/12 * x))

def mouse_over_item(cont):
	mouseover = cont.sensors['Mouse']
	scene = bge.logic.getCurrentScene()
	cursor = scene.objects['root_cursor']
	owner = cont.owner
	if mouseover.status == KX_SENSOR_JUST_ACTIVATED:
		print(owner.localPosition.y)
		cursor.localPosition.y = owner.localPosition.y

def start_local():
	print(sys.platform)
	if sys.platform in ('linux', 'linux2'):
		f = open(bge.logic.expandPath('//../blenderplayer_path.txt'), 'r')
		blenderplayer = f.read()[:-1] +'/blenderplayer'
		f.close()
		width = 1024
		height = 600
		command = '%s -w %d %d %s - -l %s' % (
			blenderplayer,
			width, height,
			bge.logic.expandPath('//main.blend'),
			bge.logic.expandPath('//../backup-exemple.txt'),
		)
		print(command)
		os.system(command)
	if sys.platform in ('win', 'win32', 'win64'):
		pass

root_items = None
root_item_selected = 3

def keyboard_item(cont):
	global root_items, root_item_selected
	keyboard = cont.sensors[0]
	scene = bge.logic.getCurrentScene()
	cursor = scene.objects['root_cursor']
	armature = scene.objects['Armature']
	owner = cont.owner
	
	if root_items == None:
		# sort items by position on Y
		root_items = []
		for child in owner.parent.children:
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
	
	# up and down keys are used to select items
	if keyboard.getKeyStatus(UPARROWKEY) == KX_INPUT_JUST_ACTIVATED:
		if root_item_selected < len(root_items)-1:  root_item_selected += 1
	
	if keyboard.getKeyStatus(DOWNARROWKEY) == KX_INPUT_JUST_ACTIVATED:
		if root_item_selected > 0:  root_item_selected -= 1
	
	if keyboard.getKeyStatus(ENTERKEY) == KX_INPUT_JUST_ACTIVATED:
		name = root_items[root_item_selected].name
		if name == "enter_local_grid":
			#bge.logic.startGame("//main.blend")
			start_local()
		elif name == "configure_settings":
			frame = armature.getActionFrame(0)
			if frame >= settings_action_loop[0] and frame <= settings_action_loop[1]:
				armature.playAction('ArmatureAction', 
					settings_action_start[1], 
					settings_action_start[0], 
					layer=1, 
					play_mode=KX_ACTION_MODE_PLAY)
				armature.playAction('ArmatureAction', 
					root_action_loop[0], 
					root_action_loop[1], 
					layer=0, 
					play_mode=KX_ACTION_MODE_LOOP)
			else:
				armature.playAction('ArmatureAction', 
					settings_action_start[0], 
					settings_action_start[1], 
					layer=1, 
					play_mode=KX_ACTION_MODE_PLAY)
				armature.playAction('ArmatureAction', 
					settings_action_loop[0],
					settings_action_loop[1],
					layer=0, 
					play_mode=KX_ACTION_MODE_LOOP)
		elif name == "quit_tronr":
			bge.logic.endGame()
			
	
	if len(root_items):
		cursor.localPosition.z = root_items[root_item_selected].localPosition.z
	keyboard.reset()
	

def init(cont):
	goto_menu_root()
	
