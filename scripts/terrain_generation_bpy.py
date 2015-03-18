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

# impots natifs python
import os
import pickle
import pprint
import random
import math
from mathutils import *
from copy import deepcopy
import sys
# imports de blender
import bpy
# importations du module local
sys.path.append("/home/jimy/blender/the-grid/terrain/scripts")
import definitions

class TerrainNode(object) :
	dir = 0 # orientation (0, 90, 180 ou 270) en degrés
	exists = False
	def __init__(self, dir=0, exists=False) :
		self.dir = dir
		self.exists = exists

def create_matrix(unit=0, dimensions=[1]) :
	dimensions = list(dimensions)
	dimensions.reverse()
	if len(dimensions) :
		mat = []
		for i in range(dimensions[0]) :
			mat.append(unit)
	for dim in dimensions[1:] :
		u = mat
		mat = []
		for i in range(dim) :
			mat.append(deepcopy(u))
	return mat

#def generate_cloud(position=Vector((0,0,0), dimensions = Vector((200,200,200))) :



class Terrain(object):
	"""Cet objet représente le terrain. Il permet de le génerer et de le détruire."""
	# constantes
	
	# constructeur
	def __init__(self, hmax=300, hmin=-100, pathfile="./terrain.data"):
		"""Instancie la classe avec les parametres.
		hmax est l'altitude en bu (blender units)
		hmin est l'altitude minimale que peut prendre un relief.
		"""
		# creation des variables internes
		self.hmax, self.hmin = hmax, hmin
		self.pathfile = pathfile
		# creation de l'inventaire des zones déja générées. Si le fichier inventaire n'existe pas, il est créé, 
		# et un inventaire vide est utilisé
		try:
			f = open(self.pathfile, 'r')
		except FileNotFoundError:
			self.generated_zone_ids = set()
			print("WARNING: no terrain file found, using "+os.getenv("PWD")+" for future saving directory.")
		else:
			data = f.read()
			f.close()
			if pathfile.split('.')[-1] in {"data", "bin"} :
				# cas d'un fichier binaire : utilisation de pickle
				self.generated_zone_ids = set(pickle.loads(data))
			else :
				# cas d'un fichier texte (surement écrit par pprint) : utilisation de eval
				self.generated_zone_ids = set(eval(data))
		# importation des mesh des objets
		library = bpy.types.BlendDataLibraries.load("//basic_terrain.blend", link=True, relative=True)
		# La manipulation suivant peut paraitre étrange. 'with' va appeller library.__enter__ qui retourne un
		# tuple de 2 descripteur de fichier blender, le premier est celui du fichier chargé, le second permet
		# d'ajouter au fichier courant.
		with library as (data_from, data_to) :
			data_to.meshes = data_from.meshes
		# Et voila ! le fichier courant contient les mesh de l'autre fichier
		
	
	def generate(self, xmin, xmax, ymin, ymax, density=2):
		"""Génere le terrain dans la zone indiquée.
		Les coordonnéées sont horizontales.
		"""
		# constantes de l'algorithme
		basic_interval = 8. # interval de base entre les reliefs : 10m
		z_max_interval = 10. # interval de hauteur maximal entre 2 blocs joints : 4m
		# constantes de la fonction
		res_x = int((xmax-xmin)/basic_interval)
		res_y = int((ymax-ymin)/basic_interval)
		#res_z = int((self.hmax-self.hmin)/basic_interval)
		res_z = 4
		
		c_matrix = create_matrix(TerrainNode(), (res_x, res_y, res_z)) # matrice de blocs
		
		# ajouter un sol en piere de base
		mesh_n = definitions.stone_floor
		object_n = mesh_n+".000"
		floor = bpy.data.objects.new("none", bpy.data.meshes[mesh_n])
		floor.name = object_n
		floor.location.x = xmin+(xmax-xmin)/2
		floor.location.y = ymin+(ymax-ymin)/2
		floor.location.z = 0
		floor.dimensions = Vector(((xmax-xmin), (ymax-ymin), 1))
		bpy.context.scene.objects.link(bpy.data.objects[floor.name])
		print("floor set")
		# creer les massifs
		for i in range(0, int((random.random()+density)*math.sqrt(res_x*res_y))) :
			# decision de la taille du massif
			sizex = int((random.random()*6)+1)
			sizey = int((random.random()*6)+1)
			stages = int((random.random()*4)+1)
			dir = random.choice([0., math.pi/2, math.pi, math.pi*3/2])
			startx = int(random.random()*res_x)
			starty = int(random.random()*res_y)
			print("new macrobloc : starting at "+str((startx,starty))+" with size of "+str((sizex,sizey,stages)))
			
			if startx+sizex > res_x : sizex = res_x-startx
			if starty+sizey > res_y : starty = res_y-starty
			
			mat = create_matrix(True, (sizex, sizey))
			
			# retirer les bords
			possibilities = [(0,0), (1,0), (0,1)]
			posx, posy = 0, 0
			for i in range(5) :
				x, y = random.choice(possibilities)
				posx += x
				posy += y
				if posx < sizex and posy < sizey :
					print("remove at "+str((posx,posy)))
					mat[posx][posy] = False
				else :
					posx -= x
					posy -= y
			
			# ajouter les etages
			for s in range(stages) :
				for y in range(sizey) :
					for x in range(sizex) :
						if mat[x][y] == True :
							X = x+startx
							Y = y+starty
							print("dir = "+str(dir)+"\t\t"+str(math.pi/2)+"   "+str(math.pi*3/2)+"   "+str(math.pi))
							if dir == 0. :            X += s
							elif dir == math.pi/2 :   Y += s
							elif dir == math.pi :     X -= s
							elif dir == math.pi*3/2 : Y -= s
							
							if X >= 0 and X < res_x and Y >= 0 and Y < res_y :
								c_matrix[X][Y][s] = TerrainNode(exists=True, dir=dir)
						else : 
							c_matrix[x+startx][y+starty][s] = TerrainNode(exists=False, dir=0)
						#print(str((x+startx,y+starty,s))+"\t"+str(c_matrix[x+startx][y+starty][s].exists))
		
		
			for s in range(stages-1) :
				for y in range(sizey) :
					for x in range(sizex) :
						if X >= 1 and X < res_x-1 and Y >= 1 and Y < res_y-1   and c_matrix[X][Y-1][s].exists and c_matrix[X][Y+1][s].exists and c_matrix[X-1][Y][s].exists	and c_matrix[X+1][Y][s].exists :
							c_matrix[X][Y][s].exists = False
		
		# enlever les blocs inutiles
		for z in range(res_z) :
			for y in range(res_y) :
				for x in range(res_x) :
					#print(str((x,y,z))+"\t"+str(c_matrix[x][y][z].exists))
					if c_matrix[x][y][z].exists == True :
						mesh_name = random.choice(definitions.all_blocs)		
						location = Vector((
							x*basic_interval+xmin,
							y*basic_interval+ymin,
							z*basic_interval+0
							))
						rotation = Euler((0,0, c_matrix[x][y][z].dir))
						r = random.random()
						scale = Vector((1.5+r,1.5+r,1.5+r))
				
						# ajouter le bloc
						object_name = "new"
						bloc = bpy.data.objects.new(object_name, bpy.data.meshes[mesh_name])
						bloc.name = "terrain-generated "+mesh_name
						bloc.location = location
						bloc.rotation_euler = rotation
						bloc.scale = scale
						bpy.context.scene.objects.link(bpy.data.objects[bloc.name])
						#print("added : \""+object_name+"\" with mesh \""+mesh_name+"\" at coordinates "+str(location))
		
	
	def ungenerate(self, xmin, ymin, xmax, ymax):
		"""Supprime le terrain dans la zone indiquée.
		Les coordonnées sont horizontales.
		"""

if __name__ == "__main__" :
	terrain = Terrain()
	terrain.generate(-200, 200,   -200, 200)
