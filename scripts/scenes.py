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
import math
import threading
import tools

scene_thread_loop_duration = 5  # (seconds) Set a smaller value if you want the loading and unloading of the scenes to be faster
distance_factor = 1. # change this factory to change the global distances to load the scenes, (if you have a bad computer)
scene_thread_stop = False

# indexes for 'scenes' list.
LOCATION = 0
FILE = 1
TEST = 2
DEPENDS = 3

######################################################################
### FONCTION CALLBACKS TO CHECK IF A SCENE SHOULD BE LOADED OR NOT ###

# the scene should always be loaded. use "all_the_time" in "scenes" list
def all_the_time():
	return True

# creates a routine that return True if the first player is above distance. use "on_distance(x)" in "scenes" list
def on_distance(distance):
	def new_ondistance(rule):
		camera = bge.logic.getCurrentScene().active_camera.worldPosition
		scene = rule[LOCATION]
		dist = math.sqrt((scene[0]-camera.x)**2 + (scene[1]-camera.y)**2 + (scene[2]-camera.z)**2)
		if dist < distance*distance_factor:
			return True
		return False
	return new_ondistance

# creates a routine that return True if the first player is above playerdistance and one of the scenes given in a list is loaded.
def on_distance_and_loaded(playerdistance, scenes):
	return False

#############################
### SCENES S DECLARATIONS ###

scenes = [
	# functions to decide of loading or not is a function as      
	#      func( rule ) -->  True or False (shoud be loaded or not). rule is the line as described bellow.
	# be carefull because scene dependencies of a dependency will also be loaded with its dependencies.
	# coordinates (xyz)    file name             function to decide of loading    list of dependencies (other scenes)
	((1000,0,0),    "small-arena-outside.blend",      on_distance(500),       ("system.blend",)),
	((0,0,0),       "town-part-00.blend",             on_distance(100),        ("system.blend",)),
	((50,0,0),      "town-part-01.blend",             on_distance(100),        ("system.blend",)),
	((0,0,0),       "system.blend",                   None,                   ()),
]



flag = 0
thread_loader_running = False
def thread_loader():
	global flag
	global thread_loader_running
	
	# uniq instance possible
	if thread_loader_running: return
	thread_loader_running = True
	bge.logic.canstop += 1 # the game could not be stopped, except if canstop is equal to 0
	
	# wait until the BGE is initialized
	if flag == 0:
		time.sleep(0.2)
		flag = 1
	
	to_load = [False] * len(scenes)
	for i in range(len(scenes)):
		# if no scene is depending on
		if not to_load[i]:
			test = scenes[i][TEST]
			if test != None: to_load[i] =  test(scenes[i])
		# if the scene is to be loaded, add dependencies
		if to_load[i]:
			for name in scenes[i][DEPENDS]:
				for j in range(len(scenes)):
					if j != i and scenes[j][FILE] == name:
						to_load[j] = True
						
	# load scene or unload it
	liblist = bge.logic.LibList()
	for i in range(len(to_load)):
		libname = bge.logic.expandPath(bge.logic.scene_path+'/'+scenes[i][FILE])
		if to_load[i] and (libname not in liblist) :
			print("module \"%s\": load scene \"%s\" ..." % (__name__, libname))
			bge.logic.LibLoad(libname, "Scene", load_actions=True, load_scripts=True, async=False)
			time.sleep(1)
			#tools.LibLoad(libname, "Scene", load_actions=True, load_scripts=True, async=True)
		
		elif (not to_load[i]) and (libname in liblist) :
			#print("module \"%s\": unload scene \"%s\" ..." % (__name__, libname))
			#bge.logic.LibFree(libname)
			# blender crashes when libfree
			pass
	
	# release the game
	bge.logic.canstop -= 1
	# exit uniq instance
	thread_loader_running = False

def callback_loader():
	thread = threading.Thread()
	thread.run = thread_loader
	thread.start()
		

