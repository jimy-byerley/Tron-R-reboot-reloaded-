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
import pprint
import random
import math
from copy import *
from mathutils import *
import bge

### DECLARATIONS DES COMPOSANTS #########################

blocs = [ # les blocs sont des formes simples
	#"terrain-cube.001",
	#"terrain-cube.006",
	#"terrain-cube.007",
	#"terrain-cube.009",
	#"terrain-cube.010",
]

volumes = [ # les volumes sont des formes complexes
	"terrain-volume.000",
	"terrain-volume.001",
	"terrain-volume.002",
	"terrain-volume.003",
	"terrain-volume.004",
	"terrain-volume.005",
]

stone_floor = "stone-floor"
basic_grid = "basic-grid"

all_blocs = blocs+volumes # la liste rassemble blocs et volumes

### CODE DE GENERATION ##################################

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
	def __init__(self, hmax=300, hmin=-100):
		"""Instancie la classe avec les parametres.
		hmax est l'altitude en bu (blender units)
		hmin est l'altitude minimale que peut prendre un relief.
		"""
		# creation des variables internes
		self.hmax, self.hmin = hmax, hmin


	def generate(self, xmin, xmax, ymin, ymax, zmin, zmax, scene, ref, density=2):
		"""Génere le terrain dans la zone indiquée.
		Les coordonnéées sont horizontales.
		ref est l'objet de reférence pour le placement.
		"""
		# constantes de l'algorithme
		basic_interval = 20. # interval de base entre les reliefs
		z_max_interval = 15. # interval de hauteur maximal entre 2 blocs joints
		# constantes de la fonction
		res_x = int((xmax-xmin)/basic_interval)
		res_y = int((ymax-ymin)/basic_interval)
		#res_z = int((self.hmax-self.hmin)/basic_interval)
		res_z = max(int((zmax-zmin)/z_max_interval), 1)

		c_matrix = create_matrix(TerrainNode(), (res_x, res_y, res_z)) # matrice de blocs

		# ajouter un sol en piere de base
		"""
		mesh_n = stone_floor
		object_n = mesh_n
		floor = scene.addObject(object_n, ref)
		floor.worldPosition.x = xmin+(xmax-xmin)/2
		floor.worldPosition.y = ymin+(ymax-ymin)/2
		floor.worldPosition.z = 0
		floor.worldScale = Vector(((xmax-xmin), (ymax-ymin), 1))
		print("floor set")
		"""
		# creer les massifs
		for i in range(0, int((random.random()+density)*math.sqrt(res_x*res_y))) :
			# decision de la taille du massif
			sizex = random.randrange(1,7)
			sizey = random.randrange(1,7)
			stages = random.randrange(0,res_z+1)
			dir = random.choice([0., math.pi/2, math.pi, math.pi*3/2])
			startx = int(random.random()*res_x)
			starty = int(random.random()*res_y)
			#print("new macrobloc : starting at "+str((startx,starty))+" with size of "+str((sizex,sizey,stages)))

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
					#print("remove at "+str((posx,posy)))
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
							#print("dir = "+str(dir)+"\t\t"+str(math.pi/2)+"   "+str(math.pi*3/2)+"   "+str(math.pi))
							if dir == 0. :            X += s
							elif dir == math.pi/2 :   Y += s
							elif dir == math.pi :     X -= s
							elif dir == math.pi*3/2 : Y -= s

							if X >= 0 and X < res_x and Y >= 0 and Y < res_y :
								c_matrix[X][Y][s] = TerrainNode(exists=True, dir=dir)
						else :
							c_matrix[x][y][s] = TerrainNode(exists=False, dir=0)
						#print(str((x+startx,y+starty,s))+"\t"+str(c_matrix[x+startx][y+starty][s].exists))


			for s in range(stages-1) :
				for y in range(sizey) :
					for x in range(sizex) :
						X = x+startx
						Y = y+starty
						if X >= 1 and X < res_x-1 and Y >= 1 and Y < res_y-1   and c_matrix[X][Y-1][s].exists and c_matrix[X][Y+1][s].exists and c_matrix[X-1][Y][s].exists	and c_matrix[X+1][Y][s].exists :
							c_matrix[X][Y][s].exists = False

		# enlever les blocs inutiles
		for z in range(res_z) :
			for y in range(res_y) :
				for x in range(res_x) :
					#print(str((x,y,z))+"\t"+str(c_matrix[x][y][z].exists))
					if c_matrix[x][y][z].exists == True :
						name = random.choice(all_blocs)
						location = Vector((
							x*basic_interval+xmin+random.randrange(-8,8),
							y*basic_interval+ymin+random.randrange(-8,8),
							z*basic_interval+zmin+random.randrange(-8,8)
							))
						rotation = Euler((0,0, c_matrix[x][y][z].dir))
						r = random.random()
						scale = Vector((2.5+r,2.5+r,2.5+r))

						# ajouter le bloc
						bloc = scene.addObject(name, ref)
						bloc.worldPosition = location
						bloc.worldOrientation = rotation
						bloc.worldScale = scale


	def ungenerate(self, xmin, ymin, xmax, ymax):
		"""Supprime le terrain dans la zone indiquée.
		Les coordonnées sont horizontales.
		"""


def stone_area() :
	cont = bge.logic.getCurrentController()
	owner = cont.owner
	scene = bge.logic.getCurrentScene()

	t = Terrain()
	t.generate(
		owner.worldPosition.x-owner.worldScale.x,
		owner.worldPosition.x+owner.worldScale.x,
		owner.worldPosition.y-owner.worldScale.y,
		owner.worldPosition.y+owner.worldScale.y,
		owner.worldPosition.z-owner.worldScale.z,
		owner.worldPosition.z+owner.worldScale.z,
		scene, owner
		)

