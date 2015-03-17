# -*- coding:utf-8 -*-
"""
le client est passif dans la liaison, il ne fait que recevoir periodiquement les informations que le serveur envoie
- le serveur centralise ces données et les classes par client
- la position et la rotation sont stoquées et mettent a jour le client, une vitesse moyene de chaque objet est egalemet calculée par le serveur pour plus de fluidité
- les proprietes d'objets peuvent aussi etre synchronisées sur demande d'un des client (tous les autres suivront)
- les liens de parentés aussi sont synchronisées sur demande d'un client au moins
- les positions de 'joueurs' definis comme "centre d'interet" sont associés a chaque client
- les densités et niveaux de détails des zones nuageuses sont déduites de la distance au "centre d'interet", mais c'est le client qui les genere car les nuages pouvant (normalement) bouger, ils est inutils qu'ils soient les memes sur tous les clients
- l'objet socket client est placé dans bge.logic pour etre accessible a tous les scripts
- c'est le client qui demande qu'un tel objet ou une telle propriete d'un objet soient mis a jours, la demande est ensuite transmise comme ordre par le serveur aux autres clients qui enveront desormais des mises a jour de l'objet demandé

- les bots e fonction sont génerés par leur batiments de fonction qui les enlevent de la simulation (enleve l'objet et son process) quand le joueur est trop loin, le comportement est alors simulé au niveau méta
"""

from basic_connection import *
from time import *


def rep(s, pattern):
	if s[:len(pattern)] == pattern : return True
	return False

class obdata:
	position = False
	rotation = False
	parent = False
	properties = False
	
	def __repr__(self):
		return "{pos=%s,\t rot=%s,\t parent=%s,\t properties=%s}" % (repr(self.position), repr(self.rotation), repr(self.parent), repr(self.properties))



class GameServer(Server):
	_end = False
	# données du jeu (rassemblées par le serveur)
	hostpriority = [] # list of the host indices ordered by priority for retreive game datas, the lowest indice have the maximum prority
	datas = {} # obdata i assiged to objet's name
	config = {} # config directement importée du fichier de config
	addons = [] # list of callables to execute sometimes (loop number between each execution are registered in the couple (callable, loopcount)
	addons_steps  = []
	loopstep = 0
	
	# suit une procedure de login pour l'hote donné
	def authenticate(self, index):
		pass
	
	# termine la boucle du thread des la fin d'un cycle
	def end(self):
		self._end = True
	
	
	def run(self):
		self.addons_steps = [0]*len(self.addons) # doesn't create pointer
		self.loopstep = 0
		
		while not self._end:
			# analys of all client requests : register an object or a property
			for i in range(len(self.hosts)):
				packet = self.getpacket(i)
				while packet != None:
					g = packet.split('\0')
					if g[0] == 'registerloc' :
						obj = g[1]
						if not obj in self.datas.keys():
							self.datas[obj] = obdata()
						self.datas[obj].position = (0,0,0)
					elif g[0] == 'registerrot' :
						obj = g[1]
						if not obj in self.datas.keys():
							self.datas[obj] = obdata()
						self.datas[obj].rotation = (0,0,0)
					elif g[0] == 'registerparent' :
						obj = g[1]
						if not obj in self.datas.keys():
							self.datas[obj] = obdata()
						self.datas[obj].parent = ""
					elif g[0] == 'registerprop':
						obj = g[1]
						if not obj in self.datas.keys():
							self.datas[obj] = obdata()
						if self.datas[obj].properties == False:
							self.datas[obj].properties = {}
						self.datas[obj].properties[g[2]] = None
					else : break
					self.clearpacket(i)
					packet = self.getpacket(i)
					
			# update game state
			for obj in self.datas.keys():
				data = self.datas[obj]
				# receive status
				for i in self.hostpriority: # ask for the most trusted client and end with the less.
					# if client accept
					self.send(i, 'requestinfo\0'+obj)
					reponse = self.nextpacket(i)
					if reponse == 'available':
						try:
							if self.datas[obj].position:
								self.send(i, 'getloc\0'+obj)
								g = self.getpacket(i).split('\0')
								self.datas[obj].position = (float(g[0]), float(g[1]), float(g[2]))
								self.clearpacket(i) # the error should just came
							
							if self.datas[obj].rotation:
								self.send(i, 'getrot\0'+obj)
								g = self.getpacket(i).split('\0')
								self.datas[obj].rotation = (float(g[0]), float(g[1]), float(g[2]))
								self.clearpacket(i)
							
							if self.datas[obj].parent != False:
								self.send(i, 'getparent\0'+obj)
								self.datas[obj].parent = self.nextpacket(i)
							
							if self.datas[obj].properties != False:
								for prop in self.data[obj].properties.keys():
									self.send(i, 'getprop\0%s\0%s' % (obj, prop))
									g = getpacket(i)
									t = g[0]
									if t == 'str':
										val = g[1]
									elif t == 'int':
										val = int(g[1])
									elif t == 'float':
										val = float(g[1])
									elif t == 'bool':
										if g[1].lower() == 'true': val = True
										else : val = False
									self.datas[obj].properties[prop] = val
							self.send(i, 'endinfo')
						except:
							print('error in decoding sync data for object "%s" from client %d (%s)' % (obj, i, self.hosts[i]))
						else:
							break
					elif reponse != 'unavailable' :
						print('warning reponse of client %i (%s) is incorrect : received %s instead of "unavailale"' % (i, self.hosts[i][0], reponse))
				
				# send to all
				if data.position : self.sendall('setloc\0%d\0%d\0%d\0%s' % (data.position[0], data.position[1], data.position[2], obj))
				if data.rotation : self.sendall('setrot\0%d\0%d\0%d\0%s' % (data.rotation[0], data.rotation[1], data.rotation[2], obj))
				if data.parent != False : self.sendall('setparent\0%s\0%s' % (obj, data.parent))
				if data.properties :
					for prop in data.properties.keys():
						self.sendall('setprop\0%s\0%s\0%s' % (obj, prop, data.properties[prop]))
			
			for i in range(len(self.addons_steps)):
				if self.loopstep == self.addons_steps[i] :
					func, step = self.addons[i]
					try: func(self)
					except: print('error (loopstep %d) in executing callable %s' % (loopstep, repr(func)))
					self.addons_steps += step
			self.loopstep += 1
			sleep(0.02)
