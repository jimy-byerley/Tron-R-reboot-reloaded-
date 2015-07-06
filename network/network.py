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
import threading, socket, time, pickle
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
	update_period        = 0.1     # maximum time (s) between 2 server update communication (update of client datas)
	step_time            = 0.2     # maximum time in execution of each step
	bad_password_timeout = 3       # time the client should wait when get a wrong password (second)
	multiple_sessions    = True    # set to True, allow multiple host to use the same user (account and password)
	registeration        = True    # set to True, allow new users to be created
	username_conformity  = username_conformity_off # function to call to test a new username (valid or not)
	
	run       = False      # put it to False to stop the server
	hosts     = []         # list of connected hosts
	datas     = {}         # list of obdatas indexed by object name (bytes for optimisation)
	thread    = None       # actual thread of the server
	order     = []         # priority of trusting for each host, first in the list are the most trusted
	delays    = {}         # list of date to take count of hosts packets (indexed by host)
	users     = {}         # list of hosts connected referenced by username
	passwords = {}         # list of passwords referenced by username
	blacklist = []         # list of host to avoid (the server will never answer to its requests)
	num_client = 0         # number of client connected
	
	next_update = 0        # next time to update database
	cleared_index = []     # index of freed clients (in lists)
	answering_clients = [] # list of booleans associated with index of clients (True if the client has send a request after the last update)
	
	
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
	
	
	# server step to tread all client requests
	def step(self):
		self.run = True
		end_step = time.time() + self.step_time
		while time.time() < self.next_update and time.time() < end_step and self.run :
			# thread client requests
			try:    packet, host = self.recvfrom(self.packet_size)
			except: time.sleep(0.001)
			else:
				# wait for quicked or delayed hosts (bad password for exemple)
				while host in self.delays and time.time() < self.delays[host]:
					packet, host = recvfrom(self.packet_size)
		
				print(self.hosts)
				# no communication with a not identified host
				if host in self.hosts:
					index = self.hosts.index(host)
					# count number of '\0' in the packet, it indicates the minimal number of words in the packet
					zeros = packet.count(b'\0')
					if similar(packet, b'getmeca\0') and zeros >= 1:
						obname = packet.split(b'\0')[1]
						if obname in self.datas:
							data = self.datas[obname]
							if data.physics:
								# if origin of the sync is updated by the sync, the object is frozen
								if index != data.host:
									msg = b'setmeca\0' + obname + b'\0' + data.physics
									self.sendto(msg, host)
							else:
								self.datas[obname].physics = None
						else:
							self.datas[obname] = obdata()
							self.datas[obname].physics = None
						self.answering_clients[index] = True
					
					elif similar(packet, b'getprop\0') and zeros >= 2:
						obname, propname = packet.split(b'\0')[1:3]
						if obname in self.datas:
							if propname in self.datas[obname].properties :
								# if origin of the sync is updated by the sync, the object is frozen
								if index != self.datas[obname].host and self.datas[obname].properties[propname] != ignore:
									msg = b'setprop\0' + obname + b'\0'+ propname + b'\0' + self.datas[obname].properties[propname]
									self.sendto(msg, host)
							else: 
								self.datas[obname].properties[propname] = ignore
						else: 
							self.datas[obname] = obdata()
							self.datas[obname].properties[propname] = ignore
						self.answering_clients[index] = True
					
					elif similar(packet, b'unknown\0') and zeros >= 1:
						obname = packet.split(b'\0')[1]
						if obname in self.datas and index == self.datas[obname].host:
							self.datas[obname].host = None
							data.host = None
					
					# packet of kind:    setmeca.name.dump  ('\0' instead of .)
					elif similar(packet, b'setmeca\0') and zeros >= 1: 
						obname = packet.split(b'\0')[1]
						if obname in self.datas:
							data = self.datas[obname]
							# if this host is more trusted, this host will be in charge of this data
							if data.host == None or data.host <= index:
								data.updated = True
								data.host = index
								data.physics = packet[9+len(obname):]
								self.datas[obname] = data
					
					# packet of kind:    setprop.name.propertyname.dump   ('\0' instead if .)
					elif similar(packet, b'setprop\0') and zeros >= 2:
						obname, propname = packet.split(b'\0')[1:3]
						if obname in self.datas:
							data = self.datas[obname]
							# if this host is more trusted, this host will be in charge of this data
							if data.host == None or data.host <= index:
								data.updated = True
								data.host = index
								data.properties[propname] = packet[10+len(obname)+len(propname):]
								self.datas[obname] = data
						
<<<<<<< HEAD
					
					elif similar(packet, PACKET_STOP):
						self.remove_client(host)
				
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
							if host in self.hosts and not self.multiple_sessions:
								debugmsg('an other session for host %s refused.' % host[0])
								self.sendto(subject + b'multisession not allowed', host)
							if self.num_client >= self.max_client:
								debugmsg('new session for host %s refused: server is full.' % host[0])
								self.sendto(subject + b'server is full', host)
							else:
								debugmsg('new session for host %s.' % host[0])
								self.sendto(subject + b'password accepted', host)
								self.add_client(host, user)
						else:
							self.delays[host] = time.time() + self.bad_password_timeout
							self.sendto(subject + b'password rejected', host)
		
		if time.time() < end_step and self.run:
			for name in self.datas:
				self.datas[name].updated = None
				data = self.datas[name] # set marker to false, to detect if client doesn't answer
				packets = [] # list of packets to send to clients concerned by this object
				
				# maybe send a maximal sized packet of data to unknown hosts (big packet to make a DOS on the machine thaht try to make one)
				
				if data.physics != False :
					packets.append(b'getmeca\0'+ name +b'\0')
				if data.properties :
					for prop in data.properties:
						packets.append(b'getprop\0'+ name +b'\0'+ prop +b'\0')
				# else, send request to this client and more trusted clients
				if data.host and self.hosts[data.host]:
					for packet in packets:
						for i in range(data.host+1):
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
=======
		for name in range(len(self.datas)):
			self.datas[name].updated = None
			data = self.datas[name] # set marker to false, to detect if client doesn't answer
			packets = [] # list of packets to send to clients concerned by this object
			
			if data.position or data.rotation or data.parent or data.velocity or data.angular :
				packets.append(b'getmeca\0'+name.encode()+b'\0')
			if data.properties :
				for prop in data.properties and data.properties[prop]:
					packets.append(b'getprop\0'+name.encode()+b'\0'+prop.encode()+b'\0')
			# else, send request to this client and more trusted clients
			if data.host and self.hosts[data.host]:
				for host in self.hosts[:data.host+1]:
					if host: self.sendto(packet, host)
			# if an host is disconnected or away from this object take an other host
			else:
				for packet in packets:
					self.send(packet, host)
		self.next_update = time.time() + self.update_period
>>>>>>> 2278660392f45922b6cd893b0407bcd9d8e030cb
	
	
	# execute self.step() in an other thread
	def thread_step(self):
		self.thread = threading.Thread()
		self.thread.run = self.step
		self.thread.start()
	
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
			return index
		else:
			return -1
