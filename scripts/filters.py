import bge

FILTER_SHORT_NAME = 0
FILTER_FILE       = 1
FILTER_LONG_NAME  = 2
FILTER_DESC       = 3

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
]

# list of filters enabled (short names)
enabled = []

# add a filter for the GPU render, filter is specified by its name in 'filters' list.
# only one filter can be set or removed per logic step
def enable_filter(name):
	for i in range(len(filters)):
		if filters[i][FILTER_SHORTNAME] == name:
			filter_code = ""
			try: f = open(bge.logic.filters_path+'/'+filters[i][FILTER_FILE], 'ro')
			except OSError: 
				print('failed to set 2D filter \'%s\'' % filters[i][FILTER_SHORTNAME])
				return False
			else:
				filter_code = f.read()
				f.close()
			actuator = bge.logic.root.actuators['2Dfilter']
			actuator.mode = bge.logic.RAS_2DFILTER_CUSTOMFILTER
			actuator.shaderText = filter_code
			actuator.passNumber = i
			bge.logic.root['set_filter'] = True
			return True
	return False

# remove a filter for the GPU render, filter is specified by its name in 'filters' list.
# only one filter can be set or removed per logic step
def disable_filter(name):
	for i in range(len(filters)):
		if filters[i][FILTER_SHORTNAME] == name:
			actuator = bge.logic.root.actuators['2Dfilter']
			actuator.mode = bge.logic.RAS_2DFILTER_DISABLED
			actuator.shaderText = ""
			actuator.passNumber = i
			bge.logic.root['set_filter'] = True
			return
