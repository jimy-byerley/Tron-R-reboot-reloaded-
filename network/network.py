# python defined
import threading, socket, time
# from the game
import ip_addr

debug = True
def debugmsg(*args):
	if debug: print(*args)

def similar(s, pattern) :        
	return s[:len(pattern)] == pattern

def username_conformity_off(s) : 
	return True


PACKET_STOP    = b"quitting"

class obdata:
	"""
	This class represents an object for the server (most common attributes are pre-defined for optimisation)
	"""
	host = 0               # maximal index of host who can provide information about this object
	position = False
	rotation = False
	parent = False
	properties = False
	velocity = False
	angular = False
	
	def __repr__(self):
		return '{pos=%s,\t rot=%s,\t parent=%s,\t properties=%s}' % (repr(self.position), repr(self.rotation), repr(self.parent), repr(self.properties))


class Server(socket.socket):
	packet_size          = 1024
	max_client           = 30      # maximum number of clients (can be set at runtime to increase number of clients but doesn't quick connected clients
	update_frequency     = 0.5     # maximum time (s) between 2 server update communication (update of client datas)
	bad_password_timeout = 3       # time the client should wait when get a wrong password (second)
	multiple_sessions    = False   # set to True, allow multiple host to use the same user (account and password)
	registeration        = True    # set to True, allow new users to be created
	username_conformity  = username_conformity_off # function to call to test a new username (valid or not)
	
	run       = False      # put it to False to stop the server
	hosts     = []         # list of connected hosts
	datas     = {}         # list of obdatas
	thread    = None       # actual thread of the server
	order     = []         # priority of trusting for each host, first in the list are the most trusted
	delays    = {}         # list of date to take count of hosts packets (indexed by host)
	users     = {}         # list of hosts connected referenced by username
	passwords = {}         # list of passwords referenced by username
	num_client = 0         # number of client connected
	
	next_update = 0        # next time to update database
	cleared_index = []     # index of freed clients (in lists)
	
	
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
		while time.time() < self.next_update :
			# thread client requests
			packet, host = recvfrom(self.packet_size)
			# wait for quicked or delayed hosts (bad password for exemple)
			while host in self.delays and time.time() > self.delays[host]:
				packet, host = recvfrom(self.packet_size)
	
			# no communication with a not identified host
			if host in self.hosts:
				index = self.hosts.find(host)
				# count number of '\0' in the packet, it indicates the minimal number of words in the packet
				zeros = packet.count(b'\0')
				if similar(packet, b'getmeca\0') and zeros >= 1:
					obname = packet.split(b'\0')[1]
					if obname in self.datas:
						data = self.datas[obname]
						msg = b'setmeca\0%s\0' % obname
						if data.position:   msg += 'pos\0%d\0%d\0%d' % data.position
						if data.position:   msg += 'rot\0%d\0%d\0%d' % data.rotation
						if data.position:   msg += 'vel\0%d\0%d\0%d' % data.velocity
						if data.position:   msg += 'ang\0%d\0%d\0%d' % data.angular
						if data.parent != False:  msg += 'par\0%s' % str(data.parent)
						self.sendto(msg, host)
						# if this host is more trusted, this host will be in charge of this data
						if data.host < index:
							self.datas[obname].host = host
				
				elif similar(packet, b'getpro\0') and zeros >= 2:
					obname, propname = packet.split(b'\0')[1:3]
					if obname in self.datas and propname in self.datas[obname].properties :
						self.sendto(b'setpro\0%s\0%s\0%s' % (obname, self.datas[obname].properties[propname]), host)
				
				elif similar(packet, b'unknown\0') and zeros >= 1:
					obname = packet.split(b'\0')[1]
					if obname in self.datas:
						self.datas[obname].host = self.max_client
				
				elif similar(packet, b'disconnect\0'):
					self.remove_client(host)
			
			# try to resolve host, or reject it
			else:
				if similar(packet, b'authentify\0'):
					user, password = packet.split(b'\0')[1:3]
					user = user.decode()
					password = password.decode()
					if user not in self.passwords and self.registeration:
						if self.username_conformity(user):
							debugmsg('create user \'%s\'.' % user)
							self.passwords[user] = password
						else:
							debugmsg('new username \'%s\' rejected because of unconformity.' % user)
							send(b'username not conform', host)
					else:
						debugmsg('creation of new user is forbidden.')
						send(b'new user disallowed', host)
					if password == self.passwords[user]:
						if host in self.hosts and not self.multiple_sessions:
							debugmsg('an other session for host %s refused.' % host[0])
							self.sendto(b'multisession not allowed', host)
						if self.num_client >= self.max_client:
							debugmsg('new session for host %s refused: server is full.', % host[0])
							self.sendto(b'server is full', host)
						else:
							debugmsg('new session for host %s.' % host[0])
							self.sendto(b'password accepted')
							self.add_client(host)
					else:
						self.delays[host] = time.time() + self.bad_password_timeout
						self.send(b'password rejected', host)
	
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
		self.sendall(PACKETSTOP)
		self.running = False
	
	# declare a new client (without authenticate him) and return host index (or -1 if fails).
	# user is the username
	# host is a couple (host, port)
	# trusting is an index in the order of trusted hosts (optionnal)
	def add_client(self, host, user, trusting=-1):
		if self.cleared_index:
			index = self.cleared_index.pop(0)
			self.hosts[index] = host
			self.delays[index] = 0.
		
		elif self.num_client <= self.max_client:
			index = len(self.hosts)
			self.hosts.append(index)
			self.delays.append(0.)
		
		else:
			return -1
		self.order.insert(trusting, index)
			self.users[user].append(host)
		self.num_client += 1
		return index
	
	def remove_client(self, host):
		if host in self.hosts:
			index = self.hosts.find(host)
			self.sendto(b'disconnect', host)
			self.hosts[index] = None
			self.order.pop(self.order.find(index))
			self.num_client -= 1
			self.cleared_index.append(index)
			return index
		else:
			return -1
