import bge

bge.logic.mirrors = {}
pi = 3.14159

def mirror_init():
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	scene = bge.logic.getCurrentScene()
	#cam = scene.active_camera
	cam = scene.objects['Camera']
	matId = bge.texture.materialID(owner, 'MAstreet junction floor')
	channel = 4
	bge.logic.mirrors[owner] = bge.texture.Texture(owner, matId, channel)
	bge.logic.mirrors[owner].source = bge.texture.ImageMirror(scene, cam, owner, matId)
	#bge.logic.mirrors[owner].source = bge.texture.ImageRender(scene, cam)

def mirror_update():
	owner = bge.logic.getCurrentController().owner
	scene = bge.logic.getCurrentScene()
	
	accam = scene.active_camera
	cam = scene.objects['Camera']
	cam.worldPosition = accam.worldPosition
	#rot = accam.worldOrientation.to_euler()
	#rot.x = pi/8
	#rot.x = 0
	#rot.y = 0
	#cam.worldOrientation = rot
	bge.logic.mirrors[owner].refresh(True)