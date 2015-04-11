import bge
import sys

# use argv
config_file = None
game_file = None

i = 0
while i < len(sys.argv):
	arg = sys.argv[i]
	if arg in ('-c', '--config'):
		config_file = sys.argv[i+1]
		i += 1
	elif arg in ('-l', '--load'):
		game_file = sys.argv[i+1]
		i += 1
	else:
		print('unknown argument', arg)
		#bge.logic.endGame()
	i += 1

# normaly the main scene is located in scenes directory
game_path = bge.logic.expandPath('//..')
bge.logic.game_path = game_path

sys.path.append(game_path+'/scripts')
sys.path.append(game_path+'/mods')

bge.logic.scene_path = game_path+'/scenes'
bge.logic.models_path = game_path+'/models'

import scenes
import backup_manager


if game_file:
	print('loading backup file \"%s\"' % game_file)
	backup_manager.loadbackup(game_file)
	backup_manager.save_file = game_file
	backup_manager.autosave = True

### thread usage ###

bge.logic.canstop = 0
# when creating a thread, add 1 to this value, when thread ends, substract 1 to this value
