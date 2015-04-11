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


class Vehicle(object):
	driver = None # kxobject qui est le conducteur, ce doit etre un character (avec un champ class qui contient une instance de la class Character)
	driversplace = None
	passengers = {}
	
	def __init__(self, kxobject, name):
		self.object = kxobject
		self.name = name
		for child in self.object.children:
			if "vehicle place" in child:
				place = child['vehicle place']
				if place == "driver" : self.driversplace = child;
				else: self.passengers[child] = None

	def enter(self, character, place):
		# character est le kxobject du personnage, place est le kxobject (empty) sur lequel est attaché le perso
		if self.driver == None and place == self.driversplace:
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
			self.passengers[place] = character
			keyword = place['vehicle place']+" "+self.name
			if keyword in character['class'].skin.animations.keys() :
				anim = character['class'].skin.animations[keyword]
				armature = character['class'].skin.armature
				armature.playAction(anim[0], anim[1], anim[4], 0)
			self.driver['class'].disable()
			self.driver.setParent(self.place, compound=False, ghost=True)
			self.driver['class'].vehicle = self.object
			

	def exit(self, character):
		if character == self.driver :
			self.driver = None
			character['class'].vehicle = None
			character.removeParent()
			character['class'].enable()
		else:
			for p in self.passengers.keys():
				if self.passengers[p] == character:
					self.passengers[p] = None
					character['class'].vehicle = None
					character.removeParent()
					character['class'].enable()


	def init(self):
		pass

	def updateCont(self, command):
		# une commande est de la forme (avant, arriere, droite, gauche, acceleration), chaque valeur de l'ensemble est un booléen
		pass

	def updateLook(self, rotEuler):
		# orientation euler du regard du joueur (world)
		pass

	def destroy(self):
		pass

	def remove(self):
		self.exit(self.driver)
		for passenger in self.passengers.values():
			self.exit(passenger)
		self.object.endObject()


def vehicle_init():
	owner = bge.logic.getCurrentController().owner
	owner['class'] = Vehicle(owner, owner['vehiclename'])
	owner['class'].init()
