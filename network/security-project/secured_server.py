# -*- coding: utf-8 -*-

import socket, time, random
import ip_addr
from encryption import * # ce module s'inscrit dans la continuité du fichier encryption.

def readconfig(config_file) :
	f = open(config_file, "r");
	lines = f.readlines();
	f.close();
	keys = {};
	# scan de chaque ligne
	i = 0;
	while i < len(lines) :
		# nouvel config d'hote détectée par un en-tête [ip 127.0.0.1 hostname]
		# chaque ligne est du type valeur="variable" ou valeur=<la valeur en python>
		if lines[i][0] == '[' and lines[i][1:3] == "ip" :
			grps = lines[i].split(' ')
			ip, hostname = grps[1], grps[2]
			hostname = hostname[:hostname.find(']')]
			conf = {}
			while i < len(lines)-1 :
				i += 1
				words = lines[i].split('=', 1)
				if len(words) == 2 :
					conf[words[0]] = eval(words[1]) # doit etre une valeur python correcte
				elif words[0][0] == "[" :
					i -= 1
					break
			# assignation des parametres du nouvel hôte dans la liste interne.
			keys[(ip, hostname)] = (conf['key'], conf['offset'])
		i += 1;
	return keys


msg_ch_secu = "¡¡CHANGE SECU!!"
msg_sync_request = "¡¡SYNC REQUEST!!"
msg_sync_answer = "SYNC ANSWER"

class SecuredServer(socket.socket) :

	def __init__(self, port):
		socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
		addr = ip_addr.speed_get_addr() # addresse obtenue rapidement par un serveu udp de google (8.8.8.8)
		socket.socket.bind(self, (addr, port))
		socket.socket.listen(self, 5) # 5 clients mis en attente au maximum avant que le server de traite les demandes de connexion
		
		self.clients = [] # liste des clients connectes : [socket, (addr, port), security]

		
	def accept(self):
		s, addr = socket.socket.accept(self)
		index = len(self.clients)
		for i in range(len(self.clients)):
			if self.clients[index][1] == None :
				index = i
		self.clients.append([s, addr, None])
		return index

	
	def close(self, id):
		s, addr, secu = self.clients[id]
		s.close()
		self.clients[id][1] = None

		
	def get_connected_clients(self):
		l = []
		for i in range(len(self.clients)):
			if self.clients[i][1] != None :
				l.append(i)
		return l

	def send(self, clientlist, string):
		for client in clientlist :
			s, addr, secu = self.clients[client]
			if secu :
				s.send(secu.encode(string).encode())
			else :
				s.send(string.encode())

				
	def recv(self, client, buffersize=1024, timeout=None):
		s, addr, secu = self.clients[client]
		to = s.gettimeout()
		s.settimeout(timeout)
		string = s.recv(buffersize).decode()
		if secu :
			string = secu.decode(string)
		while self.update(client, string) :
			string = s.recv(buffersize).decode()
			if secu :
				string = secu.decode(string)
		s.settimeout(to) # restore old timeout
		return string


	def close_server(self):
		socket.socket.close(self)


	def set_security(self, client, security) :
		"""
		Change simplement la methode de chiffrement du serveur par celle donnée.
		"""
		self.clients[client][2] = security

	def change_security(self, client, security) :
		"""
		Envoie au client un requete de changement de chiffrage. Celle-ci sera filtrée par la methode recv du client.
		"""
		s, addr, secu = self.clients[client]
		msg = "{} {} {} {}{}".format(msg_ch_secu, len(security.key), len(security.offset), security.key, security.offset)
		self.send([client], msg)

	def update(self, client, msg):
		"""
		Tente de mettre a jour le serveur avec le message donnée (on lui donne généralement un message reçu.
		Si le message en question n'est pas un ordre ou une requete du client, la fonction retourne False, sinon
		elle retourne True.
		"""
		if msg[0:len(msg_ch_secu)] == msg_ch_secu :
			blocs = msg.split(' ')
			keylen = int(blocs[1])
			offsetlen = int(bloc[2])
			key = bloc[3][:keylen]
			offset = bloc[3][keylen:keylen+offsetlen]
			self.clients[client][2].key = key
			self.clients[client][2].offset = offset
			return True
		if msg[0:len(msg_sync_request)] == msg_sync_request :
			received = time.time()
			self.send([client], msg_sync_answer)
			sent = time.time()
			r = self.recv(client)
			answered = time.time()
			if r != msg_sync_answer :
				print("{} Warning: client {} was not synchronized because of bad answer of it.".format(
					self.__class__.__name__,   self.clients[client][1][0]
					))
			else:
				self.clients[client][2].time_offset = answered-received
		else:
			return False

	def sync(self, clientlist):
		for client in clientlist:
			starting = time.time()
			self.send([client], msg_sync_request)
			sent = time.time()
			r = self.recv(client)
			answered = time.time()
			print("received:", repr(r))
			if r != msg_sync_answer :
				print("{} Warning: client {} was not synchronized because of bad answer of it.".format(
					self.__class__.__name__,   self.clients[client][1][0]
					))
				print(time.time())
			else:
				self.send([client], msg_sync_answer)
				self.clients[client][2].time_offset = answered-starting




if __name__ == "__main__" :
	import pprint
	
	#help(SecuredServer)
	server = SecuredServer(port=30000)
	print("waiting for a client.")
	client = server.accept()
	server.set_security(client, Security("truc en boité", "müche"))
	server.sync([client])
	print("type ^D to quit.")
	while 1 :
		try:
			print(server.recv(client))
			server.send([client], input("type> "))
		except EOFError or socket.error:
			print("\nQuitting.")
			break
	server.close(client)
	server.close_server()

