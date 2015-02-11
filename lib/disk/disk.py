# -*- Coding: utf8 -*-

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

import bge
from bge.logic import *
from math import *
from mathutils import *

from item import *

import threading
import time

DISK_DAMAGE = 1  # fraction de vie qu'un joueur perd quand il recoit un coup de disque
MAX_DISTANCE_LAUNCHER = 30     # distance a partir de laquelle un disque revient automatiquement a celui qui l'a lancé
LAUNCHER_PROPERTY = "launcher" # Game Property du disque faisant reférence au lanceur du disque


def item_init():
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	
	if not "lame" in owner:
		for obj in owner.children:
			if "lame" in obj:
				owner["lame"] = obj
			elif "light ambiance" in obj:
				owner["light"] = obj

	owner['class'] = IDDisc(owner, owner["itemname"], owner["hand"], owner["attach"])
	owner['class'].init()


def update_activity() :
	"""update_activity() met a jour l'apparence et la dynamique du disque en fonction des GameProperties de l'objet.
	"""
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	collision        = owner.sensors['collision']
	sound_launch     = owner.actuators['launch']
	sound_active     = owner.actuators['active']
	sound_activate   = owner.actuators['activate']
	sound_deactivate = owner.actuators['deactivate']
	
	
	if owner['class'].active == True:
		if owner['just activated'] :
			cont.activate(sound_activate)
			owner['just activated'] = False
		elif owner['just launched']:
			cont.activate(sound_launch)
			owner['just launched'] = False
		else :
			cont.activate(sound_active)
		#own["light"].visible = True
		if owner["flying"] == True:
			# update orientation
			linV = owner.worldLinearVelocity
			orientation = Euler((0,0,0))
			if linV.y and linV.z :
				orientation.x = acos(linV.y/sqrt(linV.y**2+linV.z**2))
			if linV.x and linV.z :
				orientation.y = acos(linV.z/sqrt(linV.x**2+linV.z**2))
			if linV.x and linV.y :
				orientation.z = acos(linV.x/sqrt(linV.x**2+linV.y**2))
			owner.worldOrientation = orientation
			# calcul de la distance au lanceur
			vec = owner.worldPosition - owner['launcher'].worldPosition
			dist = sqrt(vec.x*vec.x + vec.y*vec.y + vec.z*vec.z)
			if dist >= MAX_DISTANCE_LAUNCHER :
				owner['class'].returnToLauncher()
		
		if collision.status in (KX_SENSOR_ACTIVE, KX_SENSOR_JUST_ACTIVATED):
			collision.reset()
			owner['class'].hittimes += 1
			if owner['class'].hittimes >= 3:
				owner['class'].returnToLauncher()
			hits = collision.hitObjectList
			for hit in hits:
				if "hp" in hit :
					if hit != owner["launcher"] :
						# evolved system with a class which represents the object
						if "class" in hit : hit['class'].setHp(hit['hp']-1)
						# basic object with blender logic brics
						else : hit["hp"] -= 1
	else :
		if owner['just deactivated']:
			cont.activate(sound_deactivate)
			owner['just deactivated'] = False
		cont.deactivate(sound_active)



class IDDisc(Item):
	disc_activate_date = 0.
	launching = False
	hittimes = 0
	
	colors = { # meshes for colors
			'red'    : 'disk red',
			'orange' : 'disk orange',
			'white'  : 'disk white',
			'blue'   : 'disk blue',
			'green'  : 'disk green',
		}
	
	def init(self):
		Item.init(self)
		if self.object['lame'].localScale.x >= 1 :
			self.active = True
		else:
			self.active = False
		self.object['just activated'] = False
		self.object['just deactivated'] = False
		self.object['just launched'] = False
		self.object['launcher'] = None
		self.object['flying'] = False
	
	def action1(self):
		character = self.getOwner()
		if time.time() > self.disc_activate_date :
			self.disc_activate_date = time.time()+0.6
			if self.active :
				self.setActive(False)
			else : 
				self.setActive(True)

	def action2(self):
		if self.launching : return
		self.launching = True
		armature = self.object.parent.parent
		box = armature.parent # 3 niveaux : empty, armature, box
		skin = box["class"].skin
		anim = skin.animations["launch disk"]
		armature.playAction(anim[0], anim[1], anim[4], layer=2, layer_weight=0.0)
		def detach():
			while int(armature.getActionFrame(2)) < anim[2]:
				time.sleep(0.05)
			box["class"].drop()
			
			wo = box["class"].camera_head.worldOrientation.to_euler()
			orientation = Euler((-wo.y, wo.x, wo.z -pi/2))
			self.object.worldOrientation = orientation
			self.object.localLinearVelocity = Euler((0,37,0))
			
			if self.active :
				self.object["flying"] = True
				self.object['just launched'] = True
			self.launching = False
			#print('end of action2')
			
		thread = threading.Thread()
		thread.run = detach
		thread.start()

	def taken(self):
		Item.taken(self)
		self.object["launcher"] = self.object.parent.parent.parent # 3 niveaux : empty, armature, box
		self.hittimes = 0
		self.disc_activate_date = time.time()+0.5
		if self.object["flying"]:
			self.object["flying"] = False
			skin = self.object['launcher']["class"].skin
			anim = skin.animations["catch disk"]
			skin.armature.playAction(anim[0], anim[1], anim[4], layer=2, layer_weight=0.0)
		self.object.localOrientation = Euler((0,0,0))

	def droped(self):
		self.setActive(False)

	def unwielded(self):
		self.setActive(False)

	def setActive(self, active=True):
		self.active = active
		self.object['active'] = active
		self.object['lame']['active'] = active
		character = self.getOwner()
		
		if active :
			self.object['just activated'] = True
			self.object.linVelocityMin = 35
			self.object.linVelocityMax = 40
			self.object['lame'].localScale = (1.34, 1.34, 1)
			self.object['lame'].visible = True
			# setup biking with disk position
			if character.vehicle and character.vehicle.name == "light-cycle":
				keys = character.skin.animations.keys()
				if "biking with disk" in keys and "biking take disk" in keys :
					loop = character.skin.animations['set cycle']
					take = character.skin.animations['biking take disk']
					character.skin.armature.playAction(loop[0], loop[4], loop[4], layer=0, play_mode=KX_ACTION_MODE_LOOP) # from light_baton.py
					character.skin.armature.playAction(take[0], take[3], take[4], layer=2, layer_weight=0)
			
		else :
			self.object['just deactivated'] = True
			self.object.linVelocityMin = 0
			self.object.linVelocityMax = 0
			self.object['lame'].visible = False
			# setup biking with disk position
			if character.vehicle and character.vehicle.name == "light-cycle":
				keys = character.skin.animations.keys()
				if "biking with disk" in keys and "biking take disk" in keys :
					loop = character.skin.animations['biking with disk']
					take = character.skin.animations['biking take disk']
					character.skin.armature.playAction(loop[0], loop[2], loop[3], layer=0, play_mode=KX_ACTION_MODE_LOOP)
					character.skin.armature.playAction(take[0], take[1], take[2], layer=2, layer_weight=0)

	
	
	def returnToLauncher(self):
		if not self.object['launcher']: return
		vec = self.object['launcher'].worldPosition + Vector((0,0,1.2)) - self.object.worldPosition
		vec.normalize()
		self.object.worldLinearVelocity = vec
