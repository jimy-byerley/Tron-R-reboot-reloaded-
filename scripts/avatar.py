# -*- coding:utf-8 -*-

"""
Copyright 2014,2015 Yves Dejonghe

This file is part of Tron-R.

    Tron-R is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Tron-R is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Tron-R.  If not, see <http://www.gnu.org/licenses/>. 2
"""

import config
import bge, mathutils, aud
import time, random, copy, threading, math, pickle
import character, vehicle, filters
import backup_manager as bm
from bge.logic import *
from bge.events import *

class Avatar(character.Character) :
	"""
	Cette classe représente le joueur à la première personne sur cet ordinateur.
	"""
	overlay = None
	menu_active = False

	def spawn(self, ref, existing=False) :
		character.Character.spawn(self, ref, existing)
		for scene in bge.logic.getSceneList() :
			if scene.name == "overlay" :
				self.overlay = scene
		self.box["first player"] = True
		scene.addObject("skybox", ref)
	

	def setHp(self, hp) :
		pass
		"""
		if not self.overlay : self.overlay = bge.logic.getSceneList()[1]
		character.Character.setHp(self, hp)
		if hp <= 0 :
			hp = 0
			bge.logic.getCurrentScene().suspend()
			window = self.overlay.objects["end window"]
			window.visible = True
			window.children[0]["Text"] = window.children[0]["Text"].format(self.name)
			window.children[0].visible = True
			bge.logic.setExitKey(bge.events.ENTERKEY)
		self.box["hp"] = hp
		self.overlay.objects["hp progress bar"].localScale.x = hp
		"""

	def updateItemOverlay(self) :
		if not self.overlay : self.overlay = bge.logic.getSceneList()[1]

		empty_scale = 0.8
		full_scale = 1
		empty_hand_scale = 0.5
		full_hand_scale = 1.8
		
		# inventory
		for i in range(len(self.skin.items)) :
			bloc = self.overlay.objects["item bloc "+str(i)]
			visual = bloc.children[0]
			text = bloc.children[1]
			if self.skin.items[i] :
				bloc.localScale = mathutils.Euler((full_scale,  full_scale,  full_scale))
				if "itemname" in self.skin.items[i] :
					text["Text"] = self.skin.items[i]["itemname"].upper()
				else :
					text["Text"] = self.skin.items[i].name.upper()
			else :
				bloc.localScale = mathutils.Euler((empty_scale, empty_scale, empty_scale))
				text["Text"] = "<EMPTY>"
		# hand
		bloc = self.overlay.objects["hand bloc"]
		visual = bloc.children[0]
		text = bloc.children[1]
		if self.skin.handitem :
			bloc.localScale = mathutils.Euler((full_hand_scale,  full_hand_scale,  full_hand_scale))
			if "itemname" in self.skin.handitem :
				text["Text"] = self.skin.handitem["itemname"].upper()
			else :
				text["Text"] = self.skin.handitem.name.upper()
		else :
			bloc.localScale = mathutils.Euler((empty_hand_scale, empty_hand_scale, empty_hand_scale))
			text["Text"] = "<EMPTY>"
		
	def wieldItem(self, item) :
		if not self.overlay : self.overlay = bge.logic.getSceneList()[1]
		
		thread = threading.Thread()
		def a() :
			character.Character.wieldItem(self, item, wait=True)
			self.updateItemOverlay()
		thread.run = a
		thread.start()
		

	def drop(self) :
		self.updateItemOverlay()
		thread = threading.Thread()
		def a() :
			character.Character.drop(self)
			self.updateItemOverlay()
		thread.run = a
		thread.start()

	def take(self) :
		self.updateItemOverlay()
		thread = threading.Thread()
		def a() :
			character.Character.take(self)
			self.updateItemOverlay()
		thread.run = a
		thread.start()
	
	def actionItem(self, action):
		self.updateItemOverlay()
		character.Character.actionItem(self, action)
		self.updateItemOverlay()
	
	# internal methode: send sync informations, given as bytes and the python data
	def syncInfo(self, info, data):
		if bge.logic.client:
			if type(data) == int:      data = str(data).encode()
			elif type(data) == bytes:  pass
			else:                      data = pickle.dumps(data)
			# similar to Character class's method, but use the marker 'avatar\0' instead of 'character\0'
			bge.logic.client.queue.append(b'avatar\0'+info+b'\0'+str(bm.get_object_id(self.box)).encode()+b'\0'+data)
	
	def toggle_menu(self, menu=None):
		if menu==None: menu = not self.menu_active
		self.menu_active = menu
		if menu:
			self.overlay.objects['menu'].visible = True
			for child in self.overlay.objects['menu'].childrenRecursive:
				child.visible = True
			filters.enable_filter('pause menu')
			bge.render.showMouse(True)
		else:
			self.overlay.objects['menu'].visible = False
			for child in self.overlay.objects['menu'].childrenRecursive:
				child.visible = False
			filters.disable_filter('pause menu')
			bge.render.showMouse(False)
			bge.render.setMousePosition(WIN_MIDDLE_X, WIN_MIDDLE_Y)



first_player = None



def init(cont) :
	owner = cont.owner
	scene = bge.logic.getCurrentScene()

	global first_player
	if first_player != None: return
	bge.logic.addScene("overlay", 2)
	
	first_player = Avatar(owner["character_name"], owner["skin"])
	first_player.spawn(owner)
	first_player.setCameraActive("tps")
	first_player.setCameraActive("fps")
	#owner.setParent(first_player.box)

def init_noauto(game_config, player_dump) :
	global first_player
	if first_player != None:
		print('first player is initialized yet.')
		return
	bge.logic.addScene("overlay", 2)
	fp_obj = None
	for obj in bge.logic.getCurrentScene().objects:
		if 'uniqid' in obj and obj['uniqid'] == game_config['object_id']:
			fp_obj = obj
	scene = bge.logic.getCurrentScene()
	first_player = Avatar(game_config['nickname'], game_config["skin"])
	first_player.spawn(scene.active_camera, existing=fp_obj)
	first_player.setCameraActive("tps")
	first_player.setCameraActive("fps")

def post_init():
	first_player.updateItemOverlay()	



def setup_overlay() :
	scene = bge.logic.getCurrentScene()
	camera = scene.objects["Camera"]
	#first_player.overlay = scene
	w = bge.render.getWindowWidth()
	h = bge.render.getWindowHeight()
	top = scene.objects["top side"]
	bottom = scene.objects["bottom side"]
	right = scene.objects["right side"]
	left = scene.objects["left side"]

	camera.setViewport(0, 0, w, h)   # n'a pas d'effet
	
	if w >= h :
		x = ((top.localPosition.z-bottom.localPosition.z)/h * w)/2
		right.localPosition.x = x
		left.localPosition.x = -x
	elif h > w :
		z = ((right.localPosition.x-left.localPosition.x)/w * h)/2
		top.localPosition.z = z
		bottom.localPosition.z = -z


def _touch(sensor, key) :
	if sensor.getKeyStatus(key) in (bge.logic.KX_INPUT_JUST_ACTIVATED, bge.logic.KX_INPUT_ACTIVE):
		return True
	else: return False

def _click(sensor, key) :
	status = sensor.getButtonStatus(key)
	if status == bge.logic.KX_INPUT_JUST_ACTIVATED or status == bge.logic.KX_INPUT_ACTIVE:
		return True
	else: return False



WIN_MIDDLE_X = int(bge.render.getWindowWidth()/2)
WIN_MIDDLE_Y = int(bge.render.getWindowHeight()/2)
mx, my = (WIN_MIDDLE_X, WIN_MIDDLE_Y)
bge.render.setMousePosition(WIN_MIDDLE_X, WIN_MIDDLE_Y)
change = False
boxrotz = 0

def keyboard_input() :
	"""
	keyboard_input() est le callback du clavier, il est appelé par le spawn du premier joueur
	"""
	global last_action, first_player, change, mx, boxrotz
	cont = bge.logic.getCurrentController()
	own = cont.owner
	sens = cont.sensors[0]

	change = False; # doit etre placé à vrai si l'utilisateur effectue un déplacement
	x = (mx)*config.mouse.sensibility # réorientation de la camera (utilisation des variables de mouse_input() )
	y = (my)*config.mouse.sensibility
	camrotz = 0 # lacet de la camera dans le referentiel de la boite
	
	## menu ##
	
	if sens.getKeyStatus(config.keys.pause_menu) == KX_INPUT_JUST_ACTIVATED:
		first_player.toggle_menu()
	if first_player.menu_active: return

	## camera control ##

	if _touch(sens, config.keys.toggle_fps) :
		first_player.setCameraActive("fps")
	elif _touch(sens, config.keys.toggle_tps) :
		first_player.setCameraActive("back")

	## misc control ##

	# drop
	if _touch(sens, config.keys.drop) :
		first_player.drop()
		
	# wield item
	if _touch(sens, config.keys.item1):
		first_player.wieldItem(0)
	if _touch(sens, config.keys.item2):
		first_player.wieldItem(1)
	if _touch(sens, config.keys.item3):
		first_player.wieldItem(2)
	
	# show/hide helmet
	if sens.getKeyStatus(config.keys.toggle_helmet) == KX_INPUT_JUST_ACTIVATED:
		first_player.toggleHelmet()

	
	## motion control ##

	if first_player.isactive() != False:
		if _touch(sens, config.keys.run) :
			# devant
			if _touch(sens, config.keys.forward) :
				# orientation du regard selon les touches de droite t gauche
				if _touch(sens, config.keys.left):
					camrotz = -math.pi/4;
				elif _touch(sens, config.keys.right):
					camrotz = math.pi/4;
				# course
				first_player.updateRunning(3.5);
			# derriere
			elif _touch(sens, config.keys.back) :
				first_player.updateRunning(-3);
			else :
				first_player.updateRunning(0);
			change = True;
		else :
			# devant
			if _touch(sens, config.keys.forward):
				# orientation du regard selon les touches de droite t gauche
				if _touch(sens, config.keys.left):
					camrotz = -math.pi/4;
				elif _touch(sens, config.keys.right):
					camrotz = math.pi/4;
				# marche
				first_player.updateRunning(1.6);
				change = True;
			# derriere
			elif _touch(sens, config.keys.back):
				first_player.updateRunning(-1.6);
				change = True;
			else :
				first_player.updateRunning(0);

		# sauter
		if _touch(sens, config.keys.jump) :
			first_player.updateJump(True);
			change = True;
		else:
			first_player.updateJump(False);

		if change : # si déplacement, changement de l'orientation en fonction de la souris
			first_player.takeWay(-x)
			#first_player.orient.z = -x

	if first_player.vehicle :
		com = copy.deepcopy([False]*7)
		if _touch(sens, config.vehicle.keyford):
			com[vehicle.FORD] = True
		if _touch(sens, config.vehicle.keyleft):
			com[vehicle.LEFT] = True
		if _touch(sens, config.vehicle.keyright):
			com[vehicle.RIGHT] = True
		if _touch(sens, config.vehicle.keyback):
			com[vehicle.BACK] = True
		if _touch(sens, config.vehicle.keyboost):
			com[vehicle.BOOST] = True

		first_player.vehicleCommand(com)




def mouse_input() :
	"""mouse_input() gere les entrées de la souris et déplace la camera et le joueur en fonction.
	Cette fonction est parametrée par les champs du fichier config.py dans le meme repertoire
	Ce callback est appele par le spawn du premier joueur
	"""
	global mx, my, first_player, headcam, boxrotz
	cont = bge.logic.getCurrentController()
	own = cont.owner
	sens = cont.sensors[0]

	if first_player.menu_active: return

	if _click(sens, config.interact.take) and first_player.getInteractor() : # l'utilisateur doit cliquer pour ramasser l'objet
		obj = first_player.getInteractor()
		if "interact" in obj:
			first_player.click()
		elif "item" in obj:
			first_player.take()

	if _click(sens, config.interact.itemaction1):
		first_player.actionItem(1)
	if _click(sens, config.interact.itemaction2):
		first_player.actionItem(2)
	if _click(sens, config.interact.itemaction3):
		first_player.actionItem(3)
	
	mx += sens.position[0] - WIN_MIDDLE_X
	my += sens.position[1] - WIN_MIDDLE_Y
	x = (mx)*config.mouse.sensibility
	y = (my)*config.mouse.sensibility

	if y > math.pi/2:
		y = math.pi/2
		my -= sens.position[1] - WIN_MIDDLE_Y
	elif y < -math.pi/2:
		y = -math.pi/2
		my -= sens.position[1] - WIN_MIDDLE_Y
	if not first_player.isactive():
		x += first_player.orient.z
		if x > math.pi/2:
			x = math.pi/2
			mx -= sens.position[0] - WIN_MIDDLE_X
		elif x < -math.pi/2:
			x = -math.pi/2
			mx -= sens.position[0] - WIN_MIDDLE_X
		x -= first_player.orient.z
	first_player.lookAt(mathutils.Euler((0, y, -x)))

	bge.render.setMousePosition(WIN_MIDDLE_X, WIN_MIDDLE_Y)


menu_item_selected = None

def mouse_over_item(cont):
	global menu_item_selected
	mouseover = cont.sensors['Mouse']
	owner = cont.owner
	cursor = first_player.overlay.objects['menu_cursor']
	if mouseover.status == KX_SENSOR_JUST_ACTIVATED:
		menu_item_selected = owner
		cursor.setParent(owner)
		cursor.localPosition = (-1., -0.1, 0)
		cursor.localOrientation = mathutils.Euler((-math.pi/2, 0., 0.))
		# play sound
		sound = aud.Factory(bge.logic.sounds_path+'/share/interface-rollover.mp3')
		audio = aud.device()
		audio.volume = 0.1
		audio.play(sound)
	if mouseover.status in (KX_SENSOR_JUST_ACTIVATED, KX_SENSOR_ACTIVE) and mouseover.getButtonStatus(LEFTMOUSE) == KX_INPUT_JUST_ACTIVATED:
		menu_select()

def menu_cursor_blink(cont):
	if first_player.menu_active:
		cont.owner.visible = not cont.owner.visible
	elif cont.owner.visible:
		cont.owner.visible = False

def menu_select():
	print(menu_item_selected.name)
	if menu_item_selected.name == 'quit_game':
		bge.logic.bootloader['quit'] = True
	if menu_item_selected.name == 'resume_game':
		first_player.toggle_menu(False)


def skybox_update(cont) :
	cont.owner.worldPosition = first_player.box.worldPosition
