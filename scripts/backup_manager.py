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

import time
import bge
import vehicle
import item
import character
import threading
from math import *
import mypprint as pprint


save_file = "" # file to save automaticaly the current file
autosave = False


last_backup = {
	"max id"      : 0,   # current max ID for a saved object (next ID to assign)
	"characters"  : [],  # all the player and PNJ (also items take).   See dump_character()
	"items"       : [],  # all free items (not hold by a character).   See dump_item()
	"vehicles"    : [],  # all vehicles, including driven (active) vehicles. See dump_vehicle()
	"objects"     : [],  # other objects, with 'dump' property to 'object'
	
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

properties_blacklist = ["class","repr","armature", "uniqid"]   # list of kx_object properties unsaved (because of eval() is not possible)
properties_supported = [int, str, list, dict, set, float, bytes] # list ob kx_object properties types which can be serialized (can be extended by other modules)



# standard function to get an 'object ID'.
def get_object_id(kx_object):
	""" 
	Return the uniq ID of an object (character, item, ...) if the object's property
	"uniqid" is not defined, assign an unused id to this object. 
	"""
	global max_id
    
	if "uniqid" in kx_object : return kx_object["uniqid"]
	else :
		total = unloaded+loaded
		while max_id in total:
			max_id += 1
		i = max_id
		kx_object["uniqid"] = i
		max_id = max_id+1
		return i

def get_object_by_id(scene, id):
	"""Return the first object (and normaly the only one) that have the uniqid id, or None."""
	for i in range(len(scene.objects)):
		if 'uniqid' in scene.objects[i] and scene.objects[i]['uniqid'] == id:
			return scene.objects[i]
	return None


def dump_object(kx_object):
	""" Dump the object given by the root KXGameObject """
	
	item_def = None
	if 'class' in kx_object : item_def = kx_object['class']
	dump = {
		"id" :       get_object_id(kx_object),
		"pos" :      kx_object.worldPosition.xyz[:],
		"orient" :   kx_object.worldOrientation.to_euler()[:],
	}
	velocity = kx_object.worldLinearVelocity.xyz[:]
	if velocity : dump["velocity"] = velocity
	angular = kx_object.worldAngularVelocity.xyz[:]
	if angular : dump["angular"] = angular
	scale = kx_object.worldScale.xyz[:]
	if scale : dump["scale"] = scale
	
	properties = {}
	for prop_name in kx_object.getPropertyNames():
		if (prop_name not in properties_blacklist) and (type(kx_object[prop_name]) in properties_supported):
			properties[prop_name] = kx_object[prop_name]
	if properties:
		dump["properties"] = properties
	if item_def:
		dump["repr"] = repr(item_def)
	
	return dump



def dump_item(kx_object):
	""" Dump the item given by the root KXGameObject """
	dump = dump_object(kx_object)
	dump["name"] = kx_object["itemname"]
	return dump


def dump_character(kx_object):
	""" Dump the character given by the root KXGameObject """
	
	dump = dump_object(kx_object)
	character = kx_object['class']
	
	# basic character's attributes
	dump["name"]    = character.name
	dump["skin"]    = character.skin_name
	dump["helmet"]  = character.skin.helmet_active
	
	# items (just item name and properties)
	inventory = {}
	if character.skin.handitem:
		item = character.skin.handitem
		properties = {}
		for prop_name in item.getPropertyNames():
			if (prop_name not in properties_blacklist) and (type(item[prop_name]) in properties_supported):
				properties[prop_name] = item[prop_name]
		inventory["hand"] = (get_object_id(item), item["itemname"], properties)
	else:
		inventory["hand"] = None
	attachs = character.skin.attachs
	items = character.skin.items
	for i in range(len(attachs)):
		item = items[i]
		if item:
			properties = {}
			for prop_name in item.getPropertyNames():
				if (prop_name not in properties_blacklist) and (type(item[prop_name]) in properties_supported):
					properties[prop_name] = item[prop_name]
			inventory[attachs[i].name] = (get_object_id(item), item["itemname"], properties)
	dump["inventory"] = inventory
	
	return dump


def dump_vehicle(kx_object):
	""" Dump the vehicle given by the root KXGameObject """
	
	dump = dump_object(kx_object)
	dump["vehiclename"] = kx_object["vehiclename"]
	vehicle = kx_object['class']
	
	# dump driver (optionnal)
	if vehicle.driver: dump['driver'] = vehicle.driver['class'].name
	
	# dump passengers (name by place)
	passengers = {}
	places = vehicle.passengers.keys()
	for i in range(len(vehicle.passengers)):
		if vehicle.passengers[places[i]] : 
			passengers[places[i]] = vehicle.passengers[places[i]]['class'].name
	if passengers: dump['passengers'] = passengers
	
	return dump


def dump_this(obj):
	"""dump the object given, return the dump dict and store it in global variable last_backup. """
	dump = obj[marker_property]
	
	if dump == "character":
		dump = dump_character(obj)
		loaded.append(dump['id'])
		i = 0
		while i < len(last_backup['characters']):
			#pprint.pprint(last_backup['characters'][i])
			if last_backup['characters'][i]['id'] == dump['id']:
				last_backup['characters'].pop(i)
			else: i += 1
		last_backup['characters'].append(dump)
		return dump
	
	elif dump == "vehicle":
		dump = dump_vehicle(obj)
		loaded.append(dump['id'])
		last_backup['vehicles'].append(dump)
		return dump
	
	elif dump == "item":
		if not obj.parent or not (obj.parent.parent and "character" not in obj.parent) :
			dump = dump_item(obj)
			loaded.append(dump['id'])
			i = 0
			while i < len(last_backup['items']):
				if last_backup['items'][i]['id'] == dump['id']:
					last_backup['items'].pop(i)
				else: i += 1
			last_backup['items'].append(dump)
			return dump
	
	elif dump == "object":
		dump = dump_object(obj)
		dump['name'] = obj.name
		loaded.append(dump['id'])
		i = 0
		while i < len(last_backup['objects']):
			if last_backup['objects'][i]['id'] == dump['id']:
				last_backup['objects'].pop(i)
			else: i += 1
		last_backup['objects'].append(dump)
		return dump
	
	else: return None


def dump_all(scenestodump=['Scene']):
	""" Dumps the game state (items, vehicles, characters, ...) """
	global last_backup, loaded, thread_loader_running
	if thread_loader_running: return
	thread_loader_running = True
	
	# remove old internal datas first
	loaded = []
	
	# then dump data from scenes
	scenes = bge.logic.getSceneList()
	for scene in scenes:
		if scene.name in scenestodump:
			for obj in scene.objects:
				if marker_property in obj :
					dump_this(obj)
	
	# remove last_backup IDs which are not in unloaded or in loaded objects
	totalids = loaded+unloaded
	for dataname in ('characters', 'vehicles', 'items', 'objects'):
		i = 0
		while i < len(last_backup[dataname]):
			if last_backup[dataname][i]['id'] not in totalids:
				last_backup[dataname].pop(i)
			else: i += 1
	
	last_backup['max id'] = max_id
	thread_loader_running = False


def configure_object(obj, params):
	""" Apply an object dump (dump_object()) to an existing object. """
	if 'id' in params and 'id' not in obj: obj['uniqid'] = params['id'] 
	if 'pos'      in params:	obj.worldPosition        = params['pos']
	if 'rot'      in params:	obj.worldOrientation     = params['rot']
	if 'velocity' in params:	obj.worldLinearVelocity  = params['velocity']
	if 'angular'  in params:	obj.worldAngularVelocity = params['angular']
	if 'properties' in params:
		properties = params['properties']
		for prop in properties:
			obj[prop] = properties[prop]
	
	if 'repr' in params and 'class' not in obj :
		try:	item_def = eval(params['repr'])
		except:	print("loading backup %s doesn't make sense." % params['repr'])
		else:	obj['class'] = item_def


def configure_item(obj, params):
	configure_object(obj, params)
	if 'owner' in params:
		skin = params['owner']['class'].skin
		skin.attach(obj, params['attach'])


thread_loader_running = False
def thread_loader():
	global thread_loader_running
	# one instance only
	if thread_loader_running: return
	thread_loader_running = True

	bge.logic.canstop += 1 # the game could not be stopped, except if canstop is equal to 0
	
	scene = bge.logic.getCurrentScene()
	camera = scene.active_camera
	if camera.parent:
		camera = camera.parent
	campos = camera.worldPosition
	
	thread_loader_running = False
	dump_all()
	thread_loader_running = True
	

	for config in last_backup['characters']:
		obpos = config['pos']
		dist = sqrt((campos[0]-obpos[0])**2 + (campos[1]-obpos[1])**2 + (campos[2]-obpos[2])**2)
		if dist < 50 and config['id'] in unloaded:
			new_char = character.Character(config['name'], config['skin'])
			new_char.spawn(camera)
			new_char.toggleHelmet(config['helmet'])
			configure_object(new_char.box, config)
			unloaded.pop(unloaded.index(config['id']))
			inventory = config['inventory']
			for attach in inventory:
				if inventory[attach] != None:
					itemconf = {
						'id':   inventory[attach][0],
						'name': inventory[attach][1],
						'properties': inventory[attach][2],
					}
					print('load item \"%s\" for character %s' % (itemconf['name'], config['name']))
					itemconf['owner'] = new_char.box
					itemconf['attach'] = attach
					item.spawn_item(itemconf['name'], itemconf, async=False)
					unloaded.pop(unloaded.index(itemconf['id']))
				
	
	for config in last_backup['items']:
		obpos = config['pos']
		dist = sqrt((campos[0]-obpos[0])**2 + (campos[1]-obpos[1])**2 + (campos[2]-obpos[2])**2)
		if dist < 50 and config['id'] in unloaded:
			print('load item \"%s\" at coordinates %d, %d, %d' % (config['name'], config['pos'][0], config['pos'][1], config['pos'][2]))
			item.spawn_item(config['name'], config, async=False)
			unloaded.pop(unloaded.index(config['id']))
	
	for config in last_backup['objects']:
		if config['name'] in scene.objects and config['id'] in unloaded:
			configure_object(scene.objects[config['name']], config)
			unloaded.pop(unloaded.index(config['id']))
	
	# release the game
	bge.logic.canstop -= 1
	thread_loader_running = False
	
def callback_loader():
	thread = threading.Thread()
	thread.run = thread_loader
	thread.start()


def _loader_thread():
	global last_backup, loaded, unloaded, max_id
	filename = save_file
	try:  f = open(filename, 'r')
	except IOError:  print('error: backup file \"%s\" not found.' % filename)
	else:
		text = f.read()
		f.close()
		new_backup = eval(text)
		last_backup = new_backup
		max_id = last_backup['max id']

		# check for loaded ids
		bge.logic.canstop += 1
		for scene in bge.logic.getSceneList():
			if scene.name == "Scene":
				for obj in scene.objects:
					if 'id' in obj and obj['id'] not in loaded: loaded.append(obj['id'])
		bge.logic.canstop -= 1
		
		# remove last_backup IDs which are not in unloaded or in loaded objects
		for dataname in ('characters', 'vehicles', 'items', 'objects'):
			for i in range(len(last_backup[dataname])):
				id = last_backup[dataname][i]['id']
				if id not in loaded and id not in unloaded:
					unloaded.append(id)
			for character in last_backup['characters']:
				for item in character['inventory'].values():
					if (item != None) and (item[0] not in loaded) and (item[0] not in unloaded):
						unloaded.append(item[0])

def loadbackup(filename, async=True):
	# create a new thread, because no error should stop the current thread
	global save_file
	save_file = filename
	if async:
		t = threading.Thread()
		t.run = _loader_thread
		t.start()
	else:
		_loader_thread()


def savebackup(filename=None):
	if filename == None: filename = save_file
	try:  f = open(filename, 'w')
	except IOError:  print('error: unable to write backup file \"%s\"' % filename)
	else:
		f.write(pprint.pformat(last_backup))
		f.close()

def callback_saver():
	if autosave:
		savebackup(save_file)
