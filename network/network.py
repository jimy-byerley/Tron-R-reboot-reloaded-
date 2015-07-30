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

# python defined
import threading, socket, time, pickle, copy
# from the game
import ip_addr

debug = True
def debugmsg(*args):
	if debug: print(*args)

def similar(s, pattern) :        
	return s[:len(pattern)] == pattern

def username_conformity_off(_, s) : 
	return True



PACKET_STOP    = b"quitting\0"

class obdata:
	"""
	This class represents an object for the server (most common attributes are pre-defined for optimisation)
	"""
	host = 0               # maximal index of host who can provide information about this object
	updated = False        # marker for 'updated during last cycle'
	
	physics = False     # dump of physics properties of the object, False means physic properties not synchronized, can be None when sync is imminent.
	properties = {}     # dumps of game object properties of the object, only references properties are inside.
	                    # properties names are bytes (for optimisation)
	                    # property take value ignore (see class below) when sync is imminent the first time.
	dump_type = b''     # dump type (see backup manager), if dump is used.
	dump = b''          # optionnal pickle dump of the object (if was not in the backup file at start).

class ignore:
	pass

"""
* chaque hote peut ajouter a la liste des objets a synchronisée, tenue par le serveur
* a chaque cycle de sync, le serveur envoie aux clients la liste des objets dont il veut les sync (selon les clients)
* en dehors du cycle le serveur traite les requetes et receptionne les sync
* une sync qui est donnée par un client auquel le serveur n'a rien demande est oubliee
* si un client renvoie unknown au lieu de la sync d'un objet, ou ne renvoie rien avant le cycle suivant, la reference de l'hote est effacee et la requete est donnée a tous les clients, le plus haut client repondant est choisi lors de a phase de traitement
"""


class Server(socket.socket):
	packet_size          = 1024
	max_client           = 30      # maximum number of clients (can be set at runtime to increase number of clients but doesn't quick connected clients
	update_period        = 0.5     # maximum time (s) between 2 server update communication (update of client datas)
	step_time            = 0.8     # maximum time in execution of each step
	bad_password_timeout = 3       # time the client should wait when get a wrong password (second)
	multiple_sessions    = False   # set to True, allow multiple host to use the same user (account and password)
	registeration        = True    # set to True, allow new users to be created
	username_conformity  = username_conformity_off # function to call to test a new username (valid or not)
	callback_error       = True    # If True, raise error of callbacks, but this can makes the server unstable
	
	run       = False      # put it to False to stop the server
	hosts     = []         # list of connected hosts
	datas     = {}         # list of obdatas indexed by object id's (bytes for optimisation)
	thread    = None       # actual thread of the server
	order     = []         # priority of trusting for each host, first in the list are the most trusted
	delays    = {}         # list of date to take count of hosts packets (indexed by host)
	users     = {}         # list of hosts connected referenced by username
	passwords = {}         # list of passwords referenced by username
	blacklist = []         # list of host to avoid (the server will never answer to its requests)
	num_client = 0         # number of client connected
	
	next_update = 0        # next time to update database
	cleared_index = []     # index of freed clients (in lists)
	answering_clients = [] # list of booleans associated with index of clients (True if the client has send a 
	                       # request after the last update)
	
	callbacks = []         # list of functions to call when a non-standard packet is received, function must take 
	                       # 3 parameters: the server instance, the packet received (bytes), the couple (ip, port)
	                       # of the host that emited this packet.
	                       # return True to erase the packet without executing other callbacks on it.
	                       # the callbacks are executed in the list order.
	on_register = []       # list of functions callback, each are called when a new user is registered.
	                       # signature:   void func(server, (ip, port), (user, password))
	
	queue = {}             # list of packet to send after every threatment of incomming packet (send whenever there 
	                       # is no packet received). Indexed by host (ip, port).
	
	
	# put lan to False if you don't want to use lan interface
	# put lo to False if you don't want to use internal loopback interface
	# frequency is the delay between each 
	def __init__(self, port, lo=False):
		self.port = port
		socket.socket.__init__(self, socket.AF_INET, socket.SOCK_DGRAM)
		localhost = ip_addr.get_local_addr()
		debugmsg('using port %d.' % self.port)
		if not localhost or lo:
			debugmsg('internal loopback (127.0.0.1) used.')
			localhost = '127.0.0.1'
		else:
			debugmsg('LAN interface (with ip of computer %s) used.' % localhost)
		self.bind((localhost, self.port))
		self.setblocking(False)
	
	
	# server step to tread all client requests
	def step(self):
		self.run = True
		end_step = time.time() + self.step_time
		while time.time() < self.next_update and time.time() < end_step and self.run :
			# thread client requests
			try:    
				packet, host = self.recvfrom(self.packet_size)
				# wait for quicked or delayed hosts (bad password for exemple)
				while host in self.delays and time.time() < self.delays[host]:
					packet, host = recvfrom(self.packet_size)
			except socket.error or BlockingIOError: time.sleep(0.001)
			else:
				# no communication with a not identified host
				if host in self.hosts:
					index = self.hosts.index(host)
					# count number of '\0' in the packet, it indicates the minimal number of words in the packet
					words = packet.split(b'\0')
					zeros = len(words)
					
					# global synchronization request
					if similar(packet, b'requestsync\0'):
						self.answering_clients[index] = True
						for id in self.datas:
							data = self.datas[id]
							if data.host != index:
								if data.physics:
									self.sendto(b'setmeca\0'+ id +b'\0'+ data.physics, host)
								for property in data.properties:
									if data.properties[property] != ignore:
										self.sendto(b'setprop\0'+ id +b'\0'+ property +b'\0'+ data.properties[property], host)
					
					elif similar(packet, b'getmeca\0') and zeros >= 1:
						self.answering_clients[index] = True
						obid = words[1]
						if obid in self.datas:
							data = self.datas[obid]
							if data.physics:
								# if origin of the sync is updated by the sync, the object is frozen
								if index != data.host:
									msg = b'setmeca\0' + obid + b'\0' + data.physics
									self.sendto(msg, host)
							else:
								self.datas[obid].physics = None
						else:
							self.datas[obid] = obdata()
							self.datas[obid].physics = None
					
					elif similar(packet, b'getprop\0') and zeros >= 2:
						self.answering_clients[index] = True
						obid, propname = words[1:3]
						if obid in self.datas:
							if propname in self.datas[obid].properties :
								# if origin of the sync is updated by the sync, the object is frozen
								if index != self.datas[obid].host and self.datas[obid].properties[propname] != ignore:
									msg = b'setprop\0' + obid + b'\0'+ propname + b'\0' + self.datas[obid].properties[propname]
									self.sendto(msg, host)
							else: 
								self.datas[obid].properties[propname] = ignore
						else: 
							self.datas[obid] = obdata()
							self.datas[obid].properties[propname] = ignore
					
					elif similar(packet, b'unknown\0') and zeros >= 1:
						obid = words[1]
						if obid in self.datas and index == self.datas[obid].host:
							self.datas[obid].host = None
					
					# packet of kind:    setmeca.id.dump  ('\0' instead of .)
					elif similar(packet, b'setmeca\0') and zeros >= 1: 
						obid = words[1]
						if obid in self.datas:
							data = self.datas[obid]
							# if this host is more trusted, this host will be in charge of this data
							if data.host == None or data.host <= index:
								data.updated = True
								data.host = index
								data.physics = packet[9+len(obid):]
								self.datas[obid] = data
					
					# packet of kind:    setprop.id.propertyname.dump   ('\0' instead if .)
					elif similar(packet, b'setprop\0') and zeros >= 2:
						obid, propname = words[1:3]
						if obid in self.datas:
							data = self.datas[obid]
							# if this host is more trusted, this host will be in charge of this data
							if data.host == None or data.host <= index:
								data.updated = True
								data.host = index
								data.properties[propname] = packet[10+len(obid)+len(propname):]
								self.datas[obid] = data
					
					# packet of kind:    newobject.dumptype.dump
					elif similar(packet, b'newobject\0') and zeros >= 2:
						dumptype = words[1]
						dump = packet[12+len(dumptype):]
						try: dump = pickle.loads(dump)
						except: pass
						else:
							if 'id' in dump:
								original = dump['id']
								# search for an higher ID
								id = original
								for key in self.datas.keys():
									if key.isdigit() and int(key) >= id:
										id = int(key) + 1
								dump['id'] = id
								# save object dump
								data = obdata()
								data.physics   = pickle.dumps((dump['pos'], dump['rot'], dump['velocity'], dump['angular']))
								self.datas['id'] = data
								# send to all client the information of a new object
								reponse = b'newobject\0'+ dumptype +b'\0'+ pickle.dumps(dump)
								for h in self.hosts:
									if h and h != host: self.send(reponse, host)
								# change ID on client if necessary
								if original != id: self.send(b'changeid\0'+ original +b'\0'+ id, host)
					
					elif similar(packet, b'unsync\0') and zeros >= 2:
						mode, id = packet.split(b'\0', maxsplit=3)[1:3]
						if id in self.datas.keys():
							if self.datas[id].host == host:
								if mode == b'meca':
									self.datas[id].physics = False
								elif mode == b'prop':
									prop = packet.split(b'\0', maxsplit=4)[3]
									del self.datas[id].properties[prop]
								for h in self.hosts:
									if h and h != host: self.send(packet)
						
					
					elif similar(packet, PACKET_STOP):
						debugmsg('client (%s, %d) is quitting' % host)
						self.remove_client(host)
					
					else:
						for callback in self.callbacks:
							if self.callback_error:
								if callback(self, packet, host): break
							else:
								try: 
									if callback(self, packet, host): break
								except: print('error in callback:', callback)
				
				# try to resolve host, or reject it
				else: 
					if similar(packet, b'authentify\0'):
						user, password = packet.split(b'\0')[1:3]
						user = user.decode()
						password = password.decode()
						subject = b'authentication\0'
						
						# if client is not known, register it (except configuration)
						if user not in self.passwords:
							if self.registeration:
								if self.username_conformity(user):
									debugmsg('create user \'%s\'.' % user)
									self.passwords[user] = password
								else:
									debugmsg('new username \'%s\' rejected because of unconformity.' % user)
									sendto(subject + b'username not conform', host)
									break
							else:
								debugmsg('creation of new user is forbidden.')
								self.sendto(subject + b'new user disallowed', host)
								break
						
						# user should be created
						if password == self.passwords[user]:
							if host in self.hosts and len(self.users[host]) > 1 and not self.multiple_sessions:
								debugmsg('an other session for host %s refused.' % host[0])
								self.sendto(subject + b'multisession not allowed', host)
							if self.num_client >= self.max_client:
								debugmsg('new session for host %s refused: server is full.' % host[0])
								self.sendto(subject + b'server is full', host)
							else:
								debugmsg('new session for host %s.' % host[0])
								self.sendto(subject + b'password accepted', host)
								self.add_client(host, user)
								for callback in self.on_register:
									callback(self, host, (user, password))
						else:
							self.delays[host] = time.time() + self.bad_password_timeout
							self.sendto(subject + b'password rejected', host)
					
					# if there is no authentication request, send an authentication order
					else:
						self.sendto(b'authentify\0', host)
			
			# send queued, in the list order, one packet per packet received if the client receive.
			for host in self.queue:
				if host:
					while len(self.queue[host]):
						# the packet will be removed from queue when the server receive unqueue echo for this packet
						packet = self.queue[host].pop(0)
						try: self.sendto(packet, host)
						except: print('unable to send queued packet:', packet)
			
		
		
		if time.time() < end_step and self.run:
			for id in self.datas:
				self.datas[id].updated = None
				data = self.datas[id] # set marker to false, to detect if client doesn't answer
				packets = [] # list of packets to send to clients concerned by this object
				
				# maybe send a maximal sized packet of data to unknown hosts (big packet to make a DOS on the machine thaht try to make one)
				
				if data.physics != False :
					packets.append(b'getmeca\0'+ id +b'\0')
				if data.properties :
					for prop in data.properties:
						packets.append(b'getprop\0'+ id +b'\0'+ prop +b'\0')
				# else, send request to this client and more trusted clients
				if data.host != None and self.hosts[data.host]:
					for packet in packets:
						for i in range(data.host+1): # include the host provider
							host = self.hosts[i]
							if host and self.answering_clients[i]: self.sendto(packet, host)
				# if an host is disconnected or away from this object take an other host
				else:
					for packet in packets:
						for i in range(len(self.hosts)):
							host = self.hosts[i]
							if host and self.answering_clients[i]: self.sendto(packet, host)
			self.next_update = time.time() + self.update_period
			self.answering_clients = len(self.answering_clients)* [False]
	
	
	# execute self.step() in an other thread
	def thread_step(self):
		self.thread = threading.Thread()
		self.thread.run = self.step
		self.thread.start()
	
	# add a packet to the queue (to send to the specified host)
	def add_to_queue(self, packet, host='all'):
		if host == 'all':
			for host in self.hosts:
				if host:
					self.queue[host].append(packet)
		elif host:
			self.queue[host].append(packet)
	
	# clear the socket's queue, return the list of packet received
	def clear_requests(self):
		queue = []
		received=b'\0'
		while len(received):
			received = self.recv()
			queue.append(received)
		return queue
	
	# stop the server
	def stop(self):
		for host in self.hosts:
			if host: self.sendto(PACKET_STOP, host)
		self.run = False
	
	# declare a new client (without authenticate him) and return host index (or -1 if fails).
	# user is the username
	# host is a couple (host, port)
	# trusting is an index in the order of trusted hosts (optionnal)
	def add_client(self, host, user, trusting=-1):
		if self.cleared_index:
			index = self.cleared_index.pop(0)
			self.hosts[index] = host
			self.answering_clients[index] = True
		elif self.num_client <= self.max_client:
			index = len(self.hosts)
			self.hosts.append(host)
			self.answering_clients.append(True)
		else:
			return -1
		self.delays[index] = 0
		self.order.insert(trusting, index)
		if user not in self.users:  self.users[user] = []
		self.users[user].append(host)
		self.queue[host] = []
		self.num_client += 1
		return index
	
	def remove_client(self, host):
		if host in self.hosts:
			index = self.hosts.index(host)
			self.sendto(PACKET_STOP, host)
			self.hosts[index] = None
			self.order.pop(self.order.index(index))
			self.num_client -= 1
			self.cleared_index.append(index)
			del self.queue[host]
			for user in self.users:
				if host in self.users[user]: self.users[user].pop(self.users[user].index(host))
			return index
		else:
			return -1



if __name__ == '__main__':
	port = 30000
	if len(sys.argv) > 1: port = int(argv[1])
	server = network.Server(port)
	server.setblocking(False)
	run = True

	def f():
		while run:
			server.step()

	t = threading.Thread()
	t.run = f
	t.start()

	input('type enter to stop.')

	run = False
	server.stop()
	t.join()
	server.close()
