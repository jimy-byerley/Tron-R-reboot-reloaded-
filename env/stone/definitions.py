# Ce fichier sert à déclarer les mesh des blocs
# Les declarations fournissent le nom des mesh dans le fichier blender d'origine

import bpy

blocs = [ # les blocs sont des formes simples
	"terrain-cube.000",
	"terrain-cube.001",
	"terrain-cube.006",
	"terrain-cube.008",
	"terrain-cube.009",
	"terrain-cube.010",
] 

volumes = [ # les volumes sont des formes complexes
	"terrain-volume.000",
	"terrain-volume.001",
	"terrain-volume.002",
]

stone_floor = "stone-floor"
basic_grid = "basic-grid"

all_blocs = blocs+volumes # la liste rassemble blocs et volumes

