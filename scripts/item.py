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
import time
import threading
from bge import texture
import backup_manager
import tools


# to set True after game initialized
load_async = False


# indexes for 'items' list.
NAME = 0
FILE = 1
SPAWN = 2
INIT = 3

#######################################
### FUNCTIONS USED TO SPAWN AN ITEM ###

# Each function used to spawn a new item should receive 2 arguments :
#    rule : the item's definition line from 'items' list
#    properties : a dictionaary of parameters the item should take (see backup_manager.py:dump_item())

def just_spawn(rule, params):
	""" Function to call to spawn a custom item (not the plug and play to use solution). """
	libname = bge.logic.expandPath(bge.logic.models_path+'/'+rule[FILE])
	
	# load library file if it is not loaded
	if libname not in bge.logic.LibList():
		time.sleep(0.5) # delay to prevent the BGE to crash if libraries are loaded to quick
	if libname not in bge.logic.LibList():
		print("module \"%s\": load item library: %s ..." % (__name__, repr(libname)))
		bge.logic.LibLoad(libname, "Scene", load_actions=True, load_scripts=True, async=load_async)
		#if load_async: time.sleep(2)
		#time.sleep(0.5)
		#tools.LibLoad(libname, "Scene", load_actions=True, load_scripts=True, async=True)
	scene = bge.logic.getCurrentScene()
	obj = scene.addObject(rule[NAME], scene.active_camera)
	backup_manager.configure_item(obj, params)
	obj['itemname'] = rule[NAME]
	
	return obj

def load_meshlib(rule, params):
	"""Function to load a mesh library before object library, the library should have the same name with "-mesh" added before .blend"""
	groups = rule[FILE].split('.')
	groups[-2] += '-meshes'
	filename = '.'.join(groups)
	libname = bge.logic.expandPath(bge.logic.models_path+'/'+filename)
	
	# load library file if it is not loaded
	if libname not in bge.logic.LibList():
		time.sleep(0.5) # delay to prevent the BGE to crash if libraries are loaded to quick
	if libname not in bge.logic.LibList():
		print("module \"%s\": load item mesh library: %s ..." % (__name__, repr(libname)))
		bge.logic.LibLoad(libname, "Mesh", load_actions=True, load_scripts=True, async=load_async)
		#if load_async: time.sleep(2)
		#time.sleep(0.5)
	return True
	

def item_init_module():
	"""
	Generic initializer for item object.
	This function is to put in the definition list (see below), as function to initialize, or 
	to call from a python logick brick with 'module' option.
	"""
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	item_init(owner)

def item_init(kx_object):
	kx_object['class'] = Item(owner, kx_object["itemname"], kx_object["hand"], kx_object["attach"])
	kx_object['class'].init()


##########################
### ITEMS DECLARATIONS ###

items = [
	# Each line is of type :
	("disk",            "disk.blend",         lambda r,p : load_meshlib(r,p) and just_spawn(r,p),      None),
	("light baton",     "light-baton.blend",  lambda r,p : load_meshlib(r,p) and just_spawn(r,p),      None),
	# format :
	# (itemname,          file to load,      function to call to spawn a new item,  function to initialize the new item (or None))
]

class item_initializer_thread(threading.Thread):
	def run(self):
		bge.logic.canstop += 1
		obj = self.rule[SPAWN](self.rule, self.config)
		if self.rule[INIT]:
			self.rule[INIT] (obj)
		bge.logic.canstop -= 1


def spawn_item(name, config, async=True):
	i = 0
	while items[i][NAME] != name: i+=1
	t = item_initializer_thread()
	t.rule = items[i]
	t.config = config
	if async: t.start()
	else:     t.run()

 
class Item(object):
	""" 
	Standard item class, If you create an item with a class, you should use it, or create a 
	class with same methods.
	
	The class should be initialized by a function referenced in 'items' list (function to initialize)
	If you want to create your custom class, you should write an other function that you put in the 
	items list. Else, you can initialize the item object from a python logic brick and then put None 
	in the items list at the fourth field.
	"""
	colors = []
	def __init__(self, kxobject, name, handbone, bodybone):
		self.object = kxobject
		self.name = name
		self.handbone = handbone
		self.bodybone = bodybone
		
	def getOwner(self):
		if self.object.parent and self.object.parent.parent and self.object.parent.parent.parent:
			return self.object.parent.parent.parent["class"]
		return None
		
	def getOwnerObject(self):
		if self.object.parent and self.object.parent.parent:
			return self.object.parent.parent.parent
		return None
	
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
