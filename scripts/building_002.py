import bge
from bge import texture
from mathutils import *
from math import *
import bgl

EH_down = 3.3655
EH_up   = 30.7482

def elevator_hall(cont):
	collision = cont.sensors[0]
	
	elevator = cont.owner.parent.parent
	target = elevator["target"]
	pos = elevator.localPosition
	if collision.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
		cont.owner.parent.visible = True
		if abs(pos.z-EH_up) < 0.1 and target == 0:
			target = EH_down
		elif abs(pos.z-EH_down) < 0.1 and target == 0:
			target = EH_up
	elif collision.status == bge.logic.KX_SENSOR_JUST_DEACTIVATED:
		cont.owner.parent.visible = False
	if target != 0:
		if elevator_goto_step(elevator, target):
			target = 0
	elevator["target"] = target
	

def elevator_goto_step(obj, altitude):
	mover = obj.actuators['Motion']
	objz = obj.localPosition.z
	if objz-altitude < -0.1 :
		mover.dLoc = (0, 0, 0.1)
		obj['move'] = True
		return False
	elif objz-altitude > 0.1 : 
		mover.dLoc = (0, 0, -0.1)
		obj['move'] = True
		return False
	else:
		obj['move'] = False
		return True
		


def near_chair(cont):
	owner = cont.owner
	if "ob_chair" not in owner:
		for obj in owner.parent.children:
			if "chair" in obj and obj["chair"]:
				owner["ob_chair"] = obj
	if "ob_chair" in owner:
		for obj in cont.sensors[0].hitObjectList:
			if "character"in obj:
				angle = owner.getAxisVect((1,0,0)).angle(obj.worldPosition-owner.worldPosition, 0)
				if angle > pi/4:
					owner["ob_chair"].localOrientation -= Euler((0,0,pi/40))
				elif angle < -pi/4:
					owner["ob_chair"].localOrientation += Euler((0,0,pi/40))
				break


def hall_mirror_init(cont):
	owner = cont.owner
	scene = bge.logic.getCurrentScene()
	reflectcam = scene.objects['reflectcamera']
	
	m = texture.Texture(owner, 5, 1)
	m.source = texture.ImageRender(scene, reflectcam)
	m.source.capsize = [512, 512]
	m.source.background = [0,0,0,0]
	owner["mirror"] = m

def hall_mirror_step(cont):
	owner = cont.owner
	scene = bge.logic.getCurrentScene()
	activecam = scene.active_camera
	reflectcam = scene.objects['reflectcamera']
	offset = 200.0 #geometry clipping offset

	reflectcam.lens = activecam.lens
	reflectcam.projection_matrix = activecam.projection_matrix

	m1 = owner.orientation
	m2 = owner.orientation
	m2.invert()
	r180 = Matrix.Rotation(pi, 3, 'Y')
	unmir = Matrix.Scale(-1, 3, Vector((1,0,0)))

	owner.visible = False
	
	# set reflect camera
	pos = (activecam.position - owner.position) * m1
	reflectcam.position = owner.position + pos*r180*unmir*m2
	ori = Matrix(activecam.orientation)
	ori.transpose()
	ori = ori * m1 * r180 * unmir * m2
	ori.transpose()
	reflectcam.orientation = ori
	
	# invert face culling
	bgl.glCullFace(bgl.GL_FRONT)
	
	# plane equation
	normal = owner.getAxisVect((0,0,1))
	dist = -owner.position.project(normal).magnitude   # distance to plane
	v = (activecam.position - owner.position).normalized().dot(normal)  # face culling
	
	# invert normals when backface
	if v<0:  normal = -normal
	
	# making a clipping plane buffer
	plane = bgl.Buffer(bgl.GL_DOUBLE, [4], [-normal[0], -normal[1], -normal[2],  offset-dist])
	bgl.glClipPlane(bgl.GL_CLIP_PLANE0, plane)
	bgl.glEnable(bgl.GL_CLIP_PLANE0)
	
	# rendering the reflection texture
	owner['mirror'].refresh(True)
	
	# restoring face culling to normal and disabling the geometry clipping
	bgl.glCullFace(bgl.GL_BACK)
	bgl.glDisable(bgl.GL_CLIP_PLANE0)
	owner.visible = True