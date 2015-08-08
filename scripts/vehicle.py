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
import pickle, time
import backup_manager as bm
import client


# indexes for 'vehicles' list.
NAME = 0
FILE = 1
SPAWN = 2
INIT = 3

# constantes pour les commandes passées au vehicule
FORD = 0
BACK = 1
LEFT = 2
RIGHT = 3
BOOST = 4
FIRE = 5
ALTFIRE = 6

def vehicle_init():
	owner = bge.logic.getCurrentController().owner
	owner['class'] = Vehicle(owner, owner['vehiclename'])
	owner['class'].init()


class Vehicle(object):
	driver = None # kxobject qui est le conducteur, ce doit etre un character (avec un champ class qui contient une instance de la class Character)
	driversplace = None
	passengers = {}

	sync_look = 0.
	sync_command = 0.
	
	# values to implement ont each vehicle, to inform characters (NPC or players), or to use in internal fonctions
	max_speed = 0 # (m/s)
	max_yaw = 0   # maximal rotation speed (rad/s)
	
	def __init__(self, kxobject, name):
		self.object = kxobject
		self.name = name
		self.object.setOcclusion(False, True)
		for child in self.object.children:
			if "vehicle place" in child:
				place = child['vehicle place']
				if place == "driver" : self.driversplace = child
				else: self.passengers[child] = None
		client = bge.logic.client
		if client:
			if client_callback not in client.callbacks: client.callbacks.append(client_callback)
			client.sync_physic(self.object)
			client.sync_property(self.object, 'hp')
	
	# internal method: send sync information, given as bytes and the python data
	def syncInfo(self, info, data):
		if bge.logic.client:
			if type(data) == int:      data = str(data).encode()
			elif type(data) == bytes:  pass
			else:                      data = pickle.dumps(data)
			bge.logic.client.add_to_queue(b'vehicle\0'+info+b'\0'+str(bm.get_object_id(self.object)).encode()+b'\0'+data)

	def enter(self, character, place, netsync=True):
		# character est le kxobject du personnage, place est le kxobject (empty) sur lequel est attaché le perso
		if self.driver == None and place == self.driversplace:
			if netsync: self.syncInfo(b'drive', str(bm.get_object_id(character)).encode())
			self.driver = character
			keyword = self.driversplace['vehicle place']+" "+self.name
			if keyword in character['class'].skin.animations.keys() :
				anim = character['class'].skin.animations[keyword]
				armature = character['class'].skin.armature
				armature.playAction(anim[0], anim[1], anim[4], 0)
			self.driver['class'].disable()
			self.driver.setParent(self.driversplace)
			self.driver['class'].vehicle = self.object
			
		elif place in self.passengers.keys() and self.passengers[place] == None:
			if netsync: self.syncInfo(b'enter', (bm.get_object_id(character), place.name))
			self.passengers[place] = character
			keyword = place['vehicle place']+" "+self.name
			if keyword in character['class'].skin.animations.keys() :
				anim = character['class'].skin.animations[keyword]
				armature = character['class'].skin.armature
				armature.playAction(anim[0], anim[1], anim[4], 0)
			self.driver['class'].disable()
			self.driver.setParent(self.place, compound=False, ghost=True)
			self.driver['class'].vehicle = self.object
			

	def exit(self, character, netsync=True):
		self.syncInfo(b'exit', bm.get_object_id(character))
		if character == self.driver :
			self.driver = None
			character['class'].vehicle = None
			character.removeParent()
			orient = self.object.worldOrientation.to_euler()
			character['class'].takeWay(orient.z)
			character['class'].enable()
		else:
			for p in self.passengers.keys():
				if self.passengers[p] == character:
					self.passengers[p] = None
					character['class'].vehicle = None
					character.removeParent()
					orient = self.object.worldOrientation.to_euler()
					character['class'].takeWay(orient.z)
					character['class'].enable()


	def init(self):
		pass

	def updateControl(self, speed, yaw, breaks, netsync=True):
		"""
		speed:    the target speed to reach, if greather than the maximum speed, it will never be reched (meters per sec, float)
		yaw:      the angular speed to reach, ... (radians per sec, float)
		breaks:   vehicle breaks (bool)
		"""
		if netsync and self.sync_command < time.time():
			self.syncInfo(b'command', (speed, yaw, breaks))
			self.sync_command = time.time() + 0.1
		

	def updateLook(self, rotEuler, netsync=True):
		# orientation euler du regard du joueur (world)
		if netsync and self.sync_look < time.time():
			self.syncInfo(b'look', rotEuler[:])
			self.sync_look = time.time() + 0.1

	def destroy(self, netsync=True):
		if netsync: self.syncInfo(b'destroy', b'')

	def remove(self, netsync=True):
		if netsync: self.syncInfo(b'remove', b'')
		if self.driver: self.exit(self.driver)
		for passenger in self.passengers.values():
			self.exit(passenger)
		self.object.endObject()


def client_callback(interface, packet):
	if client.similar(packet, b'vehicle\0'):
		# then retreive vehicle
		if packet.count(b'\0') < 3:
			print('error: client_callback: invalid packet', packet)
			return True
		info, idbytes = packet.split(b'\0', maxsplit=3)[1:3]
		data = packet[10+len(info)+len(idbytes):]
		if not idbytes.isdigit(): return True
		uniqid = int(idbytes)
		object = bm.get_object_by_id(bge.logic.getCurrentScene(), uniqid)
		if not object:
			print('error: client_callback: vehicle', uniqid, "doesn't exists")
			return True
		if 'class' not in object:
			print('error: client_callback: vehicle', uniqid, "doesn't have any class")
			return True
		vehicle = object['class']
		
		# treatment of informations
		if info == b'look':
			try: rotEuler = pickle.loads(data)
			except: return True
			vehicle.updateLook(rotEuler, netsync=False)
		
		elif info == b'command':
			try: speed, yaw, breaks = pickle.loads(data)
			except: return True
			vehicle.updateControl(speed, yaw, breaks, netsync=False)
		
		elif info == b'drive':
			if not data.isdigit(): return True
			character = bm.get_object_by_id(bge.logic.getCurrentScene(), int(data))
			if not character: return True
			vehicle.enter(character, vehicle.driversplace, netsync=False)
		
		elif info == b'enter':
			try: id, placename = pickle.loads(data)
			except: return True
			character = bm.get_object_by_id(bge.logic.getCurrentScene(), id)
			place = None
			if placename == vehicle.driversplace.name: place = vehicle.driversplace
			for placeobject in vehicle.passengers.keys():
				if placeobject.name == placename:
					place = placeobject
			if place and character:
				vehicle.enter(character, place, netsync=False)
		
		elif info == b'exit':
			if not data.isdigit(): return False
			character = bm.get_object_by_id(bge.logic.getCurrentScene(), int(data))
			if not character: return False
			vehicle.exit(character, netsync=False)
		
		elif info == b'destroy':
			vehicle.destroy(netsync=False)
			
		elif info == b'remove':
			vehicle.remove(netsync=False)
