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
import vehicle
import item
import character
from pprint import pprint


last_backup = {
	"max id"      = 0,   # current max ID for a saved object (next ID to assign)
	"characters"  = [],  # all the player and PNJ (also items take).   See dump_character()
	"items"       = [],  # all free items (not hold by a character).   See dump_item()
	"vehicles"    = [],  # all vehicles, including driven (active) vehicles. See dump_vehicle()
	"objects"     = [],  # other objects, with 'dump' property to 'object'
	
	# To mark an object to be saved in the backup, It should have the object property 'dump' 
	# set to one of the values of the markers detailled below.
}

# internal variables (but can be read by other scripts).
unloaded = []  # list of IDs of not loaded objects
loaded   = []  # list of IDs of loaded objects
max_id   = 0   # current next ID to assign


##  BACKUP MARKERS  ##
marker_property  = "dump"       # name of the game property (the marker)
marker_character = "character"  # object will be saved as a character
marker_item      = "item"       # object will be saved as an item
marker_vehicle   = "vehicle"    # object will be saved as a vehicle
marker_object    = "object"     # object properties and physic state will be saved
marker_dontsave  = ""           # object will not be saved, equivalent to not define the property


def get_object_id(kx_object):
	""" 
	Return the uniq ID of an object (character, item, ...) if the object's property
    "uniqid" is not defined, assign an unused id to this object. 
    """
    global max_id
    
	if "uniqid" in kx_object : return kx_object["backup_id"]
	else :
		i = max_id
		max_id += 1
		kx_object["uniqid"] = i
		return i


def dump_object(kx_object):
	""" Dump the object given by the root KXGameObject """
	
	item_def = kx_object['class']
	dump = {
		"id" :       get_object_id(kx_object),
		"name" :     kx_object["itemname"],
		"pos" :      kx_object.worldPosition,
		"orient" :   kx_object.worldOrientation,
	}
	velocity = kx_object.worldLinearVelocity
	if velocity : dump["velocity"] = velocity
	angular = kx_object.worldAngularVelocity
	if angular : dump["angular"] = angular
	scale = kx_object.worldScale
	if scale : dump["scale"] = scale
	
	properties = {}
	for prop_name in kx_object.getPropertyNames():
		properties[prop_name] = kx_object[prop_name]
	dump["properties"] = properties
	if item_def:
		dump["repr"] = repr(item_def)
	
	return dump



def dump_item(kx_object):
	""" Dump the item given by the root KXGameObject """
	return dump_object(kx_object)


def dump_character(kx_object):
	""" Dump the character given by the root KXGameObject """
	
	dump = dump_object(kx_object)
	character = kx_object['class']
	
	# basic character's attributes
	dump["name"]    = character.name
	dump["skin"]    = character.skin_name
	dump["helmet"]  = character.skin.helmet_active
	
	# items (just item name and properties)
	inventory = {
		"hand" : character.skin.handitem['itemname'],
	}
	attachs = character.skin.attachs
	items = character.skin.items
	for i in range(len(attachs)):
		if item: 
			properties = {}
			item = items[i]
			for prop_name in item.getPropertyNames():
				properties[prop_name] = item[prop_name]
			inventory[attachs[i]] = (get_object_id(item), item["itemname"], properties)
	dump["inventory"] = inventory
	
	return dump


def dump_vehicle(kx_object):
	""" Dump the vehicle given by the root KXGameObject """
	
	dump = dump_object(kx_object)
	vehicle = kx_object['class']
	
	# dump driver (optionnal)
	if vehicle.driver: dump['driver'] = vehicle.driver['class'].name
	
	# dump passengers (name by place)
	passengers = {}
	places = vehicle.passengers.keys()
	for i in range(len(vehicle.passengers)):
		if passengers[places[i]] : 
			passengers[places[i]] passengers[places[i]]['class'].name
	if passengers: dump['passengers'] = passengers
	
	return dump



def dump_all(scenestodump=['Scene']):
	""" Dumps the game state (items, vehicles, characters, ...) """
	global last_backup, loaded
	
	# remove old internal datas first
	loaded = []
	
	# then dump data from scenes
	scenes = bge.logic.getSceneList()
	for scenename in scenestodump:
		scene = scenes[scenename]
		for obj in scene.objects:
			if marker_property in obj :
				dump = obj[marker_property]
				
				if dump == "character":
					dump = dump_character(obj)
					loaded.append(dump['id'])
					last_backup['characters'].append(dump)
				
				elif dump == "vehicle":
					dump = dump_vehicle(obj)
					loaded.append(dump['id'])
					last_backup['vehicles'].append(dump)
				
				elif dump == "item":
					if not obj.parent or not "character" in obj.parent :
					dump = dump_item(obj)
					loaded.append(dump['id'])
					last_backup['items'].append(dump)
	
	# remove last_backup IDs which are not in unloaded or in loaded objects
	totalids = loaded+unloaded
	for dataname in ('characters', 'vehicles', 'items', 'objects'):
		for i in range(len(last_backup[dataname])):
			if last_backup[dataname]['id'] not in totalids:
				last_backup[dataname].pop(i)


def load_item(dump): # dictionnary
	pass
