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

import character
import config
import bge
import mathutils
import math
import Rasterizer
import threading
import time
import vehicle
import copy
import random

class Avatar(character.Character) :
	"""
	Cette classe représente le joueur à la première personne sur cet ordinateur.
	"""

	def spawn(self, ref) :
		character.Character.spawn(self, ref)
		self.overlay = None
		for scene in bge.logic.getSceneList() :
			if scene.name == "overlay" :
				self.overlay = scene
		self.box["first player"] = True

	def setHp(self, hp) :
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

	def updateItemOverlay(self) :
		if not self.overlay : self.overlay = bge.logic.getSceneList()[1]

		empty_scale = 0.8
		full_scale = 1
		empty_hand_scale = 1.4
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
		
		
		


first_player = None



def init() :
	cont = bge.logic.getCurrentController();
	owner = cont.owner;
	scene = bge.logic.getCurrentScene();

	global first_player;
	bge.logic.addScene("overlay", 2)
	
	owner["p"] = first_player = Avatar(owner["character_name"], owner["skin"]);
	first_player.spawn(owner);
	first_player.setCameraActive("tps");
	first_player.setCameraActive("fps");
	owner.setParent(first_player.box)
	#thread = threading.Thread()
	#thread.run = mouse_thread
	#thread.start()


def setup_overlay() :
	scene = bge.logic.getCurrentScene()
	camera = scene.objects["Camera"]
	#first_player.overlay = scene
	w = Rasterizer.getWindowWidth()
	h = Rasterizer.getWindowHeight()
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



WIN_MIDDLE_X = int(Rasterizer.getWindowWidth()/2)
WIN_MIDDLE_Y = int(Rasterizer.getWindowHeight()/2)
mx, my = (WIN_MIDDLE_X, WIN_MIDDLE_Y)
Rasterizer.setMousePosition(WIN_MIDDLE_X, WIN_MIDDLE_Y)
change = False
boxrotz = 0;

def keyboard_input() :
	"""
	keyboard_input() est le callback du clavier, il est appelé par le spawn du premier joueur
	"""
	global last_action, first_player, change, mx, boxrotz;
	cont = bge.logic.getCurrentController();
	own = cont.owner;
	sens = cont.sensors[0];

	change = False; # doit etre placé à vrai si l'utilisateur effectue un déplacement
	x = (mx)*config.mouse.sensibility; # réorientation de la camera (utilisation des variables de mouse_input() )
	y = (my)*config.mouse.sensibility;
	camrotz = 0; # lacet de la camera dans le referentiel de la boite

	## camera control ##

	if _touch(sens, config.keys.toggle_fps) :
		first_player.setCameraActive("fps");
	elif _touch(sens, config.keys.toggle_tps) :
		first_player.setCameraActive("back");

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
	if _touch(sens, config.keys.toggle_helmet):
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
	cont = bge.logic.getCurrentController()
	own = cont.owner
	sens = cont.sensors[0]

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
	
	global mx, my, first_player, headcam, boxrotz
	mx += sens.position[0] - WIN_MIDDLE_X
	my += sens.position[1] - WIN_MIDDLE_Y
	x = (mx)*config.mouse.sensibility
	y = (my)*config.mouse.sensibility

	first_player.lookAt(mathutils.Euler((0, y, -x)))

	Rasterizer.setMousePosition(WIN_MIDDLE_X, WIN_MIDDLE_Y)



def update_skybox() :
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	owner.worldPosition = first_player.box.worldPosition

def update_bloom_fac(cont) :
	cont.owner['bloom_fac'] = 1.9/Rasterizer.getWindowWidth()
