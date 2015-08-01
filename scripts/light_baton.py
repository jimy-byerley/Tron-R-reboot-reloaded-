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
			dev.volume = 0.1
			dev.play(sound)
			
			holo = self.object.children[0]
			holo.visible = True
			self.cycle['class'].remove(netsync=False)
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
			dev.volume = 0.1
			
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
		if self.cycle: 
			print(self.cycle['uniqid'])


def item_init():
	cont = bge.logic.getCurrentController()
	owner = cont.owner

	owner['class'] = LightBaton(owner, owner["itemname"], owner["hand"], owner["attach"])
	owner['class'].init()



class LightCycle(Vehicle):
	# vehicle caracteristics
	max_speed = 100    # m/s
	max_yaw = pi/4     # rad/m
	max_accel = 20     # maximum acceleration m/s^2
	
	reach_stability = 0.1  # second
	reach_yaw = 0.1
	reach_tilt = 0.6
	
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
		Vehicle.init(self)
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

	def updateControl(self, speed, yaw, breaks, netsync=True):
		if speed > self.max_speed:    speed = self.max_speed
		elif speed < 0:               speed = 0
		if yaw > self.max_yaw: yaw = self.max_yaw
		if yaw < -self.max_yaw: yaw = -self.max_yaw
		self.object['speed']  = speed
		self.object['yaw']    = yaw
		self.object['breaks'] = breaks
		Vehicle.updateControl(self, speed, yaw, breaks, netsync)


def cycle_init(cont):
	owner = cont.owner
	owner['class'] = LightCycle(owner, owner["vehiclename"])
	owner['class'].init()

def cycle_update(cont):
	object = cont.owner
	cycle = object['class']
	onfloor = cycle.floor.sensors[0].status
	obstacle = cycle.front.sensors[0].status
	
	speed  = object['speed']
	yaw    = object['yaw']
	breaks = object['breaks']

	velocity = object.localLinearVelocity
	orientation = object.localOrientation.to_euler()
	angular = object.localAngularVelocity
	mass = object.mass
	
	if onfloor in (KX_INPUT_JUST_ACTIVATED, KX_INPUT_ACTIVE):
		# acceleration
		if speed < velocity.y:
			acceleration = -cycle.max_accel/10
		elif speed > velocity.y:
			acceleration = cycle.max_accel
		propulsion = mass * acceleration
		lateral_reaction = -mass *  velocity.x / cycle.reach_stability
		
		# tilt rotation
		if yaw > 0.1:    inclin = -pi/5
		elif yaw < -0.1: inclin = pi/5
		else:            inclin = 0
			
		tilt = (inclin - orientation.y) / cycle.reach_tilt
		
		# yaw speed
		torque_yaw = mass * cycle.max_yaw * velocity.y / cycle.reach_yaw
		if angular.z / velocity.y > cycle.max_yaw or abs(yaw - object.localAngularVelocity.z) < pi/12:
			torque_yaw = 0
		elif yaw < angular.z:
			torque_yaw = -torque_yaw
		
		# apply physic changes
		object.applyForce((lateral_reaction, propulsion, 0.), True)
		object.applyTorque((sin(orientation.y)*torque_yaw, 0., cos(orientation.y)*torque_yaw), True)
		object.localAngularVelocity.y = tilt
		
		# update wheels animation with vehicle speed
		if cycle.animup == 20:
			cycle.animup = 0
			s = 7*velocity.y / cycle.max_speed
			current = cycle.armature.getActionFrame(0)%60
			cycle.armature.playAction("light cycle running", current, current+59, speed=s, layer=0, play_mode=KX_ACTION_MODE_LOOP)
		else : cycle.animup += 1
