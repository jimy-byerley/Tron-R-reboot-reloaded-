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

elevator = None
last_dest = 0
children = []

def elevator_init():
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	global elevator
	elevator = owner

def elevator_request():
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	if not elevator : return
	if not elevator.isPlayingAction():
		global last_dest
		elevator.playAction("time returner ascensor", last_dest, owner['frame'], speed=0.3)
		last_dest = owner['frame']

def elevator_goto():
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	if not elevator : return
	if not elevator.isPlayingAction():
		global last_dest
		elevator.playAction("time returner ascensor", last_dest, owner['frame'], speed=0.3)
		last_dest = owner['frame']

def update_character_on():
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	sensor = cont.sensors[0]
	for obj in sensor.hitObjectList:
		if "character" in obj :
			if obj not in children:
				pos = obj.worldPosition
				obj.setParent(owner)
				obj.worldPosition = pos
				children.append(obj)
	for i in range(len(children)):
		obj = children[i]
		dist = (obj.worldPosition-owner.children['timereturner elevator center'].worldPosition).length
		if dist > 100: return
		if dist > 2.3:
			pos = obj.worldPosition
			obj.removeParent()
			obj.worldPosition = pos
			children.pop(i)
			break