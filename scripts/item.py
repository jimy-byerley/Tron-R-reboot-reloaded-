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


#######################################
### FUNCTIONS USED TO SPAWN AN ITEM ###

# Each function used to spawn a new item should receive 2 arguments :
#    rule : the item's definition line from 'items' list
#    properties : a dictionaary of parameters the item should take (see backup_manager.py:dump_item())

def just_spawn(rule, properties):
	""" Function to call to spawn a custom item (not the plug and play to use solution). """
	pass

def item_init():
	"""
	Generic initializer for item object.
	This function is to put in the definition list (see below), as function to initialize, or 
	to call from a python logick brick with 'module' option.
	"""
	cont = bge.logic.getCurrentController()
	owner = cont.owner

	owner['class'] = Item(owner, owner["itemname"], owner["hand"], owner["attach"])
	owner['class'].init()


###############################################################################
### ITEMS DECLARATIONS (to do dynamicaly from item script file if there is) ###

items = [
	# Each line is of type :
	# ("disk",            "disk.blend",      just_spawn,      None),
	# format :
	# (itemname,          file to load,      function to call to spawn a new item,  function to initialize the new item (or None))
]


 
class Item(object):
	""" 
	Standard item class, If you create an item with a class, you should use it, or create a 
	class with same methods.
	"""
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
