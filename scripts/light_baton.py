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

from item import *
from vehicle import *
import time
import bge
from bge.logic import *
from mathutils import *
from math import *
import threading
import aud

anim_frame_time = 1/24.  # time of animation frame

class LightBaton(Item):
	cycle = None
	next_action1 = 0.
	next_action2 = 0.
	
	colors = { # meshes for color
		'blue' : 'light baton blue',
		'red' : 'light baton red',
		'orange' : 'light baton orange',
		'white' : 'light baton white',
		'green' : 'light baton green',
		}
	
	cyclecolors = { # meshes for cycle color
		'blue' : 'cycle body blue',
		'red' : 'cycle body red',
		'orange' : 'cycle body orange',
		'white' : 'cycle body white',
		'green' : 'cycle body green',
		}
	
	def init(self):
		Item.init(self)
		if "color" in self.object:
			self.changeColor(self.object['color'])

	def taken(self):
		Item.taken(self)
		self.changeColor(self.getOwner().getColor())
		self.next_action1 = self.next_action2 = time.time()
	
	def action1(self):
		if self.next_action1 > time.time(): return
		else: self.next_action1 = time.time() + 0.5
		if self.cycle :
			# play sound
			path = bge.logic.sounds_path+'/light-vehicles/cycle-stop.wav'
			sound = aud.Factory.file(path)
			dev = aud.device()
			cam = bge.logic.getCurrentScene().active_camera
			vec = self.getOwnerObject().worldPosition - cam.worldPosition
			dev.listener_location = vec
			dev.volume = 0.1
			dev.play(sound)
			
			holo = self.object.children[0]
			holo.visible = True
			self.cycle['class'].remove(netsync=False)
			self.cycle = None
			holo.playAction("light baton prototype", 10, 0)
			def t():
				time.sleep(anim_frame_time*8)
				holo.visible = False
			thread = threading.Thread()
			thread.run = t
			thread.start()
			
		else :
			# play sound
			path = bge.logic.sounds_path+'/light-vehicles/cycle-start.wav'
			sound = aud.Factory.file(path)
			dev = aud.device()
			cam = bge.logic.getCurrentScene().active_camera
			vec = self.getOwnerObject().worldPosition - cam.worldPosition
			dev.listener_location = vec
			dev.volume = 0.1
			
			# spawn the cycle
			skin = self.getOwner().skin
			armature = skin.armature
			anim = skin.animations["set cycle"]
			armature.playAction(anim[0], anim[1], anim[4], layer=1)
			hologram = self.object.children[0]
			def t():
				time.sleep(abs(anim[1]-anim[3])*anim_frame_time)
				hologram.visible = True
				hologram.playAction("light baton prototype", 0, 10)
				dev.play(sound)
				time.sleep(anim_frame_time*8)
				scene = bge.logic.getCurrentScene()
				self.cycle = scene.addObject("light-cycle", self.getOwnerObject())
				self.cycle.worldLinearVelocity = self.getOwnerObject().worldLinearVelocity
				self.cycle['class'] = LightCycle(self.cycle, "light cycle")
				self.cycle['class'].init()
				self.cycle['class'].enter(self.getOwnerObject(), self.cycle['class'].driversplace)
				hologram.visible = False

			thread = threading.Thread()
			thread.run = t
			thread.start()
	
	def action2(self):
		if self.next_action2 > time.time(): return
		else: self.next_action2 = time.time()+0.5
		if self.cycle: 
			if 'uniqid' in self.cycle: print(self.cycle['uniqid'])
			self.cycle['class'].set_trail(not self.cycle['class'].trail)


def item_init():
	cont = bge.logic.getCurrentController()
	owner = cont.owner

	owner['class'] = LightBaton(owner, owner["itemname"], owner["hand"], owner["attach"])
	owner['class'].init()



## TRAIL AND VEHICLE SECTION ##

trail_precision = 1.0 # (meters)


def putshaderuniform(shader, p, i):
	shader.setUniform3f('p'+str(i), p[i][0], p[i][1], p[i][2])

def update_trail(cont):
	owner = cont.owner
	marker = owner['marker']
	path = owner['path']
	trail_len = int(owner['len']/trail_precision)
	
	p = marker.worldPosition - path[1]
	dist = sqrt(p.x**2 + p.y**2 + p.z**2)
	if dist > trail_precision :
		path.pop(-1)
		path[0] = marker.worldPosition.copy()
		path.insert(0, marker.worldPosition) # position as a pointer
		for i in range(trail_len):
			putshaderuniform(owner['shader'], path, i)
	else:
		putshaderuniform(owner['shader'], path, 0)


def add_trail(marker, length=100):
	trail = bge.logic.getCurrentScene().addObject("light trail")
	mesh = trail.meshes[0]
	mat = mesh.materials[0]
	trail_len = int(length/trail_precision)
	
	trail['len'] = length
	trail['marker'] = marker
	trail['path'] = [trail.position] * trail_len
			
	if not 'shader' in trail:
		shader = trail['shader'] = mat.getShader()
	if not shader.isValid():
		# declaration on positions
		uniforms = 'p0, p1'
		for i in range(2, trail_len):
			uniforms += ', p'+str(i)
		# selection of position to use
		selecter = '\tif (I >= -%f) pos = p0;\n' % (1/float(trail_len),)
		for i in range(trail_len):
			selecter += '\tif (I >= -%f && I < -%f)  pos = p%d;\n' % ((i+1)/float(trail_len), i/float(trail_len), i)
		# setting shader
		vertex = trail_vertex % (uniforms, selecter)
		shader.setSource(vertex, trail_fragment, 1)
		shader.setSampler("tex_emit", 0)
		shader.setUniform1f('len', trail_len)
		
		for i in range(trail_len):
			putshaderuniform(shader, trail['path'], i)
	
	return trail
	    
	
trail_vertex = """
uniform vec3 %s;
varying vec2 Texcoord;
varying float dist;

void main(){
	float I = gl_Vertex.y;
	vec3 pos = gl_Vertex.xyz;
%s
	gl_Position = gl_ModelViewProjectionMatrix * vec4(pos.x+gl_Vertex.x, pos.y, pos.z+gl_Vertex.z, gl_Vertex.a);
	Texcoord = gl_MultiTexCoord0.xy;

	dist = length(p0-p1);
}

"""

trail_fragment = """


uniform sampler2D tex_emit;
varying vec2 Texcoord;
varying float dist;
uniform float len;

void main()
{
	vec4 trail_tex = texture2D(tex_emit, vec2(Texcoord.x+dist,Texcoord.y)).rgba;
	vec3 color = trail_tex.rgb * vec3(0.4, 0.8, 1) * 2;
	float alpha = float(Texcoord.x) - dist/len;
	gl_FragColor = vec4(color*alpha, alpha);
}
"""


class LightCycle(Vehicle):
	# vehicle caracteristics
	max_speed = 55    # m/s  (~ 200 km/h)
	max_yaw = pi/4     # rad/m
	max_accel = 20     # maximum acceleration m/s^2
	
	reach_stability = 0.1  # second
	reach_yaw = 0.1
	reach_tilt = 0.6
	
	animup = 10
	trail = None
	
	def enter(self, character, place, netsync=True):
		Vehicle.enter(self, character, place, netsync)
		armature = self.driver['class'].skin.armature
		# anim player to in vehicle position
		anim = self.driver['class'].skin.animations['set cycle']
		armature.playAction(anim[0], anim[4], anim[4], layer=0, play_mode=KX_ACTION_MODE_LOOP)
		for child in self.object.children:
			if "head_pos" in child:
				self.headpos = child
		head = self.driver['class'].camera_head
		self.oldheadpos = head.localPosition.copy()
		head.worldPosition = self.headpos.worldPosition
		mesh = self.body.meshes[0]
		'''# unfortunatly crashing on material.getShader()
		for matid in range(mesh.numMaterials):
			if mesh.getMaterialName(matid) == 'MAcycle body white':
				shader = mesh.materials[matid].getShader() # crashing on getShader
				if shader != None :
					vertfile = open(bge.logic.shaders_path+'/standard.vert', 'r')
					fragfile = open(bge.logic.shaders_path+'/light-cycle.frag', 'r')
					shader.delSource()
					shader.setSource(vertfile.read(), fragfile.read())
					vertfile.close()
					fragfile.close()
					shader.setSampler('emit', 4)
					shader.setUniform3f('color', 1.0, 1.0, 1.0, 1.0)
					shader.validate()
		'''

	def init(self):
		Vehicle.init(self)
		for child in self.object.children:
			if "floor sensor" in child:  self.floor = child
			if "front sensor" in child:  self.front = child
			if "armature" in child:      self.armature = child
			if "trail marker" in child:  self.trail_marker = child
		for child in self.armature.children:
			if "body" in child:
				self.body = child
		self.timer = time.time()
		
	def exit(self, character, netsync=True):
		head = character['class'].camera_head
		head.localPosition = self.oldheadpos
		self.driver['class'].update_TPV_distance(bge.logic.config['game_tpv_distance'])
		Vehicle.exit(self, character, netsync)

	def updateControl(self, speed, yaw, breaks, netsync=True):
		if speed > self.max_speed:    speed = self.max_speed
		elif speed < 0:               speed = 0
		if yaw > self.max_yaw: yaw = self.max_yaw
		if yaw < -self.max_yaw: yaw = -self.max_yaw
		self.object['speed']  = speed
		self.object['yaw']    = yaw
		self.object['breaks'] = breaks
		Vehicle.updateControl(self, speed, yaw, breaks, netsync)
	
	def set_trail(self, active=True):
		if self.trail and not active:
			self.trail.endObject()
			self.trail = None
			bge.logic.getCurrentScene().active_camera.frustum_culling = True
		elif not self.trail and active:
			self.trail = add_trail(self.trail_marker)
			bge.logic.getCurrentScene().active_camera.frustum_culling = False
	
	def remove(self, netsync=False):
		self.set_trail(False)
		Vehicle.remove(self, netsync)


def cycle_init(cont):
	owner = cont.owner
	owner['class'] = LightCycle(owner, owner["vehiclename"])
	owner['class'].init()

def cycle_update(cont):
	object = cont.owner
	cycle = object['class']
	onfloor = cycle.floor.sensors[0].status
	
	speed  = object['speed']
	yaw    = object['yaw']
	breaks = object['breaks']

	velocity = object.localLinearVelocity
	orientation = object.localOrientation.to_euler()
	angular = object.localAngularVelocity
	mass = object.mass
	
	if cycle.driver:
		cycle.driver['class'].update_TPV_distance(bge.logic.config['game_tpv_distance']+velocity.magnitude/4)
	
	if onfloor in (KX_INPUT_JUST_ACTIVATED, KX_INPUT_ACTIVE):
		# acceleration
		if speed < velocity.y:
			acceleration = -cycle.max_accel/10
		elif speed > velocity.y:
			acceleration = cycle.max_accel
		propulsion = mass * acceleration
		lateral_force = -mass * velocity.x / cycle.reach_stability
		
		if breaks and velocity.y > 0: 
			yaw *= 2
			propulsion = -mass * cycle.max_accel
		
		# tilt rotation
		if yaw > 0.1:    inclin = -pi/5
		elif yaw < -0.1: inclin = pi/5
		else:            inclin = 0
			
		tilt = (inclin - orientation.y) / cycle.reach_tilt
		
		# yaw speed
		if yaw > 0: yaw = min(cycle.max_yaw*velocity.y, yaw)
		else:       yaw = max(-cycle.max_yaw*velocity.y, yaw)
		
		# apply physic changes
		object.applyForce((lateral_force, propulsion, 0.), True)
		#object.applyTorque((0., sin(orientation.y)*torque_yaw, cos(orientation.y)*torque_yaw), True)
		object.localAngularVelocity.y = tilt
		#object.localAngularVelocity.x = yaw * sin(orientation.y)
		object.localAngularVelocity.z = yaw * cos(orientation.y)
		
		# update wheels animation with vehicle speed
		if cycle.animup == 20:
			cycle.animup = 0
			s = 7*velocity.y / cycle.max_speed
			current = cycle.armature.getActionFrame(0)%60
			cycle.armature.playAction("light cycle running", current, current+59, speed=s, layer=0, play_mode=KX_ACTION_MODE_LOOP)
		else : cycle.animup += 1
