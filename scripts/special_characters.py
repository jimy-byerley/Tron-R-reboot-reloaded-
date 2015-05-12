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

MOVE_ACTION = "move action"
ITEM_ACTION = "item action"
HEADZ_ACTION = "head Z"
HEADY_ACTION = "head Y"

# dictionnary of all characters animations
animations = {
	
	'clu' : { # animations pour CLU
		"click" : ('clu item', 285, 289, 290, 292),
		# disk actions
		#"launch disk" : ('clu item', 90, 103, 104, 120),
		"launch disk" : ('clu move', 120, 130, 131, 140),
		"catch disk" : ('clu item', 257, 257, 270, 270),
		"take disk" : ('clu item', 60, 64, 66, 74),
		# light-baton and cycle actions
		"take light baton" : ('clu item', 241, 249, 249, 253),
		"set cycle" : ('clu move', 216, 220, 224, 228), # départ, dabut de saut, prise 2 mains, position de conduite
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
		
	'monitor' : { # animations pour Moniteur
		"click" : ('monitor item', 85, 88, 80, 94),
		# disk actions
		"take disk" :('monitor item', 0, 6, 8, 15),
		"launch disk" : ('monitor item', 50, 56, 57, 61),
		"catch disk" : ('monitor item', 70, 73, 77, 81),
		# light-baton and cycle actions
		"take light baton" : ('monitor item', 20, 25, 27, 30),
		"set cycle" : ('monitor move', 117, 119, 129, 135),
		"biking with disk" : ('monitor move', 150, 155, 155, 160),
		"biking take disk" : ('monitor item', 35, 39, 39, 44),
		# head movements
		"look Z" : ('monitor head Z', 0, 5, 5, 10),
		"look Y" : ('monitor head Y', 0, 5, 5, 10),
		# basic movements
		"walk ford" : ('monitor move', 14, 21, 40, 46),
		"walk back" : ('monitor move', 46, 40, 21, 14),
		"run ford" : ('monitor move', 55, 62, 74, 80),
		"jump" : ('monitor move', 90, 95, 98, 104),
		},
	}

# dynamicaly defined animations
animations['flynn'] = animations['clu']

# some prefixes
models = 'models/'
special_characters = models+'characters/'

# locations of file of all skins
files = {
	'clu' : special_characters+'clu.blend',
	'flynn' : special_characters+'flynn.blend',
	'monitor' : special_characters+'monitor.blend',
	}
