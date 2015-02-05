from lib import libbuild
import os

local_path = '/'.join(__file__.split('/')[1:-1])
blend_file = "/disk.blend"

def addDisk(name, position) :
	"""Add a disk to the specified position, and rename it with the specified name."""
	print("load \""+local_path+blend_file+"\"")
	body = libbuild.addObject(name, local_path+blend_file, "disk body", position)
	lame = libbuild.addObject(name+" lame", local_path+blend_file, "disk lame", position)
	halo = libbuild.addObject(name+" halo", local_path+blend_file, "disk halo", position)
	# parenty section
	lame.setParent(body)
	halo.setParent(body)
	# properties section
	lame["arme"] = False
	body["flying"] = False
	body["arme"] = False
	# dynamics section
	body.restoreDynamics()
	body.enableRigidBody()
	
	return body
