# -*- coding:utf-8 -*-

import socket, time, random
from encryption import * # ce module s'inscrit dans la continuité du fichier encryption.py
from secured_server import * # les composants de ce module sont faits pour interagir avec ceux du fichier secured_server.py


class SecuredClient(socket.socket) :
	"""
	La classe SecuredClient permet de creer et utiliser un socket client, avec un système de sécurité tel que
	Security (voir encyption.py).
	"""

	# activer pour le debugage (il est reconnandé de la faire manuellement dans un script).
	debug = False

	def __init__(self, config_file=None, security_jury=jury):
		"""
		port (int)         Le numero du port que l'on va utiliser.
		config_file (str)  est le fichier de configuration à partir duquel, les serveur va démarrer, il contient
		                   les information concernant chaque serveur déja rencontré. Cet argument est optionnel.
		                   Attention : ce fichier devra etre consulté à chaque connexion.
		                   Ce fichier peut etre le même que celui donné à SecuredServer.
		"""
		socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM);
		self.secu = None

	def send(self, string) :
		if self.secu :
			socket.socket.send(self, self.secu.encode(string).encode())
		else:
			socket.socket.send(self, string.encode())

	def recv(self, buffersize=1024, timeout=None) :
		to = socket.socket.gettimeout(self)
		socket.socket.settimeout(self, timeout)
		string = socket.socket.recv(self, buffersize).decode()
		if self.secu :
			string = self.secu.decode(string)
		while self.update(string) :
			string = socket.socket.recv(self, buffersize).decode()
			if self.secu :
				string = self.secu.decode(string)
		socket.socket.settimeout(self, to)
		return string

	def set_security(self, security):
		"""
		Change simplement la methode de chiffrement du client par celle donnée.
		"""
		self.secu = security

	def change_security(self, security):
		"""
		Envoie au serveur un requete de changement de chiffrage. Celle-ci sera filtrée par la methode recv du serveur.
		"""
		msg = "{} {} {} {}{}".format(msg_ch_secu, len(security.key), len(security.offset), security.key, security.offset)
		self.send(msg)

	def update(self, msg):
		"""
		Tente de mettre a jour le client avec le message donnée (on lui donne généralement un message reçu.
		Si le message en question n'est pas un ordre ou une requete du serveur, la fonction retourne False, sinon
		elle retourne True.
		"""
		print("received:", repr(msg))
		if msg[0:len(msg_ch_secu)] == msg_ch_secu :
			blocs = msg.split(' ')
			keylen = int(blocs[1])
			offsetlen = int(bloc[2])
			key = bloc[3][:keylen]
			offset = bloc[3][keylen:keylen+offsetlen]
			self.secu.key = key
			self.secu.offset = offset
			return True
		if msg[0:len(msg_sync_request)] == msg_sync_request :
			received = time.time()
			self.send(msg_sync_answer)
			sent = time.time()
			r = self.recv()
			answered = time.time()
			if r != msg_sync_answer :
				print("{} Warning: server was not synchronized because of bad answer of it.".format(self.__class__.__name__))
				print(time.time())
			else:
				self.secu.time_offset = answered-received
			return True
		else:
			return False

	def sync(self):
		starting = time.time()
		self.send(msg_sync_request)
		sent = time.time()
		r = self.recv(client)
		answered = time.time()
		if r != msg_sync_answer :
			print("{} Warning: server was not synchronized because of bad answer of it.".format(self.__class__.__name__))
		else:
			self.send(msg_sync_answer)
			self.secu.time_offset = answered-starting




if __name__ == "__main__" :
	#help(SecuredClient)
	client = SecuredClient()
	input("type return to continue. ")
	client.connect(("192.168.1.10", 30000))
	client.set_security(Security("truc en boité", "müche"))
	print("type ^D to quit.")
	while 1:
		try:
			client.send(input("type> "))
			print(client.recv())
		except EOFError or socket.error:
			print("\nQuitting.")
			break
	client.close()

