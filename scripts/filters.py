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
import Rasterizer

FILTER_SHORTNAME = 0
FILTER_FILE      = 1
FILTER_LONGNAME  = 2
FILTER_DESC      = 3

# list of existing 2D filters, ordered by pass order on the GPU
# each item is of type:     short name,  file,  long name,  description
filters = [
	("FXAA",  "FXAA.glsl", "screen antiliasing",
	           "Will reduce a lot liasing due to openGL."),
	
	("SSAO",  "SSAO.glsl", "ambient occlusion",
	           "Improve ambient occlusion: occlusion of indirect lights due to objects's materials diffusion."),
	
	("bloom", "bloom.glsl",  "light glow",
	           "All luminescent line or white objects will be outlined by a gradiant of the same color (GPU consumpting)."),
	
	("field depth (simple)", "field_depth.glsl", "glow background and foreground",
	           "Objects that have not the focus will be glowed, as if there was a true camera, with optics.\
At contrary of other field depth effects, objects thaht have not the focus are glowed."),
	
	("field depth (pentagon)", "field_depth_pentagon.glsl", "glow background and foreground",
	           "Objects that have not the focus will be glowed, as if there was a true camera, with optics.\
At contrary of other field depth effects, objects that have not the focus appears in multiple pentagons."),
	
	("field depth (ring)", "field_depth_ring.glsl", "glow background and foreground",
	           "Objects that have not the focus will be glowed, as if there was a true camera, with optics.\
At contrary of other field depth effects, objects that have not the focus appears as rings (no light inside, circle of light)."),
	
	("history mode", "history_mode.glsl", "warp border of screen",
	           "History mode is as the flashback in tron legacy: It warp image on the sides of the screen and difract the colors."),
	
	# don't use theses
	("pause menu", "pause_menu.glsl", "darken the screen for the pause menu", ""),
]

enabled = []    # list of filters enabled (short names)

# add filter names to theses lists to enable/disable it. One filter only will be applied by logic step and removed from this list.
# filters to disable would be treated first.
to_enable = []  # list of filters to enable (will automaticaly enable, 1 per logic step)
to_disable = [] # list of filters to disable (will automaticaly disable, 1 per logic step)

def enable_filter(name):
	global to_enable
	to_enable.append(name)
	bge.logic.root['set_filter'] = True

def disable_filter(name):
	global to_disable
	to_disable.append(name)
	bge.logic.root['set_filter'] = True


def callback_update(cont):
	owner = cont.owner
	# disable first to avoid overload of the GPU during the steps filters are changed.
	if to_disable:
		name = to_disable.pop(0)
		for i in range(len(filters)):
			if filters[i][FILTER_SHORTNAME] == name:
				print('module \"%s\": disable filter \'%s\'.' % (__name__, name))
				actuator = cont.actuators[0]
				actuator.mode = bge.logic.RAS_2DFILTER_DISABLED
				actuator.shaderText = ""
				actuator.passNumber = i
				cont.activate(actuator)
				break
	elif to_enable:
		name = to_enable.pop(0)
		for i in range(len(filters)):
			if filters[i][FILTER_SHORTNAME] == name:
				print('module \"%s\": enable filter \'%s\'.' % (__name__, name))
				filter_code = ""
				try: f = open(bge.logic.filters_path+'/'+filters[i][FILTER_FILE], 'r')
				except OSError: 
					print('module \"%s\": failed to set 2D filter \'%s\' (unable to open file \'%s\').' % (__name__, filters[i][name], bge.logic.filters_path+'/'+filters[i][FILTER_FILE]))
					return False
				else:
					filter_code = f.read()
					f.close()
				actuator = cont.actuators[0]
				actuator.mode = bge.logic.RAS_2DFILTER_CUSTOMFILTER
				actuator.shaderText = filter_code
				actuator.passNumber = i
				cont.activate(actuator)
				break
	else:
		owner['set_filter'] = False


def update_bloom_fac() :
	bge.logic.root['bloom_fac'] = 1.9/Rasterizer.getWindowWidth()
