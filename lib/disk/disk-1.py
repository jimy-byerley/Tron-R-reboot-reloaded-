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
import mathutils

from item import *

import threading
import time

DISK_DAMAGE = 100              # nombre de points de vie (hp) qu'un joueur perd quand il subit un coup de disque
MAX_DISTANCE_LAUNCHER = 30     # distance a partir de laquelle un disque revient automatiquement a celui qui l'a lancé
LAUNCHER_PROPERTY = "launcher" # Game Property du disque faisant reférence au lanceur du disque

def update_activity() :
	"""update_activity() met a jour l'apparence et la dynamique du disque en fonction des GameProperties de l'objet.
	GameProperty "arme"    False : la lame est rentrée,  True : la lame est sortie.
	GameProperty "flying"  False : le disque est en dynamique noCollision  True : le disque vole et rebondit
	"""
	cont = bge.logic.getCurrentController()
	own = cont.owner
	
	if not "lame" in own:
		for obj in own.children:
			if "lame" in obj:
				own["lame"] = obj
			elif "light ambiance" in obj:
				own["light"] = obj
	lame = own["lame"]
	lame["arme"] = own["arme"]
	if own["arme"] == True:
		# deplier la lame
		lame.localScale.x = 1.34
		lame.localScale.y = 1.34
		lame.visible = True
		#own["light"].visible = True
	else :
		# replier la lame
		lame.localScale.x = 1
		lame.localScale.y = 1
		lame.visible = False
		#own["light"].visible = False
	if own["flying"] == True:
		#own.restoreDynamics()
		own.linVelocityMin = 35
		own.linVelocityMax = 40
	else:
		#own.suspendDynamics()
		own.linVelocityMin = 0
		own.linVelocityMax = 0
#


def update_orientation():
	"""update_orientation() met à jour l'orientation spaciale en 3d du disque selon sa direction
	Il utilise la vitesse effective (linV, linear velocity) du disque dans le worldspace.
	Le disque doit toujours etre dans un plan parallèle à sa trajectoire.
	Cette fonction est a appeler depuis un controller (KX_Controller).
	"""
	cont = bge.logic.getCurrentController()
	own = cont.owner
	if not own["flying"] : return
	linV = own.worldLinearVelocity
	if not linV.x and not linV.y and not linV.z : return
	orientation = mathutils.Euler((0,0,0))
	if linV.y and linV.z :
		orientation.x = acos(linV.y/sqrt(linV.y**2+linV.z**2))
	if linV.x and linV.z :
		orientation.y = asin(linV.z/sqrt(linV.x**2+linV.z**2))
	if linV.x and linV.y :
		orientation.z = acos(linV.x/sqrt(linV.x**2+linV.y**2))
	own.worldOrientation = orientation
#


def return_2_owner():
	"""return_2_owner() fonctionne uniquement lorque le disque s'élogigne trop de son proprietaire. Quand c'est la cas, elle fait revenir le disque sur lui.
	Cette fonction est a appeler depuis un controller (KX_Controller).
	"""
	cont = bge.logic.getCurrentController()
	own = cont.owner
	actu = cont.actuators["track to owner"]
	# le disque doit voler et avoir un proprietaire
	if LAUNCHER_PROPERTY in own and own["flying"] :
		prop = own[LAUNCHER_PROPERTY]
	else : return
	if not prop : return
	# distance au lanceur
	prop.worldPosition
	own.worldPosition
	vec = prop.worldPosition-own.worldPosition
	dist = sqrt(vec.x**2 + vec.y**2 + vec.z**2)
	# retour si necessaire
	if dist > MAX_DISTANCE_LAUNCHER :
		#own["last returned"] = time.time()
		actu.object = prop
		cont.activate("track to owner")
		own.localLinearVelocity = mathutils.Vector((0,1,0))
	else :
		actu.object = None
#

def disk_hit():
	"""disk_hit() tue les joueurs que le disque frappe.
	Cette fonction est a appeler depuis un controller activé par une brique capteur de collision (KX_Controller).
	"""
	cont = bge.logic.getCurrentController()
	own = cont.owner
	print('hittimes = ', own['hittimes'], end='  ')
	own['hittimes'] += 1
	print(own[hittimes])
	sens = cont.sensors["collision"]
	hits = sens.hitObjectList
	for hit in hits:
		if "hp" in hit :
			if hit != own["launcher"] :
				if "class" in hit : hit['class'].setHp(hit['hp']-1)
				else :hit["hp"] -= 1
#

class IDDisc(Item):
	disc_activate_date = 0.
	launching = False
	
	colors = { # meshes for colors
			'red'    : 'disk red',
			'orange' : 'disk orange',
			'white'  : 'disk white',
			'blue'   : 'disk blue',
			'green'  : 'disk green',
		}
	
	def action1(self):
		character = self.getOwner()
		if time.time() > self.disc_activate_date :
			self.disc_activate_date = time.time()+0.6
			if self.object["arme"] :
				self.object["arme"] = False
				# setup biking with disk position
				if character.vehicle and character.vehicle.name == "light-cycle":
					keys = character.skin.animations.keys()
					if "biking with disk" in keys and "biking take disk" in keys :
						loop = character.skin.animations['set cycle']
						take = character.skin.animations['biking take disk']
						character.skin.armature.playAction(loop[0], loop[4], loop[4], layer=0, play_mode=KX_ACTION_MODE_LOOP) # from light_baton.py
						character.skin.armature.playAction(take[0], take[3], take[4], layer=2, layer_weight=0)
				
			else :
				self.object["arme"] = True
				# setup biking with disk position
				if character.vehicle and character.vehicle.name == "light-cycle":
					keys = character.skin.animations.keys()
					if "biking with disk" in keys and "biking take disk" in keys :
						loop = character.skin.animations['biking with disk']
						take = character.skin.animations['biking take disk']
						character.skin.armature.playAction(loop[0], loop[2], loop[3], layer=0, play_mode=KX_ACTION_MODE_LOOP)
						character.skin.armature.playAction(take[0], take[1], take[2], layer=2, layer_weight=0)

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
			orientation = mathutils.Euler((-wo.y, wo.x, wo.z -pi/2))
			self.object.worldOrientation = orientation
			self.object.localLinearVelocity = mathutils.Vector((0,37,0))
			
			if self.object["arme"] :
				self.object["flying"] = True
			self.object["launcher"] = box
			self.launching = False
			#print('end of action2')
			
		thread = threading.Thread()
		thread.run = detach
		thread.start()

	def taken(self):
		Item.taken(self)
		print('set hittimes to 0')
		self.object['hittimes'] = 0
		self.disc_activate_date = time.time()+0.5
		if self.object["flying"]:
			self.object["flying"] = False
			skin = self.object['launcher']["class"].skin
			anim = skin.animations["catch disk"]
			skin.armature.playAction(anim[0], anim[1], anim[4], layer=2, layer_weight=0.0)
		self.object.localOrientation = mathutils.Euler((0,0,0))

	def droped(self):
		self.object["arme"] = False

	def unwielded(self):
		if self.object["arme"] : self.action1()

def item_init():
	cont = bge.logic.getCurrentController()
	owner = cont.owner

	owner['class'] = IDDisc(owner, owner["itemname"], owner["hand"], owner["attach"])
	owner['class'].init()

