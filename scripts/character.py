# -*- coding:utf-8 -*-

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

import bge, mathutils
import special_characters, tools
import client
import backup_manager as bm
import os, time, threading, pickle, math



def similar(s, pattern) :        
	return s[:len(pattern)] == pattern

# to set True after game initialized
load_async = False


# fonctions utilisées par les classes

def add_special_skin(name, ref) :
	"""
	Ajoute le corps personnage spécial nommé, sur l'objet donné.
	Le personnage est détecté par son armature qui doit etre nommée name+' armature', tous le reste du skin doit etre
	dans la parenté descendant de l'armature.
	"""
	armature_name = name+" armature"
	# check if the skin is loaded
	if name in special_characters.files:
		skin_file = bge.logic.expandPath(bge.logic.game_path+'/' + special_characters.files[name])
	else: 
		print("error: unable to find a file for skin "+name)
		return None
	# load if not
	if skin_file not in bge.logic.LibList():
		print("module \"%s\": loading skin model \"%s\"" % (__name__, skin_file,))
		s = bge.logic.LibLoad(skin_file, "Scene", load_actions=True, async=load_async)
		if load_async: time.sleep(2)
		time.sleep(1)
		#tools.LibLoad(skin_file, "Scene", load_actions=True, async=False)
	# add to scene
	scene = bge.logic.getCurrentScene()
	armature = scene.addObject(armature_name, scene.active_camera)
	#armature = scene.objects[armature_name]
	armature.worldPosition = ref.worldPosition
	armature.worldOrientation = ref.worldOrientation
	#return scene.addObject(name+" armature", ref)
	return armature

def add_generic_skin(name, ref) :
	return False

def add_skin(name, ref) :
	"""
	Ajoute le corps du personnage ('spécial' ou pas) sur l'objet donné comme référence.
	Le personnage est détecté par son armature qui doit etre nommée name+' armature', tous le reste du skin doit etre
	dans la parenté descendant de l'armature.
	"""
	c =  add_generic_skin(name, ref)
	if c == False :
		return add_special_skin(name, ref)
	else : return c;



MOVE_ACTION = "move action"
ITEM_ACTION = "item action"
HEADZ_ACTION = "head Z"
HEADY_ACTION = "head Y"

HALFPI = math.pi/2


class Skin(object) :
	"""
	Cette classe représente un personnage du point de vue affichage : mouvements, déplacements, ...
	Elle implémente les fonctions d'un personnage spécial, tous les personnages doivent etre contenus dans le
	fichier blender ou cette classe est utilisée.
	"""
	body_hair = body_head = body_helmet = None
	helmet_active = False
	
	attachs  = [] # attaches pour ranger les items sur le corps
	hands    = {} # attaches des items dans la main, désignées par leur nom
	items    = [] # liste des items attachés au corps
	handitem = None # item selectionné

	animations = {
		# disk actions
		"launch disk" : ('clu item', 90, 103, 104, 120),
		"catch disk" : ('clu item', 257, 257, 270, 270),
		"take disk" : ('clu item', 60, 64, 68, 79),
		# light-baton and cycle actions
		"take light-baton" : ('clu item', 241, 249, 249, 253),
		"set cycle" : ('clu move', 216, 220, 224, 228),
		"biking with disk" : ('clu move', 239, 243, 243, 247),
		"biking take disk" : ('clu item', 276, 278, 278, 280),
		# head movements
		"look Z" : ('clu head Z', 10, 20, 20, 30),
		"look Y" : ('clu head Y', 10, 20, 20, 30),
		# basic movements
		"walk ford" : ('clu move', 20, 30, 51, 60),
		"walk back" : ('clu move', 60, 51, 30, 20),
		"run ford" : ('clu move', 141, 147, 161, 168),
		"jump" : ('clu move', 168, 173, 182, 191),
		},

	def __init__(self, skin_name, collisionbox) :
		self.skin_name = skin_name
		self.box = collisionbox
		self.action = ""
		self.look = mathutils.Euler((0,0,0))
		if skin_name in special_characters.animations.keys():
			self.animations = special_characters.animations[skin_name]

	def __repr__(self) :
		return "'%s(skin_name=%s, collisionbox=%s)" % (self.__class__.__name__, repr(self.skin_name), repr(self.box))


		
	# affiche l'objet dans la scene
	def spawn(self, existing=None) :
		if not existing:
			self.armature = add_skin(self.skin_name, self.box)
		else:
			self.armature = existing
			oldclass = existing['class']
		self.armature.setParent(self.box)
		self.box["armature"] = self.armature
	
		self.attachs  = [] # attaches pour ranger les items sur le corps
		self.hands    = {} # attaches des items dans la main, désignées par leur nom
		self.items    = [] # liste des items attachés au corps
		self.handitem = None # item selectionné
		# recuperer les points d'attache pour les items
		for child in self.armature.children :
			if "attach" in child :
				self.attachs.append(child)
				self.items.append(None)
			elif "hand" in child :
				self.hands[child["hand"]] = child
			elif "body" in child :
				self.body = child
			elif "body head" in child :
				self.body_head = child
			elif "body hair" in child:
				self.body_hair = child
			elif "body helmet" in child:
				self.body_helmet = child
		self.updateRest()
		self.toggleHelmet(False)
		self.armature['class'] = self
		if existing:
			self.items = oldclass.items
			self.handitem = oldclass.handitem
		return self.armature



		
	# place le personnage en position de repos (debout)
	def updateRest(self) :
		if self.action == "" : return; # à l'état fixe de repos (sans mouvement du squelette), self.action est une chaine vide
		anim = self.animations[self.action]
		current = int(self.armature.getActionFrame())
		# lancement de l'animation de fin d'action dans le cas ou une action serait en cour
		if current > anim[4] or current < anim[3] :
			self.armature.playAction(anim[0], anim[3], anim[4])
		# si cette animation est terminée, mise en mode repos
		if current == anim[4] or current == anim[4]-1 :
			#self.armature.setActionFrame(0) # pour une raison inconnue, cela fait recommencer l'animation d'arret
			self.action = ""
	
	# effectue une marche en avant : la vitesse définit si il s'agit d'une marche ou d'une course, et le signe du sens de cette derniere.
	def updateRunning(self, speed) :
		if self.action == "jump" :
			return;
		if speed == 0 :
			self.updateRest();
			return;
		#print(int(self.armature.getActionFrame()));
		# selectionner l'action a effectuer
		if speed < -2 : 	todo = "run back";
		elif speed < 0 :	todo = "walk back";
		elif speed < 2 :	todo = "walk ford";
		else :          	todo = "run ford";
		
		anim = self.animations[todo]
		current = int(self.armature.getActionFrame());
		# fin de l'animation précédente si necessaire
		if self.action == "" and abs(current-anim[2]) > 5 :
			# demarrer la marche
			self.armature.playAction(anim[0], anim[1], anim[2]);
			self.action = todo;
		elif self.action not in ("run back", "walk back", "walk ford", "run ford") :
			if current > anim[3] and current < anim[1] :
				# retour en position de repos avant démarrage
				#print(self.action, "return to rest")
				self.updateRest();
			else :
				# marche
				self.armature.playAction(anim[0], anim[2], anim[3], play_mode=bge.logic.KX_ACTION_MODE_LOOP);
				self.action = todo;
		else :
			# marche
			self.armature.playAction(anim[0], anim[2], anim[3], play_mode=bge.logic.KX_ACTION_MODE_LOOP);
			self.action = todo;

	# fait s'accroupir ou se lever le personnage
	def updateCrouch(self, crouched=True) :
		pass

	# change l'etat du saut (stand pour pas de saut, jump pour en train de sauter, up pour en train de se relever)
	def updateJump(self, jump=True) :
		if jump == False :
			if self.action == "jump" :
				self.updateRest();
			return;
		# action a effectuer
		anim = self.animations["jump"]
		current = int(self.armature.getActionFrame(0))

		if current > anim[3] or current < anim[1] :
			# lancement du saut
			self.armature.playAction(anim[0], anim[1], anim[2], layer=0);
			self.action = "jump";
		elif abs(current-anim[2]) < 3 :
			# saut
			self.armature.playAction(anim[0], anim[2], anim[2], layer=0, play_mode=bge.logic.KX_ACTION_MODE_LOOP);
			self.action = "jump";
		

	# fait regarder le personnage dans une direction
	def lookAt(self, rotEuler) :
		self.look = rotEuler
		#print(self.look)
		anim_z = self.animations["look Z"]
		headposz = anim_z[2]+(anim_z[4]-anim_z[1])*rotEuler.z/math.pi;
		self.armature.playAction(anim_z[0], headposz, headposz, layer=3, layer_weight=0.0, play_mode=bge.logic.KX_ACTION_MODE_LOOP, blend_mode=bge.logic.KX_ACTION_BLEND_BLEND);
	
	def click(self, interactor):
		# effectue l'action 'clic' ou 'touch' sur l'objet donne.
		if "click" in self.animations :
			anim = self.animations["click"]
			self.armature.playAction(anim[0], anim[1], anim[4], layer=2)

	# saisi l'objet
	def take(self, item) :
		if item and self.handitem == None : # la main doit etre vide
			self.attach(item, "hand")
			if "class" in item and item["class"] :
				item["class"].taken()
		else :
			return False
		return True

	def drop(self) :
		"""
		lache l'objet tenu en main
		"""
		if self.handitem :
			item = self.handitem
			self.detach("hand")
			if item['class']:
				item['class'].droped()

			
	def attach(self, item, attach="hand") :
		"""
		item est un KX_GameObject  et attach une chaine.
		"""
		if bge.types.KX_GameObject in type(item).__bases__  :
			raise(TypeError("item type must be KX_GameObject."))
		if attach == "hand" :
			# assignation
			self.handitem = item
			attach = self.hands[item["hand"]]
			# nettoyer l'ancien emplacement de l'item
			if item in self.items :
				oldindex = self.items.index(item)
				self.items[oldindex] = None
		else :
			# nettoyer l'ancien emplacement de l'item
			oldindex = -1
			if item in self.items :
				oldindex = self.items.index(item)
				self.items[oldindex] = None
			elif item == self.handitem :
				oldindex = -2
				self.handitem = None

			# selection du nouvel emplacement
			index = 0
			if type(attach) == str :
				for i in range(len(self.attachs)) :
					if self.attachs[i].name == attach :
						index = i
						break
			elif type(attach) == int :
				index = attach
			elif type(attach) == bge.types.KX_GameObject :
				for i in range(len(self.attach)) :
					if self.attach[i] == attach :
						index = i
						break
			else :
				raise(TypeError("attach must be of type int, str or KX_GameObject instead of %s" % str(type(attach))))
			attach = self.attachs[index]
			# vider la case cible si elle est pleine
			if self.items[index] != None :
				self.toggleItem(index, wielded=True, wait=True)
			# si on ne peut pas vider la case cible, annulation
			if self.items[index] != None :
				# replacement de l'item dans l'inventaire
				if oldindex > 0 : self.items[oldindex] = item
				elif oldindex == -2 : self.handitem = item
				print(self.items[index], oldindex, index)
				print('error: Skin.attach(): new attach is busy')
				return

			# assigner l'item au nouvel emplacement
			self.items[index] = item
		
		item.setParent(attach);
		item.localPosition = mathutils.Euler((0,0,0))
		item.localOrientation = mathutils.Euler((0,0,0))

		
	def detach(self, item="hand") :
		"""
		item peut etre un KX_GameObject ou bien l'indice de l'item, si item egal "hand", l'objet tenu en main est alors détaché
		"""
		if item == "hand" : # cas particulier de l'item placé dans la main
			self.handitem.removeParent()
			self.handitem = None
			return
		# cas général
		if type(item) == bge.types.KX_GameObject :
			index = self.items.index(item)
		elif type(item) == int :
			index = item
		else :
			raise(TypeError("item type must be int or KX_GameObject."))
			return
		# détachement
		self.items[index].removeParent()
		self.items[index].localAngularVelocity += mathutils.Vector((1, 1, 0))
		self.items[index] = None

	def toggleItem(self, item, wielded=True, wait=False):
		"""
		item peut etre un KX_GameObject ou bien l'indice de l'item, si item egal "hand", l'objet tenu en main est alors détaché
		Si wait est fausse, des threads séparés seront créés pour gerer les animations.
		"""
		if type(item) == int :
			index = item
			obj = self.items[index]
		elif item == "hand" or self.handitem == item :
			index = "hand"
			obj = self.handitem
		elif type(item) == bge.types.KX_GameObject :
			index = self.items.index(obj)
			obj = item
		else :
			raise(TypeError("item type must be int or KX_GameObject."))
			return
		
		if index == "hand" :
			if wielded or self.handitem == None : return # dans ce cas il n'y a rien besoin de faire
			# sinon, deselection
			if "class" in self.handitem and self.handitem["class"] : self.handitem["class"].unwielded()
			
			radical = self.handitem["attach"] # seul les attaches dont le nom commence par le nom demandé par l'item sont valides
			for i in range(len(self.attachs)) :
				name = self.attachs[i]["attach"]
				if len(name) >= len(radical) and name[:len(radical)] == radical and self.items[i] == None : # l'emplacement est approprié et libre
					# animation de replacement de l'item
					if "itemname" in obj :
						anim = self.animations["take "+obj["itemname"]]
						self.armature.playAction(anim[0], anim[4], anim[1], layer=2, layer_weight=0.0)
						# il faut une boucle de controle parallele pour attacher l'item a la main au bon moment
						def _attach() :
							while True:
								# cas ou l'animation se lit de gauche a droite
								if anim[1] >= anim[4] and self.armature.getActionFrame(2) >= anim[2] :
									self.attach(obj, i)
									break
								# cas ou l'animation se lit de droite à gauche
								if anim[1] <= anim[4] and self.armature.getActionFrame(2) <= anim[2] :
									self.attach(obj, i)
									break
							#print('end of _attach (1)')
							return
						if wait :
							_attach()
						else :
							thread = threading.Thread()
							thread.run = _attach
							thread.start()

					else :
						self.attach(obj, i)
		else :
			# rien besoin de faire si l'item n'est pas séléctionné
			if not wielded : return
			if "class" in obj and obj["class"] : obj["class"].wielded()
			# sinon, selection de l'item
			if self.handitem != None :
				def _freehand() :
					self.toggleItem("hand", wielded=False, wait=True)
					if self.handitem != None :
						print("Can't deselect wielded item.")
						return
					self.toggleItem(item, wielded=True, wait=True)
				if wait :
					_freehand()
				else :
					thread = threading.Thread()
					thread.run = _freehand
					thread.start()
			else :
				# animation de prise de l'item
				if "itemname" in obj :
					anim = self.animations["take "+obj["itemname"]]
					self.armature.playAction(anim[0], anim[1], anim[4], layer=2, layer_weight=0.0)
					# il faut une boucle de controle parallele pour attacher l'item a la main au bon moment
					def _attach() :
						while True:
							# cas ou l'animation se lit de gauche a droite
							if anim[4] >= anim[1] and self.armature.getActionFrame(2) >= anim[2] :
								self.attach(obj, "hand")
								break
							# cas ou l'animation se lit de droite à gauche
							elif anim[4] <= anim[1] and self.armature.getActionFrame(2) <= anim[2] :
								self.attach(obj, "hand")
								break
						#print("end of __attach (2)")
						return
					if wait :
						_attach()
					else :
						thread = threading.Thread()
						thread.run = _attach
						thread.start()
						
				else :
					self.attach(obj, "hand")
		
		

	def wieldItem(self, item, wait=False):
		"""
		item peut etre un KX_GameObject ou bien l'indice de l'item, si item egal "hand", l'objet tenu en main est alors détaché
		"""
		if type(item) == int :
			if item >= len(self.items): return
			index = item
			obj = self.items[index]
		elif item == "hand" :
			obj = self.handobject
		elif type(item) == bge.types.KX_GameObject :
			index = self.items.index(obj)
			obj = item
		else :
			raise(TypeError("item type must be int or KX_GameObject."))
			return

		if obj == None :
			self.toggleItem("hand", wielded=False, wait=wait)
		else :
			self.toggleItem(index, wielded=True, wait=wait)
		

	def actionItem(self, action):
		# execute l'action numero action sur l'item de la main, une action est similaire à un clic de la souris
		if not self.handitem or not 'class' in self.handitem or not self.handitem['class'] :
			return
		if action == 1 :
			self.handitem['class'].action1()
		if action == 2 :
			self.handitem['class'].action2()
		if action == 3 :
			self.handitem['class'].action3()
			
	def setHp(self, hp):
		if hp <= 0:
			self.drop()
			for item in self.items:
				if item : self.detach(item)

	def _ch_color(self, color, obj):
		if 'emit tex' not in self.object:
			ID = bge.texture.materialID(obj, 'IM{}_body_emit_{}.png'.format(self.skin_name, self.armature['color']))
			object_texture = bge.texture.Texture(obj, ID)
			obj['emit tex'] = object_texture
		
		url = bge.logic.expandPath('//{}_body_emit_{}.png'.format(self.skin_name, color))
		src = bge.texture.ImageFFmpeg(url)
		obj['emit tex'].source = src
		bge.texture.refresh(False)
		self.armature['color'] = color
		
	def setColor(self, color):
		# change la couleur du personnage par une autre (blue, red, orange, white)
		self.object['color'] = color
		self._ch_color(color, self.body)
		#self._ch_color(color, self.body_head)
		#self._ch_color(color, self.body_hair)
		for item in self.items:
			item['class'].changeHolderColor(color)
	
	def toggleHelmet(self, helmet=None):
		if self.body_head and self.body_hair and self.body_helmet:
			if helmet == None: helmet = (not self.helmet_active)
			if helmet:
				self.body_head.visible = False
				self.body_hair.visible = False
				self.body_helmet.visible = True
			else:
				self.body_head.visible = True
				self.body_hair.visible = True
				self.body_helmet.visible = False
			self.helmet_active = helmet



class OfflineCharacter(object) :
	"""
	Représente un personnage, vrai joueur ou non, c'est un avatar. Cette classe sert à manager l'ensemble des
	possibilités du personnage (action, mouvements, ...)
	"""

	minimal_fall_velocity_for_damage = 20

	vehicle = None
	uptime = 0
	
	body_head = body_hair = body_helmet = None
	
	inair_date = 0.
	inair_laststate = False
	item_toggle_date = 0.
	helmet_toggle_date = 0.

	
	def __init__(self, name, skin_name="clu") :
		self.name = name
		self.skin_name = skin_name

	def __repr__(self) :
		return "%s(name=%s, skin_name=%s)" % (self.__class__.__name__, repr(self.name), repr(self.skin_name))

	def spawn(self, ref=None, existing=None) :
		scene = bge.logic.getCurrentScene()
		if not existing:
			self.box = scene.addObject("player collision", ref)
		else:
			self.box = existing
		self.box["hp"] = 1.0
		self.box["active"] = True
		self.mover = self.box.actuators['Motion']
		self.skin = Skin(self.skin_name, self.box)
		# search for pre-existing skin
		skin = None
		if existing:
			for child in self.box.children:
				if child.name[-9:] == " armature":
					existing = child
					break
		self.skin.spawn(existing)
		
		for child in self.box.children :
			# index jump sensor
			if "jump sensor" in child and child["jump sensor"] :
				self.jump_sensor = child
			# camera head
			elif "camera head" in child and child["camera head"] :
				self.camera_head = child
			elif "top right"   in child: self.sens_top_right    = child.sensors[0]
			elif "right"       in child: self.sens_right        = child.sensors[0]
			elif "floor right" in child: self.sens_flooar_right = child.sensors[0]
			elif "top left"    in child: self.sens_top_left     = child.sensors[0]
			elif "left"        in child: self.sens_left         = child.sensors[0]
			elif "floor left"  in child: self.sens_flooar_left  = child.sensors[0]
			elif "top back"    in child: self.sens_top_left     = child.sensors[0]
			elif "back"        in child: self.sens_left         = child.sensors[0]
			elif "floor back"  in child: self.sens_flooar_left  = child.sensors[0]
			elif "top front"   in child: self.sens_top_right    = child.sensors[0]
			elif "front"       in child: self.sens_right        = child.sensors[0]
			elif "floor right" in child: self.sens_flooar_right = child.sensors[0]
			
		# index cameras, ...
		for child in self.camera_head.children :
			if "camera TPS" in child and child["camera TPS"] :
				self.camera_back = child
			elif "camera FPS" in child and child["camera FPS"] :
				self.camera_fps = child
			# item sensor
			elif "item sensor" in child and child["item sensor"] :
				self.item_sensor = child
		# la tête du skin
		self.body_head = None
		self.body_hair = None
		for child in self.skin.armature.children :
			if "body head" in child :
				self.body_head = child
			if "body hair" in child :
				self.body_hair = child
			if "body helmet" in child:
				self.body_helmet = child
		self.box["class"] = self
		# markup the network synchronisation for physics
		self.box[client.marker_property_physic] = True
		self.box[client.marker_property_property] = "('hp', 'active', 'move_speed')"
		return self.box


	def disable(self):
		self.box["active"] = False
	def enable(self):
		self.box["active"] = True
	def isactive(self):
		return self.box["active"]

	def getColor(self):
		return self.skin.armature['color']

	def updateRest(self) :
		self.skin.updateRest()


	def updateRunning(self, speed) :
		t = time.time()
		dt = t-self.uptime
		self.uptime = t
		if not self.inair_laststate:
			self.skin.updateRunning(speed)
			self.move_speed = speed
			self.box['move speed'] = speed
			v = self.mover.dLoc
			#self.mover.dLoc = (0, speed*dt, 0)
			self.mover.dLoc = (0, speed/(bge.logic.getLogicTicRate()), 0)  # or bge.logic.getAverageFrameRate()
		else :
			self.mover.dLoc = (0,0,0)

	last_zv = 0
	last_last_zv = 0 # 2 valeurs pour le rebond
	falldate = 0
	def updateJump(self, jump=True) :
		s = self.jump_sensor.sensors[0] # il n'y a qu'un seul capteur sur le jump sensor
		if s.status in (bge.logic.KX_INPUT_JUST_ACTIVATED, bge.logic.KX_INPUT_ACTIVE) and self.falldate < time.time() :
			# calculer les dégats de chute
			if self.inair_laststate :
				if self.last_last_zv < -self.minimal_fall_velocity_for_damage :
					self.setHp(self.getHp() + min(0, (self.last_last_zv+self.minimal_fall_velocity_for_damage)/self.minimal_fall_velocity_for_damage))
			
			# changer l'état du saut
			if jump and time.time() >= self.inair_date+0.3 :
				self.skin.updateJump(True)
				self.box.localLinearVelocity.z += 8.
				self.falldate = time.time()+0.3
			else :
				self.skin.updateJump(False)

			# changer l'état air/sol
			self.inair_laststate = False

		else :
			if self.inair_laststate == False:
				self.box.localLinearVelocity.y += self.move_speed*2
				self.box['move speed'] = 0
			self.inair_laststate = True
			self.last_last_zv = self.last_zv
			self.last_zv = self.box.localLinearVelocity.z
			self.inair_date = time.time()
			self.skin.updateJump(True)
		s.reset();

	def setHp(self, hp) :
		if hp <= 0 :
			hp = 0
			self.skin.setHp(hp)
			#self.box.endObject()
		self.box["hp"] = hp


	def getHp(self) :
		return self.box["hp"]



	def setCameraActive(self, camera) :
		scene = bge.logic.getCurrentScene()
		
		if camera == "back" :
			scene.active_camera = self.camera_back
			if self.skin.helmet_active and self.body_helmet:
				self.body_helmet.visible = True
				if self.body_head : self.body_head.visible = False
				if self.body_hair : self.body_hair.visible = False
			else:
				if self.body_head : self.body_head.visible = True
				if self.body_hair : self.body_hair.visible = True
		
		elif camera == "fps" :
			scene.active_camera = self.camera_fps
			if self.body_head :   self.body_head.visible = False
			if self.body_hair :   self.body_hair.visible = False
			if self.body_helmet : self.body_helmet.visible = False

	
	def availableItem(self) :
		s = self.item_sensor.sensors[0]
		if s.status in (bge.logic.KX_INPUT_JUST_ACTIVATED, bge.logic.KX_INPUT_ACTIVE) and len(s.hitObjectList) :
			for obj in s.hitObjectList :
				if "item" in obj :
					return s.hitObjectList[0]
		return None;

	def take(self) :
		obj = self.getInteractor()
		if obj and "item" in obj: self.skin.take(obj)
	
	def click(self):
		obj = self.getInteractor()
		if obj and "interact" in obj:
			self.takeWay(self.look.z)
			self.skin.click(obj)
			self.box.sendMessage("click", " ", obj.name)
			self.box.sendMessage("touch", " ", obj.name)
	
	def getInteractor(self): # retourne l'objet interactif vise ou None
		s = self.item_sensor.sensors[0]
		if s.status in (bge.logic.KX_INPUT_JUST_ACTIVATED, bge.logic.KX_INPUT_ACTIVE) and len(s.hitObjectList) :
			for obj in s.hitObjectList :
				if "item" in obj or "interact" in obj :
					return obj
		return None
		

	def drop(self) :
		self.skin.drop()

	# item est un KX_GameObject, une chaine ou un numero (attention, le numero 0 signifie la main)
	def wieldItem(self, item, wait=False) :
		if time.time() >= self.item_toggle_date : # éviter les répétitions trop rapides des touches
			self.item_toggle_date = time.time() + 0.5
			self.skin.wieldItem(item, wait=wait)

	def actionItem(self, action):
		self.skin.actionItem(action)
	
	
	def toggleHelmet(self, helmet=None):
		if self.helmet_toggle_date <= time.time():
			self.helmet_toggle_date = time.time() + 0.5
			self.skin.toggleHelmet(helmet)


	orient = mathutils.Euler((0,0,0))
	look = mathutils.Euler((0,0,0))
	
	# fait regarder le personnage dans une direction
	def lookAt(self, rotEuler) :
		o = self.orient.z
		t = 0
		diff = rotEuler.z - self.orient.z
		if diff > HALFPI :
			if self.isactive():	o = rotEuler.z - HALFPI
			else:	rotEuler.z = HALFPI
			t = HALFPI
		elif diff < -HALFPI :
			if self.isactive():	o = rotEuler.z + HALFPI
			else:	rotEuler.z = -HALFPI
			t = -HALFPI
		else :
			t = diff
		rotEuler.y = max(min(rotEuler.y, HALFPI), -HALFPI)
		self.skin.lookAt(mathutils.Euler((0, rotEuler.y, t)))
		self.camera_head.localOrientation = mathutils.Euler((0, rotEuler.y, t + HALFPI))
		self.takeWay(o)
		self.look = rotEuler

	def takeWay(self, rz) :
		if self.isactive() == False: return
		self.orient.z = rz
		self.box.worldOrientation = self.orient


	def vehicleCommand(self, comlist):
		if self.vehicle:
			self.vehicle['class'].updateCont(comlist)
	

class Character(OfflineCharacter):
	"""
	Represent a character PNJ or not. This class add network sync to client on these methods:
	* lookAt
	* takeWay
	* updateJump
	* updateRunning
	* drop
	* click
	* helmet
	* wieldItem
	"""
	# next times to sync movements
	sync_run = 0.
	sync_jump = 0.
	sync_look = 0.
	sync_way = 0.
	
	def spawn(self, ref=None, existing=None):
		OfflineCharacter.spawn(self, ref, existing)
		client = bge.logic.client
		if client:
			# configure client<->server sync exchange
			if client_callback not in client.callbacks: client.callbacks.append(client_callback)
			client.sync_physic(self.box)
			client.sync_property(self.box, 'active')
			client.sync_property(self.box, 'move speed')
			client.sync_property(self.box, 'hp')
	
	# internal method: send sync information, given as bytes and the python data
	def syncInfo(self, info, data):
		if bge.logic.client:
			if type(data) == int:      data = str(data).encode()
			elif type(data) == bytes:  pass
			else:                      data = pickle.dumps(data)
			bge.logic.client.add_to_queue(b'character\0'+info+b'\0'+str(bm.get_object_id(self.box)).encode()+b'\0'+data)
		
	
	def lookAt(self, rotEuler):
		if time.time() > self.sync_look:
			self.sync_look = time.time() + 0.3
			self.syncInfo(b'look', rotEuler[:])
		OfflineCharacter.lookAt(self, rotEuler)
	
	def takeWay(self, orient):
		if time.time() > self.sync_way:
			self.sync_way = time.time() + 0.5
			self.syncInfo(b'way', orient)
		OfflineCharacter.takeWay(self, orient)
	
	def updateJump(self, jump=True):
		if time.time() > self.sync_jump:
			self.sync_jump = time.time() + 0.1
			if jump: self.syncInfo(b'jump', b'1')
			else:    self.syncInfo(b'jump', b'0')
		OfflineCharacter.updateJump(self, jump)
	
	def updateRunning(self, speed):
		if time.time() > self.sync_run:
			self.sync_run = time.time() + 0.1
			self.syncInfo(b'run', float(speed))
		OfflineCharacter.updateRunning(self, speed)

	def drop(self):
		self.syncInfo(b'drop', b'')
		OfflineCharacter.drop(self)
	
	def take(self):
		obj = self.getInteractor()
		self.syncInfo(b'take', bm.get_object_id(obj))
		OfflineCharacter.take(self)
	
	def click(self):
		self.syncInfo(b'click', b'')
		OfflineCharacter.click(self)
	
	def actionItem(self, action):
		# execute l'action numero action sur l'item de la main, une action est similaire à un clic de la souris
		if not self.skin.handitem or not 'class' in self.skin.handitem or not self.skin.handitem['class'] :
			return
		self.syncInfo(b'actionItem', action)
		OfflineCharacter.actionItem(self, action)
	
	def wieldItem(self, item, wait=False):
		if time.time() >= self.item_toggle_date:
			if type(item) == int :
				if item >= len(self.skin.items): return
				index = item
				obj = self.skin.items[index]
			elif item == "hand" :
				obj = self.skin.handobject
			elif type(item) == bge.types.KX_GameObject :
				index = self.skin.items.index(obj)
				obj = item
			else :
				raise(TypeError("item type must be int or KX_GameObject."))
				return
			if item != "hand": self.syncInfo(b'wield', index)
			else: self.syncInfo(b'wield', b'hand')
			OfflineCharacter.wieldItem(self, item, wait)

	def toggleHelmet(self, helmet=None):
		if self.helmet_toggle_date <= time.time():
			if helmet == None: helmet = (not self.skin.helmet_active)
			if helmet: self.syncInfo(b'helmet', b'1')
			else:      self.syncInfo(b'helmet', b'0')
			OfflineCharacter.toggleHelmet(self, helmet)
			# there is not need to increment helmet_toggle_date, because it is done in toggleHelmet()


# execute all the characters actions resquested by the server, without distincition of if it is or not an offline character.
def client_callback(server, packet):
	if client.similar(packet, b'character\0'):
		if packet.count(b'\0') < 3: return True
		info, uniqid = packet.split(b'\0')[1:3]
		data = packet[12+len(info)+len(uniqid):] # data can be a seriaalized data, so might contain zeros
		if not uniqid.isdigit(): return True
		uniqid = int(uniqid)
		char = bm.get_object_by_id(bge.logic.getCurrentScene(), uniqid)
		if not char: return True
		if 'class' not in char:
			print('error: client_callback: avatar', uniqid, "doesn't have any class")
			return True
		character = char['class']
		if info == b'look':
			try: rotEuler = pickle.loads(data)
			except: return True # good packet, but bad information
			OfflineCharacter.lookAt(character, mathutils.Euler(rotEuler))
		
		elif info == b'way':
			try: orient = pickle.loads(data)
			except: return True
			OfflineCharacter.takeWay(character, orient)
		
		elif info == b'jump':
			if data == b'1': OfflineCharacter.updateJump(character, True)
			else:            OfflineCharacter.updateJump(character, False)
		
		elif info == b'run':
			try: speed = pickle.loads(data)
			except: return True
			OfflineCharacter.updateRunning(character, speed)
		
		elif info == b'drop':
			OfflineCharacter.drop(character)
		
		elif info == b'click':
			OfflineCharacter.click(character)
		
		elif info == b'actionItem':
			if data.isdigit(): OfflineCharacter.actionItem(character, int(data))
		
		elif info == b'take':
			if data.isdigit():
				obj = bm.get_object_by_id(bge.logic.getCurrentScene(), int(data))
				if obj and "item" in obj: character.skin.take(obj)
		
		elif info == b'wield':
			if data == b'hand':  OfflineCharacter.wieldItem(character, 'hand', wait=True)
			elif data.isdigit(): OfflineCharacter.wieldItem(character, int(data), wait=True)
		
		elif info == b'helmet':
			if data == b'1': OfflineCharacter.toggleHelmet(character, True)
			else:            OfflineCharacter.toggleHelmet(character, False)
		# remove packet after this callback
		return True
	# else, unknown packet for this callback, pass
	return False



# callback d'initialisation d'un objet personnage
def init() :
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	character = Character(owner["character_name"], owner["skin"])
	character.spawn(owner)
	owner.endObject()
	# this object was not existing in the game backup, so signal its creation
	if bge.logic.client:
		bge.logic.client.created_object(character.box)
