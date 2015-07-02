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

"""
Small module that contains generic functions to use lights effects in the BGE.
"""

import bge
from mathutils import *

"""
This function is a game callback script toshow/hide an object if the camera is in a certain angular field. (point light for exemple ...)
The angular field is defined by the direction of the center ray and the angular amplitude of the field.
All coordinates are local coordinates.

To use it:
----------
* Add an always sensor connected to a python script actuator (type 'module') and type 
  'light.display_in_field' in the text entry.
* Put an object property named 'field_dir' (type string) an type the direction vector of 
  the central ray of the field, ('(6, 7.1, -5.32)' for exemple).
* Put an object property named 'field_limit' (type float) and put the angle in degrees that 
  limit the field (maximal angle between direction of the field and direction of the camera)
"""
def display_in_field(cont):
	owner     = cont.owner
	camera    = bge.logic.getCurrentScene().active_camera
	
	if 'field_dir' in owner:
		direction = owner['field_dir']
		if type(direction) == str:
			direction = Vector(eval(direction))
			owner['field_dir'] = direction
	else:
		direction = Vector((1,0,0))
		owner['field_dir'] = direction
	limit = owner['field_limit']
	
	worlddir = direction.rotate(owner.worldOrientation)
	owntocam = camera.worldPosition - owner.worldPosition
	if worlddir.angle(owntocam) > limit:
		owner.visible = False
	else:
		owner.visible = True
