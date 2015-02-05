######################################################
#
#    Mirror.py        Blender 2.5
#
#    Tutorial for using Mirror.py can be found at
#
#    www.tutorialsforblender3d.com
#
#    Released under the Creative Commons Attribution 3.0 Unported License.	
#
#    If you use this code, please include this information header.
#
######################################################

# import bge module
import bge

# get the current controller
controller = bge.logic.getCurrentController()

# get object script is attached to
obj = controller.owner

# check to see variable Mirror has been created
if "Mirror" in obj:
	# update the mirror
	obj["Mirror"].refresh(True)

# if variable Mirror hasn't been created
else:

	# get current scene
	scene = bge.logic.getCurrentScene()

	# get the mirror material ID
	matID = bge.texture.materialID(obj, "MA" + obj['material'])

	# get the active camera
	cam = scene.active_camera 
			
	# texture channel
	if 'channel' in obj:
		
		# set texture channel
		texChannel = obj['channel']
	
	else:
		
		# use texture channel 1
		texChannel = 0

	# get the mirrortexture
	mirror = bge.texture.Texture(obj, matID, texChannel)
	
	# get the mirror source
	mirror.source = bge.texture.ImageMirror(scene, cam, obj, matID)
	mirror.source.capsize =  [2000, 2000]

	# save mirror as an object variable
	obj["Mirror"] = mirror
	