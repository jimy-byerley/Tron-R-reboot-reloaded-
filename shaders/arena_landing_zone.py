from bge import logic as g
from bge import texture
from mathutils import *
from math import *
import bgl

cont = g.getCurrentController()
own = cont.owner
scene = g.getCurrentScene()
objlist = scene.objects

reflsize = 512 #reflection tex dimensions
refrsize = 512 #refraction tex dimensions
offset = 200.0 #geometry clipping offset

#texture background color
bgR = 0.02
bgG = 0.02
bgB = 0.02
bgA = 0.0

activecam = scene.active_camera
viewer = activecam
watercamera = objlist['reflectcamera'] #camera used for rendering the water

#setting lens and projection to watercamera
watercamera.lens = activecam.lens
watercamera.projection_matrix = activecam.projection_matrix

#rotation and mirror matrices
m1=Matrix(own.orientation)
m2=Matrix(own.orientation)
m2.invert()

r180 = Matrix.Rotation(radians(180),3,'Y')
unmir = Matrix.Scale(-1,3,Vector([1,0,0]))

#disable visibility for the water surface during texture rendering
own.visible = False

###REFLECTION####################

#initializing camera for reflection pass
pos = (viewer.position - own.position)*m1
#watercamera.near = abs((watercamera.position - own.position - pos*r180*unmir*m2).z/2)
watercamera.position = own.position + pos*r180*unmir*m2
ori = Matrix(viewer.orientation)
ori.transpose()
ori = ori*m1*r180*unmir*m2
ori.transpose()
watercamera.orientation = ori

#culling front faces as the camera is scaled to -1
bgl.glCullFace(bgl.GL_FRONT)

#plane equation
normal = own.getAxisVect((0.0, 0.0, 1.0)) #plane normals Z=front

D = -own.position.project(normal).magnitude #closest distance from center to plane
V = (activecam.position-own.position).normalized().dot(normal) #VdotN to get frontface/backface

#invert normals when backface
if V<0:
	normal = -normal


#making a clipping plane buffer
plane = bgl.Buffer(bgl.GL_DOUBLE, [4], [-normal[0], -normal[1], -normal[2], -D+offset])
bgl.glClipPlane(bgl.GL_CLIP_PLANE0, plane)
bgl.glEnable(bgl.GL_CLIP_PLANE0)

#rendering the reflection texture in tex channel 0
if not hasattr(g, 'arena_landing_zone'):
	g.arena_landing_zone = texture.Texture(own, 0, 0)
	g.arena_landing_zone.source = texture.ImageRender(scene,watercamera)
	g.arena_landing_zone.source.capsize = [reflsize,reflsize]
	g.arena_landing_zone.source.background = [int(bgR*255),int(bgG*255),int(bgB*255),int(bgA*255)]

g.arena_landing_zone.refresh(True)

#restoring face culling to normal and disabling the geometry clipping
bgl.glCullFace(bgl.GL_BACK)
bgl.glDisable(bgl.GL_CLIP_PLANE0)

own.visible = True
