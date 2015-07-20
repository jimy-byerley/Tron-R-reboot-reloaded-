import bge
from character import *
import backup_manager as bm
import pickle, time


class NetCharacter(Character):
	"""
	Represent a character PNJ or not.
	"""
	look_sync   = 0
	way_sync    = 0
	jump_sync   = 0
	run_sync    = 0
	drop_sync   = 0
	wield_sync  = 0
	helmet_sync = 0
	hp_sync     = 0
	
	def spawn(self, ref=None, existing=None):
		Character.spawn(self, ref, existing)
		client = bge.logic.client
		client.sync_physic(self.box)
		client.sync_property(self.box, 'active')
		client.sync_property(self.box, 'move speed')
		client.sync_property(self.box, 'hp')
	
	def lookAt(self, rotEuler):
		if time.time() < self.look_sync:
			bge.logic.client.queue.append(b'character\0look\0'+ str(bm.get_object_id(self.box)).encode() +b'\0'+ pickle.dumps(rotEuler[:]))
			self.look_sync = time.time() + bge.logic.client.update_period
		Character.lookAt(self, rotEuler)
	
	def takeWay(self, orient):
		if time.time() < self.way_sync:
			bge.logic.client.queue.append(b'character\0way\0'+ str(bm.get_object_id(self.box)).encode() +b'\0'+ str(orient).encode())
			self.way_sync = time.time() + bge.logic.client.update_period
		Character.takeWay(self, orient):
	
	def updateJump(self, jump=True):
		if time.time() < self.jump_sync:
			bge.logic.client.queue.append(b'character\0jump\0'+ str(bm.get_object_id(self.box)).encode())
		Character.updateJump(self, jump)
	
	def updateRunning(self, speed):
		if time.time() < self.run_sync:
			bge.logic.client.queue.append(b'character\0run\0'+ str(bm.get_object_id(self.box)).encode() +b'\0'+ speed)
			self.run_sync = time.time() + bge.logic.client.update_period
		Character.updateRunning(self, speed)

	def drop(self):
		if time.time() < self.drop_sync:
			bge.logic.client.queue.append(b'character\0drop\0'+ str(bm.get_object_id(self.box)).encode())
			self.drop_sync = time.time() + bge.logic.client.update_period
		Character.drop(self)
	