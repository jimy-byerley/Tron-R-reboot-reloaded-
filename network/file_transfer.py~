# -*- coding:utf-8 -*-

import hashlib, sys, os
from time import *
from basic_connection import *


basic_server = Server
basic_client = Client


class FileTransferServer(basic_server):
	# le serveur n'a le droit de diffuser que des fichiers préfixés par le path
	def __init__(self, port, path):
		basic_server.__init__(self, port)
		self.path = path
	
	def accept(self):
		basic_server.accept(self)
	
	# retourne le path absolu d'un fichier ou repertoire si il est dans l'arboressence autorisée, None sinon
	def realpath(self, path):
		path = os.path.abspath(path)
		if sys.platform[:4] == 'win':
			separator = '\\'
		else : 
			separator = '/'
		dirs = path.split(separator)
		pathdirs = self.path.split(separator)
		for i in range(len(pathdirs)):
			if i >= len(dirs) or dirs[i] != pathdirs[i] : return False
		return path
	
	# envoie un fichier au client (présuppose que le client en attend deja un)
	def sendfile(self, index, pathfrom):
		# ouverture
		try:
			f = open(pathfrom, 'rb')
		except OSError:
			print('error in sending file:', pathfrom)
			self.send(index, 'abort')
			return
		self.send(index, 'ready')
		contain = f.read()
		f.close()
		# verification de la difference avec le fichier du client (si il n'y en a pas, c'est inutile de le transferer)
		md5 = hashlib.md5(contain)
		self.send(index, md5.hexdigest())
		reponse = self.nextpacket(index)
		if reponse == 'match':
			return
		elif reponse != 'wait':
			print('error: receive reponse', repr(reponse), 'instead of "match" or "wait"')
			return
		# envoi du fichier
		filesize = len(contain)
		packetsize = 1024
		self.send(index, filesize)
		self.send(index, packetsize)
		# attendre la reception du client
		sleep(0.2)
		self.lock(index)
		self.threadlock.acquire()
		total = 0
		while total < filesize:
			n = total+packetsize
			if n > filesize :
				while True:
					try: self.tunnels[index].send(contain[total:])
					except: sleep(0.01)
					else: break
				n = filesize
			else :
				while True:
					try: self.tunnels[index].send(contain[total:n])
					except: sleep(0.01)
					else: break
			total = n
			sleep(0.001)
			print(total)
		self.threadlock.release()
		self.unlock(index)
		reponse = self.nextpacket(index)
		if reponse != 'ok':
			print("some error: the client hasn't answered 'ok' but "+repr(reponse))
	
	
	# recoit un fichier du client (suppose que le client en envoi un)
	def recvfile(self, index, pathto):
		# verifier si il existe deja un fichier et si il a deja la meme signature (on ne le retelechare pas)
		reponse = self.nextpacket(index)
		if reponse == 'abort' : return
		elif reponse != 'ready' :
			print('server sent ', repr(reponse))
			return
		md5 = self.nextpacket(index)
		try:
			f = open(pathto, 'rb')
		except IOError:
			pass
		else :
			content = f.read()
			sum = hashlib.md5(content)
			if sum.hexdigest() == md5:
				self.send(index, 'match')
				return
		# creation du fichier
		try:
			f = open(pathto, 'wb')
		except IOError:
			print('error in receiving file:', repr(pathto))
			self.send(index, 'error')
			return
		# demande d'envoi
		self.send(index, 'wait')
		filesize = int(self.nextpacket(index))
		packetsize = int(self.nextpacket(index))
		self.lock(index)
		self.threadlock.acquire()
		total = 0
		while total < filesize:
			recv = b''
			try:
				recv = self.tunnels[index].recv(packetsize)
			except : pass
			total += len(recv)
			f.write(recv)
			#sleep(0.01)
			#print(total)
		self.threadlock.release()
		self.unlock(index)
		f.close()
		self.send(index, 'ok')
	
	
	def run(self):
		step_date = time()
		while True:
			# eviter d'encombrer le CPU quand il n'y a pas de requete
			t = time()
			sleep(t-step_date)
			step_date = t
			# analyser les derniers paquets
			for index in range(len(self.hosts)):
				packet = self.getpacket(index)
				
				if packet:
					if rep(packet, 'want file') :
						pathfrom = packet[10:]
						self.clearpacket(index)
						realpath = self.realpath(pathfrom)
						if realpath :
							self.send(index, 'accept')
							self.sendfile(index, realpath)
						else :
							self.send(index, 'reject')
					
					if rep(packet, 'take file'):
						pathto = packet[10:]
						self.clearpacket(index)
						realpath = self.realpath(pathto)
						if realpath:
							self.send(index, 'accept')
							self.recvfile(index, realpath)
						else:
							self.send(index, 'reject')






def rep(s, pattern):
	if s[:len(pattern)] == pattern : return True
	return False



class FileTransferClient(basic_client):
	
	# demande au serveur le fichier donné, retourne true seulement si fichier transferé
	def getfile(self, pathfrom, pathto):
		self.send('want file '+pathfrom)
		reponse = self.nextpacket()
		if reponse == 'reject':
			return False
		elif reponse != 'accept':
			print('error in requesting file', repr(pathfrom), ': received', repr(reponse))
			return False
		self.recvfile(pathto)
		return True
	
	# recoit un fichier du serveur (suppose que le serveur en envoi un)
	def recvfile(self, pathto):
		# verifier si il existe deja un fichier et si il a deja la meme signature (on ne le retelechare pas)
		reponse = self.nextpacket()
		if reponse == 'abort' : return
		elif reponse != 'ready' :
			print('server sent ', repr(reponse))
			return
		md5 = self.nextpacket()
		try:
			f = open(pathto, 'rb')
		except IOError:
			pass
		else :
			content = f.read()
			sum = hashlib.md5(content)
			if sum.hexdigest() == md5:
				self.send('match')
				return
		# creation du fichier
		try:
			f = open(pathto, 'wb')
		except IOError:
			print('error in receiving file:', repr(pathto))
			self.send('error')
			return
		# demande d'envoi
		self.send('wait')
		filesize = int(self.nextpacket())
		packetsize = int(self.nextpacket())
		self.lock()
		self.threadlock.acquire()
		total = 0
		while total < filesize:
			recv = b''
			try:
				recv = self.tunnel.recv(packetsize)
			except : pass
			total += len(recv)
			f.write(recv)
			#sleep(0.01)
			print(total)
		self.threadlock.release()
		self.unlock()
		f.close()
		self.send('ok')

	# demande au serveur se recevoir un fichier
	def putfile(self, pathfrom, pathto):
		self.send('take file '+pathto)
		reponse = self.nextpacket()
		if reponse == 'reject':
			return False
		elif reponse != 'accept':
			print('protocol error : received', repr(reponse))
			return False
		self.sendfile(pathfrom)
		return True
	
	# envoie un fichier au serveur (mode basique, il suppose que le serveur en attend deja un)
	def sendfile(self, pathfrom):
		# ouverture
		try:
			f = open(pathfrom, 'rb')
		except OSError:
			print('error in sending file:', pathfrom)
			self.send('abort')
			return
		self.send('ready')
		contain = f.read()
		f.close()
		# verification de la difference avec le fichier du client (si il n'y en a pas, c'est inutile de le transferer)
		md5 = hashlib.md5(contain)
		self.send(md5.hexdigest())
		reponse = self.nextpacket()
		if reponse == 'match':
			return
		elif reponse != 'wait':
			print('error: receive reponse', repr(reponse), 'instead of "match" or "wait"')
			return
		# envoi du fichier
		filesize = len(contain)
		packetsize = 1024
		self.send(filesize)
		self.send(packetsize)
		# attendre la reception du client
		sleep(0.2)
		self.lock()
		self.threadlock.acquire()
		total = 0
		while total < filesize:
			n = total+packetsize
			if n > filesize :
				while True:
					try: self.tunnel.send(contain[total:])
					except: sleep(0.01)
					else: break
				n = filesize
			else :
				while True:
					try: self.tunnel.send(contain[total:n])
					except: sleep(0.01)
					else: break
			total = n
			sleep(0.001)
			#print(total)
		self.threadlock.release()
		self.unlock()
		reponse = self.nextpacket()
		if reponse != 'ok':
			print("some error: the client hasn't answered 'ok' but "+repr(reponse))



if __name__ == '__main__':
	port = 10000
	if len(sys.argv) >= 3: port = int(sys.argv[2])
	if sys.argv[1] == 'server':
		s = FileTransferServer(port, '/home/jimy/tron-reboot/server/a')
		input("press enter to accept client.")
		s.accept()
		s.start()
		
	else:
		c = FileTransferClient(('192.168.1.10', port))
		input("press enter to get file.")
		c.getfile("a/boot3.blend", "b/boot3.blend")
		c.putfile("b/boot2.blend", "a/boot2.blend")
		c.close()
