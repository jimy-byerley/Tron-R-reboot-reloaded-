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

import GameLogic
import bge
import mathutils

cursor_name = "cursor"
free_object = "to replace"

def addObject(name, lib, mesh, position) :
	"""Add an object from an other blender file.
	Parameteres : name (str or KX_GameObject) the object to add (name)
	              lib  (str) the blender file path for importation
	              mesh (str or MeshProxy) the mesh for the created object
	              position (str) the position of the center of the new object
	Returns : the created object (KX_GameObject)
	"""
	if lib not in bge.logic.LibList() : bge.logic.LibLoad(lib, "Mesh",  verbose = True)
	scene = bge.logic.getCurrentScene()
	cursor = scene.objects[cursor_name]
	cursor.position = mathutils.Euler(position)
	obj = scene.addObject(free_object, cursor_name)
	#obj.name = name
	obj.replaceMesh(mesh, True, True)
	obj.localScale = mathutils.Euler((1,1,1))
	return obj

