# Fichier de configuration basique
# constantes pour les touches :
# https://www.blender.org/documentation/blender_python_api_2_70a_release/bge.events.html#keyboard-keys

# utilisation des codes des touches
from bge.events import *

class keys:
	forward = ZKEY
	back = SKEY
	right = DKEY
	left = QKEY
	jump = SPACEKEY
	run = LEFTSHIFTKEY

	toggle_fps = CKEY
	toggle_tps = VKEY

	# actions sur les items
	drop = AKEY
	item1 = ONEKEY
	item2 = TWOKEY
	item3 = THREEKEY
	
	toggle_helmet = HKEY
	
	pause_menu = ESCKEY

class mouse:
	sensibility = 0.002

class interact:
	# actions sans item
	take = LEFTMOUSE

	# actions avec des items
	itemaction1 = LEFTMOUSE
	itemaction2 = RIGHTMOUSE
	itemaction3 = MIDDLEMOUSE
	action4 = WHEELUPMOUSE
	action5 = WHEELDOWNMOUSE

class vehicle:
	# keys
	keyford = keys.forward
	keyback = keys.back
	keyleft = keys.left
	keyright = keys.right
	keyboost = keys.run
