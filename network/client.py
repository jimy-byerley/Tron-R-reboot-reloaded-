# -*- coding:utf-8 -*-

from basic_connection import *
import bge
from time import *


class GameClient(Client):
	_end = False
	queue = [] # list of packets to send
	addons = [] # list of couple (function, executestep)
	addons_steps = [] # list of next loop steps to execute addon
	loopstep = 0 # counter of thread steps
	
	
	# authentifie le client vis a vis du serveur
	def login(self):
		pass
	
	# tell to client to sychronize the objet location in realtime, the client tell the server to do it.
	# kxobject is a KX_GameObject
	def registerLocationUpdate(self, kxobject):
		self.queue.append('registerloc\0'+str(kxobject))
	
	def registerRotationUpdate(self, kxobject):
		self.queue.append('registerrot\0'+str(kxobject))
	
	def registerPropertyUpdate(self, kxobject, propertyname):
		self.queue.append('registerprop\0%s\0%s' % (str(kxobject), propertyname))
	
	# register a function to execute each loopcount loop step, this function should not take parameters and return a True value if the packet is usefull
	def registerAddon(self, function, loopcount):
		self.addons.append((function, loopcount))
		self.addons_steps.append(self.loopstep+loopcount)
	
	# termine la boucle principale du client
	def end(self):
		self._end = True
	
	def run(self):
		self.addons_steps = [0] * len(self.addons)
		self.loopstep = 0
		
		while not self._end:
			# send all methods requests
			print('send queued')
			for i in range(len(self.queue)):
				print('queue') ## THE PROGRAM DOESN'T EXECUTE THIS LINE BEFORE THE GAME HAS CRASHED
				self.send(self.queue[0])
				self.queue.pop(0)
			print('receiving')
			packet = self.getpacket()
			if packet :
				print('confirmed')
				p = packet.split('\0')
				delete = True
				com = p[0]
				scene = bge.logic.getCurrentScene()
				if com == 'setloc':
					pos = (float(p[1]), float(p[2]), float(p[3]))
					scene.objects[p[4]] = pos
				elif com == 'setrot':
					rot = (float(p[1]), float(p[2]), float(p[3]))
					scene.objects[p[4]] = rot
				elif com == 'setparent':
					scene.objects[p[1]].setParent(scene.objects[p[2]])
				elif com == 'setprop':
					scene.objects[p[1]][p[2]] = val(p[3])
				elif com == 'requestinfo':
					if p[1] not in scene.objects: self.send('unavailable')
					else :
						self.send('available')
						obj = scene.objects[p[1]]
						while True:
							p = self.getpacket().split('\0')
							delete = True
							com = p[0]
							if com == 'getloc':
								pos = obj.worldPosition
								self.send('%d\0%d\0%d' % (pos.x, pos.x, pos.x))
							elif com == 'getrot':
								rot = obj.worldOrientation
								self.send('%d\0%d\0%d' % (rot.x, rot.y, rot.z))
							elif com == 'getparent':
								self.send(obj.parent.name)
							elif com == 'getprop':
								if p[1] in obj:
									self.send(str(obj[p[1]]))
								else: self.send('error: property not found')
							elif com == 'endinfo':
								break
							else:
								print('error unknown request '+repr(com))
								delete = False
							if delete : self.clearpacket()
						delete = False # don't remove next packet (not read)
				else:
					delete = False
					# execute all addons and delete the current packet if one of the addons return a true value
					for i in range(len(self.addons)):
						if self.addons_steps[i] == self.loopstep:
							func, step = self.addons[i]
							self.addons_steps[i] += step
							res = False
							try: res |= func(packet)
							except: print('error when executing addon %s, loopstep %d' % (str(func), self.loopstep))
							if res: delete = True
				if delete: self.clearpacket()
			
			self.loopstep += 1
			sleep(0.02)

def val(s):
	v = None
	try : v = int(s)
	except :
		try: v = float(s)
		except:
			low = s.lower()
			if low == 'true':
				return True
			elif low =='false':
				return False
			else: return s
	return v