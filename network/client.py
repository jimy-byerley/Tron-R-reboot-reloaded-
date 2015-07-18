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
import threading, socket, time, pickle
from network import *
import backup_manager as bm


def get_object_id(kx_object):
	""" 
	Return the uniq ID of an object (character, item, ...) if the object's property
	"uniqid" is not defined, assign an unused id to this object. 
	"""
	if "uniqid" in kx_object : return kx_object["uniqid"]
	else :
		total = unloaded+loaded
		while bm.max_id in total:
			bm.max_id += 1
		i = bm.max_id
		kx_object["uniqid"] = i
		bm.max_id = bm.max_id+1
		# new part of the function: 
		if hasattr(bge.logic, 'client'):
			dump_type = 'object'
			if 'dump' in kx_object:
				dump_type = kx_object['dump']
			else:
				kx_object['dump'] = 'object'
			dump = dump_this(kx_object)
			bge.logic.client.queued.append(b'newobject\0'+ dump_type.encode() +b'\0'+ pickle.dumps(dump))
		return i

# replace standard function to access an object ID
bm.get_object_id = get_object_id


marker_property_physic   = "network_meca"   # set to True to enable synchronizationn of physic properties (velocity, angular, pos, rot, ...)
marker_property_property = "network_prop"   # can ba a tuple or a string, will be converted automatically in string during the game
											# a tuple contain the string names of the properties to sync
											# a string contain the string names of the properties to sync separated by spaces or punctuation.



def try_login(server, user, password):
	"""
	Test a login (username and password) on the server given by tuple (address, port).
	Return the error string message on fail, and empty string on success.
	"""
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.settimeout(10)
	s.connect(server)
	s.send(b'authentify\0'+ user.encode() +b'\0'+ password.encode())
	try: reponse = s.recv(1024)
	except socket.timeout:
		s.close()
		return 'timeout error'
	except ConnectionRefusedError:
		s.close()
		return 'connection refused'
	s.send(PACKET_STOP)
	s.close()
	if reponse == b'authentication\0password accepted':
		return ""
	else:
		try:
			return reponse.decode()
		except:
			return "reponse '%s' doesn't make sense" % repr(reponse)


# simple callback for the game use
def callback_thread_step():
	bge.logic.client.thread_step()



class Client(socket.socket):
	packet_size   = 1024     # max size of buffers to receive from the server
	update_period = 0.1      # minimum time interval between 2 update from the server, of objects positions
	step_time     = 0.05     # maximum time for each step
	# extendable list of properties to exclude of syncs (to avod security breachs)
	properties_blacklist = ["class","repr","armature", "uniqid", marker_property_physic, marker_property_property]
	
	synchronized = []        # list of objects to synchronize
	next_update  = 0         # next time to ask the server for update informations
	run          = False     # put it to False to stop the client execution stepn (automaticaly set to True on step start
	
	callbacks = []         # list of functions to call when a non-standard packet is received, function must 
	                       # take 2 parameters: the server instance and the packet received (bytes)
	                       # return True to erase the packet without executing other callbacks on it.
	                       # the callbacks are executed in the list order.
	
	queue = []             # list of packet to send after every threatment of incomming packet (send whenever 
	                       # there is no packet received)
	
	def __init__(self, remote, scene=None, user="", password=""):
		self.remote = remote
		self.username = user
		self.password = password
		self.scene = scene or bge.logic.getCurrentScene()
		socket.socket.__init__(self, socket.AF_INET, socket.SOCK_DGRAM)
		self.connect(remote)
		self.setblocking(False)
	
	def step(self):
		self.run = True
		bge.logic.canstop += 1 # the game could not be stopped, except if canstop is equal to 0
		end_step = time.time() + self.step_time
		while time.time() < self.next_update and time.time() < end_step and self.run:
			# recvfrom raise an error on no packet available
			try:    
				packet, host = self.recvfrom(self.packet_size)
				# only packets from the server are accepted (limit intrusion)
				while host != self.remote:   packet, host = recvfrom(self.packet_size)
			except socket.error or BlockingIOError: time.sleep(0.001)
			else:
				# words are separated by a \0 character
				words = packet.split(b'\0')
				# count number of '\0' in the packet, it indicates the minimal number of words in the packet
				zeros = len(words)
				# packet of kind:     getmeca.id
				if similar(packet, b'getmeca\0') and zeros >= 1:
					idbytes = words[1]
					if idbytes.isdigit():
						id = int(idbytes)
						obj = bm.get_object_by_id(self.scene, id)
						if obj:
							if obj.parent:  parent = obj.parent.name
							else:           parent = None
							msg = b'setmeca\0' + idbytes + b'\0' + pickle.dumps((
								obj.worldPosition[:],       obj.worldOrientation.to_euler()[:],
								obj.worldLinearVelocity[:], obj.worldAngularVelocity[:],
								parent))
							self.send(msg)
						else:
							self.send(b'unknown\0'+ idbytes)
				
				# packet of kind:     getprop.id.propname
				elif similar(packet, b'getprop\0') and zeros >= 2:
					idbytes, propname = words[1:3]
					if idbytes.isdigit():
						id = int(idbytes)
						obj = bm.get_object_by_id(self.scene, id)
						prop = propname.decode()
						if obj:
							if prop in self.scene.objects[ob] :
								msg = b'setprop\0' + idbytes + b'\0'+ propname + b'\0' + pickle.dumps(self.scene.objects[ob][prop])
								self.sendto(msg, host)
						else:
							self.send(b'unknown\0'+obname)
				
				# packet of kind:    setmeca.id.dump  ('\0' instead of .)
				elif similar(packet, b'setmeca\0') and zeros >= 1: 
					idbytes = words[1]
					if idbytes.isdigit():
						id = int(idbytes)
						obj = bm.get_object_by_id(self.scene, id)
						if obj:
							(obj.worldPosition,        obj.worldOrientation,
							obj.worldLinearVelocity,  obj.worldAngularVelocity,
							parent)     = pickle.loads(packet[9+len(obname):])
							obj.setParent(parent)
				
				# packet of kind:    setprop.id.propertyname.dump   ('\0' instead if .)
				elif similar(packet, b'setprop\0') and zeros >= 2:
					idbytes, propname = words[1:3]
					if idbytes.isdigit():
						id = int(idbytes)
						obj = bm.get_object_by_id(self.scene, id)
						prop = propname.decode()
						if obj and prop not in self.properties_blacklist:
							try: self.scene.objects[ob][prop] = pickle.loads(packet[10+len(obname)+len(propname):])
							except: pass
				
				# packet of kind:   changeid.IDsrc.IDdst
				elif similar(packet, b'changeid\0') and zeros >= 2:
					 idorigin, idtarget = words[1:3]
					 if idorigin.isdigit() and idtarget.isdigit():
						 idorigin, idtarget = int(idorigin), int(idtarget)
						 obj = get_object_by_id(self.scene, idorigin)
						 if obj: obj['uniqid'] = idtarget
				
				# packet of kind:    newobject.dumptype.dump
				elif similar(packet, b'newobject\0') and zeros >= 2:
					dumptype, dump = words[1:3]
					try: dump = pickle.loads(dump)
					except: pass
					else:
						dumptype = dumptype.decode()
						if 'id' in dump and dumptype in (bm.marker_character, bm.marker_item, bm.marker_vehicle, bm.marker_object) :
							bm.last_backup[dumptype] = dump
							bm.unloaded.append(dump['id'])
				
				
				elif similar(packet, b'authentication\0') and zeros >= 1:
					msg = words[1]
					try: debugmsg('server answered', msg.decode())
					except: pass
				
				elif similar(packet, PACKET_STOP):
					self.close()
					self.run = False
					return
				
				else:
					for callback in self.callbacks:
						try: 
							if callback(self, packet): break
						except: print('error in callback:', callback)
			
			# send queued, in the list order, one packet per packet received if the client receive.
			if self.queue:
				packet = self.queue.pop(0)
				try: self.send(packet)
				except: print('unable to send queued packet:', packet)
		
		
		if end_step > time.time() and self.run:
			for obj in self.synchronized:
				if obj :
					if marker_property_physic in obj and obj[marker_property_physic]:
						self.send(b'getmeca\0'+ str(bm.get_object_id(obj)).encode())
					if marker_property_property in obj:
						ok=True
						if type(obj[marker_property_property]) == str:
							try: obj[marker_property_property] = obj[marker_property_property].split()
							except:
								print("client.step: error on loading marker for network sync (property '%s') on object '%s', delete property." % (marker_property_property, obj.name))
								del obj[marker_property_property]
								ok=False
						if ok:
							for propname in obj[marker_property_property]:
								if propname not in self.properties_blacklist:
									self.send(b'getprop\0'+ str(bm.get_object_id(obj)).encode() +b'\0'+ propname.encode())
			
			self.next_update = time.time() + self.update_period
		bge.logic.canstop -= 1
		
	
	def thread_step(self):
		self.thread = threading.Thread()
		self.thread.run = self.step
		self.thread.start()
	
	def authentify(self, username='', password=''):
		self.username = username or self.username
		self.password = password or self.password
		self.sendto(b'authentify\0'+ self.username.encode() +b'\0'+ self.password.encode(), self.remote)
	
	# clear the socket's queue, return the list of packet received
	def clear_requests(self):
		queue = []
		received=b'\0'
		while len(received):
			received = self.recv()
			queue.append(received)
		return queue
	
	def stop(self):
		self.run = False
		self.send(PACKET_STOP)
