# -*- coding:utf-8 -*-


import socket, ssl ,threading, ip_addr
from time import *

# un packet commence et se termine par ces chaines (plutot rares il es vrai)
END_MARK = "/Ä/END/Ë/"
START_MARK = "/Ä/START/Ë/"



class Client(threading.Thread):
	def __init__(self, addr): # Client((host, port))
		threading.Thread.__init__(self)
		self.tunnel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.tunnel.connect(addr)
		self.tunnel.setblocking(False)
		self.host = addr
		self.received = ""
		self.threadlock = threading.Lock()
		self._lock = False
		self.stop = False
	
	def close(self):
		self.tunnel.close()
	
	def lock(self):
		self._lock = True
	def unlock(self):
		self._lock = False
	def locked(self):
		return self._lock
	
	# reçoit et retourne le premier des paquets présents dans la file ou None
	def getpacket(self):
		print('getpacket')
		self.threadlock.acquire()
		try: self.received += self.tunnel.recv(1024).decode()
		except: pass
		self.threadlock.release()
		start = self.received.find(START_MARK)
		end   = self.received.find(END_MARK, start)
		if start == -1 or end == -1:
			print('no packet')
			return None
		packet = self.received[start+len(START_MARK):end]
		print('getpacket:', repr(packet))
		return packet
	
	# efface le premier paquet recu de la file
	def clearpacket(self):
		start = self.received.find(START_MARK)
		end   = self.received.find(END_MARK, start)
		if start == -1 or end == -1:
			print('EE')
			return
		self.received = self.received[:start] + self.received[end+len(END_MARK):]
	
	# retoure le paquet suivant et le supprime de la file, si il n'y en a pas, attend qu'il y en ai
	def nextpacket(self, wait=True, delete=True):
		packet = self.getpacket()
		if wait:
			while packet == None:
				packet = self.getpacket()
				sleep(0.05)
		if packet != None and delete : self.clearpacket()
		print('nextpacket', repr(packet))
		return packet
	
	# envoie un paquet a l'hote indiqué
	def send(self, data):
		print('send', repr(data))
		self.tunnel.send('{}{}{}'.format(START_MARK, str(data), END_MARK).encode())
	
	# methode a implementer dans les classes descendantes
	def run(self):
		pass


class SSLClient(Client):
	def __init__(self, addr):
		Client_.__init__(self, addr)
		self.tunnel, self.host = ssl.wrap_socket(self.tunnel)





class Server(threading.Thread):
	max_client = 40
	tunnels = [] # liste des tunnels établis avec les clients
	hosts = []   # liste des hotes (ip, port)     rangée dans le meme ordre que self.tunnels
	locks = []   # marque de verrouillage         rangée dans le meme ordre que self.tunnels
	received = [] # pile de reception (par hote), rangée dans le meme ordre que self.tunnels
	closed = [] # liste des indices de sockets fermes
	
	def __init__(self, port):
		threading.Thread.__init__(self)
		localhost = ip_addr.get_local_addr()
		if not localhost:
			localhost = '127.0.0.1' # only for offline tests
			print('unable to find local ip address, use internall loopback instead')
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# prevent from 'address already in use'
		self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server.bind((localhost, port))
		self.server.listen(5)
		self.server.setblocking(True)
		self.threadlock = threading.Lock()
	
	
	def accept(self):
		self.threadlock.acquire()
		try: sock, addr = self.server.accept()
		except: return None
		sock.setblocking(False)
		self.threadlock.release()
		index = len(self.hosts)-1
		if len(self.closed):
			index = self.closed.pop(0)
			self.tunnels[index] = sock
			self.hosts[index] = addr
			self.locks[index] = False
			self.received[index] = ""
		elif len(self.hosts) < self.max_client :
			self.tunnels.append(sock)
			self.hosts.append(addr)
			self.locks.append(False)
			self.received.append("")
		return index
	
	def disconnect(self, index):
		if self.tunnels[index] != None: 
			self.tunnels[index].close()
		self.tunnels[index] = None
		self.hosts[index] = None
		self.received[index] = []
		self.closed.append(index)
	
	def close(self):
		for i in range(len(self.hosts)):
			if self.hosts[i]:
				self.disconnect(i)
		self.server.close()
	
	# verrouille (officiellement seulement) le iièeme tunnel
	def lock(self,index):
		self.locks[index] = True
	
	# déverrouille (officiellement seulement) le iièeme tunnel
	def unlock(self, index):
		self.locks[index] = False
	
	# retourne vrai si le iième tunnel est verrouillé
	def locked(self, index):
		return self.locks[index]
	
	# reçoit et retourne le premier des paquets présents dans la file ou None
	def getpacket(self, index):
		i= index
		#print('receive: ', end='')
		self.threadlock.acquire()
		try: self.received[i] += self.tunnels[i].recv(1024).decode()
		except: pass
		self.threadlock.release()
		start = self.received[i].find(START_MARK)
		end = self.received[i].find(END_MARK, start)
		if start == -1 or end == -1 :
			return None
		# il est possible qu'un paquet soit reçu en meme temps qu'un autre, si il est reçu en plusieurs
		# morceaux, la fonction cherche donc des données seulement à partir d'un en-tete valide, en
		# laissant les données non comprises de coté, quand le paquet interférant est supprimé, le paquet
		# fragmenté est reconstitué.
		packet = self.received[i][start+len(START_MARK):end]
		print('getpacket:', repr(packet))
		return packet
	
	# efface le dernier packet reçu de la file
	def clearpacket(self, index):
		start = self.received[index].find(START_MARK)
		end = self.received[index].find(END_MARK, start)
		if start == -1 or end == -1 :
			print('EE')
			return
		self.received[index] = self.received[index][:start] + self.received[index][end+len(END_MARK):]
	
	# retoure le paquet suivant et le supprime de la file, si il n'y en a pas, attend qu'il y en ai
	def nextpacket(self, index, wait=True, delete=True):
		packet = self.getpacket(index)
		if wait:
			while packet == None:
				packet = self.getpacket(index)
				sleep(0.05)
		if packet != None and delete : self.clearpacket(index)
		print('nextpacket:', repr(packet))
		return packet
	
	# envoie un paquet a l'hote indiqué
	def send(self, index, data):
		print('send', repr(data))
		self.tunnels[index].send('{}{}{}'.format(START_MARK, str(data), END_MARK).encode())
	
	def sendall(self, data):
		for i in range(len(self.hosts)):
			self.send(i, data)
	
	def run(self):
		pass


class SSLServer(Server):
	def __init__(self, keyfile, certfile, port):
		Server.__init__(self, port)
		self.certfile = certfile
		self.keyfile = keyfile
	
	def accept(self):
		i = len(self.hosts)
		Server.accept(self)
		self.tunnels[i] = ssl.wrap_socket(self.tunnels[i], server_side=True, keyfile=self.keyfile, certfile=self.certfile)

