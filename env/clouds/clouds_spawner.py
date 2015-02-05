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

import random
import bge
import mathutils

def spawn_cloud() :
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	scene = bge.logic.getCurrentScene()

	scale = owner.localScale
	facescale = owner["facescale"]

	pos = owner.worldPosition.copy()
	for i in range(int(scale.x*scale.y*scale.z/(facescale**3))) :
		num = str(random.randrange(15))
		while len(num) != 3 : num = "0"+num
		new = scene.addObject("cloud face."+num, owner)
		
		pos.x += (random.random()-0.5)*scale.x
		pos.y += (random.random()-0.5)*scale.y
		pos.z += (random.random()-0.5)*scale.z
		if abs(pos.x - owner.worldPosition.x) > scale.x/2 : 	pos.x = owner.worldPosition.x + (random.random()-0.5)*scale.x
		if abs(pos.y - owner.worldPosition.y) > scale.y/2 : 	pos.y = owner.worldPosition.y + (random.random()-0.5)*scale.y
		if abs(pos.z - owner.worldPosition.z) > scale.z/2 : 	pos.z = owner.worldPosition.z + (random.random()-0.5)*scale.z
		print("create cloud face at", pos)
		new.worldPosition = pos
		
		new.localScale.x = facescale
		new.localScale.y = facescale
		new.localScale.z = facescale
		
		#new.setParent(owner)
