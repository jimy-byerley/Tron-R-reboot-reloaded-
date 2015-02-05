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
from bge import texture
 
class Item(object):
	colors = []
	def __init__(self, kxobject, name, handbone, bodybone):
		self.object = kxobject
		self.name = name
		self.handbone = handbone
		self.bodybone = bodybone
		
	def getOwner(self):
		return self.object.parent.parent.parent["class"]
		
	def getOwnerObject(self):
		return self.object.parent.parent.parent
	
	def changeColor(self, color):
		# change la couleur de l'item
		''' # changement de couleur par texture (ne fonctionne pas)
		if 'emit tex' not in self.object:
			matname = 'IM'+self.colors[self.object['color']].split('/')[-1]
			print(self.object, self.object.children, self.object['color'], matname)
			ID = texture.materialID(self.object, matname)
			object_texture = texture.Texture(self.object, ID)
			self.object['emit tex'] = object_texture
		
		url = bge.logic.expandPath(self.colors[color])
		src = texture.ImageFFmpeg(url)
		self.object['emit tex'].source = src
		texture.refresh(False)
		'''
		# changement du maillage
		if color in self.colors:
			self.object.replaceMesh(self.colors[color])
			self.object['color'] = color
	
	def changeHolderColor(self, color):
		# appelé lorsque le joueur qui tient l'item change de couleur
		self.changeColor(color)
	
	# appellée lorsque l'item est creé
	def init(self):
		pass
	
	def taken(self):
		self.changeColor(self.getOwner().getColor())
		pass
	
	def droped(self):
		pass
	
	def wielded(self):
		pass
	
	def unwielded(self):
		pass
	
	# clic gauche
	def action1(self):
		pass

	#clic droit
	def action2(self):
		pass

	#clic milieu
	def action3(self):
		pass


def item_init():
	cont = bge.logic.getCurrentController()
	owner = cont.owner

	owner['class'] = Item(owner, owner["itemname"], owner["hand"], owner["attach"])
	owner['class'].init()

