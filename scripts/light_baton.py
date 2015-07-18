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

from item import *
from vehicle import *
import time
import bge
from bge.logic import *
from mathutils import *
from math import *
import threading
import aud

class LightBaton(Item):
	cycle = None
	activate_date = 0.
	
	colors = { # meshes for color
		'blue' : 'light baton blue',
		'red' : 'light baton red',
		'orange' : 'light baton orange',
		'white' : 'light baton white',
		'green' : 'light baton green',
		}
	
	cyclecolors = { # meshes for cycle color
		'blue' : 'cycle body blue',
		'red' : 'cycle body red',
		'orange' : 'cycle body orange',
		'white' : 'cycle body white',
		'green' : 'cycle body green',
		}
	
	def init(self):
		Item.init(self)
		if "color" in self.object:
			self.changeColor(self.object['color'])

	def taken(self):
		Item.taken(self)
		self.changeColor(self.getOwner().getColor())
		self.activate_date = time.time()
	
	def action1(self):
		if self.activate_date+0.5 > time.time() : return
		if self.cycle :
			# play sound
			path = bge.logic.sounds_path+'/light-vehicles/cycle-stop.wav'
			sound = aud.Factory.file(path)
			dev = aud.device()
			cam = bge.logic.getCurrentScene().active_camera
			vec = self.getOwnerObject().worldPosition - cam.worldPosition
			dev.listener_location = vec
			dev.volume = 0.3
			dev.play(sound)
			
			holo = self.object.children[0]
			holo.visible = True
			self.cycle['class'].remove()
			self.cycle = None
			holo.playAction("light baton prototype", 10, 0)
			def t():
				while holo.getActionFrame() >= 2:
					time.sleep(0.05)
				holo.visible = False
			thread = threading.Thread()
			thread.run = t
			thread.start()
			
		else :
			# play sound
			path = bge.logic.sounds_path+'/light-vehicles/cycle-start.wav'
			sound = aud.Factory.file(path)
			dev = aud.device()
			cam = bge.logic.getCurrentScene().active_camera
			vec = self.getOwnerObject().worldPosition - cam.worldPosition
			dev.listener_location = vec
			dev.volume = 0.3
			
			# spawn the cycle
			skin = self.getOwner().skin
			armature = skin.armature
			anim = skin.animations["set cycle"]
			armature.playAction(anim[0], anim[1], anim[4], layer=1)
			hologram = self.object.children[0]
			def t():
				while armature.getActionFrame(1) <= anim[3] :
					time.sleep(0.05)
				hologram.visible = True
				hologram.playAction("light baton prototype", 0, 10)
				dev.play(sound)
				while hologram.getActionFrame(0) <= 8:
					time.sleep(0.05)
				scene = bge.logic.getCurrentScene()
				self.cycle = scene.addObject("light-cycle", self.getOwnerObject())
				self.cycle.worldLinearVelocity = self.getOwnerObject().worldLinearVelocity
				self.cycle['class'] = LightCycle(self.cycle, "light cycle")
				self.cycle['class'].init()
				self.cycle['class'].enter(self.getOwnerObject(), self.cycle['class'].driversplace)
				hologram.visible = False
				
				color = self.object['color']
				if color in self.cyclecolors : 
					#self.cycle['class'].armature.replaceMesh(self.cyclecolors[color])
					for child in self.cycle['class'].armature.children:
						if 'body' in child:
							child.replaceMesh(self.cyclecolors[color])
					#self.cycle['class'].armature.update()

			thread = threading.Thread()
			thread.run = t
			thread.start()
		self.activate_date = time.time()
	
	def action2(self):
		print(self.object['uniqid'])
		obj = bge.logic.getCurrentScene().objects[self.object.name]
		print(obj)
		print(obj == self.object)
		print(obj['uniqid'])


def item_init():
	cont = bge.logic.getCurrentController()
	owner = cont.owner

	owner['class'] = LightBaton(owner, owner["itemname"], owner["hand"], owner["attach"])
	owner['class'].init()



class LightCycle(Vehicle):
	reach = 2 # time to reach the maximal speed (~)
	animup = 10
	def enter(self, character, place):
		Vehicle.enter(self, character, place)
		armature = self.driver['class'].skin.armature
		# anim player to in vehicle position
		anim = self.driver['class'].skin.animations['set cycle']
		armature.playAction(anim[0], anim[4], anim[4], layer=0, play_mode=KX_ACTION_MODE_LOOP)
		for child in self.object.children:
			if "head_pos" in child:
				self.headpos = child
		head = self.driver['class'].camera_head
		self.oldheadpos = head.localPosition.copy()
		head.worldPosition = self.headpos.worldPosition

	def init(self):
		self.motion = self.object.actuators["motion"]
		self.motion.dLoc = Vector((0,0,0))
		self.object["move"] = True
		for child in self.object.children:
			if "floor sensor" in child:
				self.floor = child
			if "front sensor" in child:
				self.front = child
			if "armature" in child:
				self.armature = child
		self.timer = time.time()
		
	def exit(self, character):
		head = character['class'].camera_head
		head.localPosition = self.oldheadpos
		Vehicle.exit(self, character)

	def updateCont(self, com):
		#print(self.armature.meshes[0].materials)
		onfloor = self.floor.sensors[0].status # seul capteur
		obstacle = self.front.sensors[0].status # seul capteur
		date = time.time()
		
		if obstacle in (KX_INPUT_JUST_ACTIVATED, KX_INPUT_ACTIVE):
			self.motion.dLoc = Vector((0,0,0))
			return
		
		if onfloor in (KX_INPUT_JUST_ACTIVATED, KX_INPUT_ACTIVE):
			o = self.object.localOrientation.to_euler()
			i = Euler((o.x,0,0)) # inclinaison
			l = Vector((0.,0.,0.)) # vitesse lineaire
			r = Vector((0.,0.,0.)) # vitesse de rotation
			if com[FORD] :
				l.y = .8
				if com[BOOST] :
					l.y = 1.
				if com[BACK] :
					i.x = pi/4
			elif com[BACK] :
				if self.motion.dLoc.y > 0: l.y = -0.2
			if self.motion.dLoc.y > 0.05:
				if com[LEFT] :
					r.z = 1.1
					i.y = -0.8
				if com[RIGHT] :
					r.z = -1.1
					i.y = 0.8
			
			dt = date-self.timer
			self.motion.dLoc = self.motion.dLoc*(1-dt/self.reach) + l*dt/self.reach
			o.x = o.x*(1-dt*3) + i.x*dt*3
			o.y = o.y*(1-dt*3) + i.y*dt*3
			#if i.x : o.x = i.x
			#if i.y : o.y = i.y
			self.object.localOrientation = o
			#print(o)
			r.rotate(Euler((-o.x, -o.y, 0)))
			self.motion.dRot = r*dt
			if self.animup == 10:
				self.animup = 0
				s = self.motion.dLoc.y
				current = self.armature.getActionFrame(0)%9
				self.armature.playAction("light cycle running", current, current+9, speed=s, layer=0, play_mode=KX_ACTION_MODE_LOOP)
			else : self.animup += 1
			self.object['move'] = True
			self.timer = date


def cycle_init():
	owner = bge.logic.getCurrentController().owner
	owner['class'] = LightCycle(owner, owner["vehiclename"])
	owner['class'].init()
