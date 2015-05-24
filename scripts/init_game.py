import bge
import sys

# use argv
config_file = None
game_file = None

i = 0
while sys.argv[i] != '-' and i < len(sys.argv) : i += 1
i += 1
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
game_path = bge.logic.expandPath('//../')
bge.logic.game_path = game_path

sys.path.append(game_path+'/scripts')
sys.path.append(game_path+'/mods')

bge.logic.scene_path = game_path+'/scenes'
bge.logic.models_path = game_path+'/models'
bge.logic.sounds_path = game_path+'/sounds'

import scenes
import backup_manager
import avatar
import item
import character

## load global configuration file ##

try: f = open(bge.logic.expandPath("//../config.txt"), 'r')
except IOError:
	print('config.txt not found, use default values instead.')
else:
	lines = f.readlines()
	f.close()
	config = {}
	for line in lines:
		line = line.expandtabs()
		name = ""
		value = ""
		i = 0
		while line[i] != ' ':	i += 1
		name = line[:i]
		j = i
		while line[i] == ' ':	i += 1
		while line[j] != '\n':	j += 1
		value = line[i:j]
		config[name] = eval(value)

bge.logic.config = config

### thread usage ###

bge.logic.canstop = 0
# when creating a thread, add 1 to this value, when thread ends, substract 1 to this value

## load game backup (last in config file or specified in commandline) ##

if not game_file and 'game_backup' in config:
	game_file = config['game_backup']
if game_file:
	print('loading backup file \"%s\"' % game_file)
	backup_manager.loadbackup(game_file, async=False)
	backup_manager.save_file = game_file
	backup_manager.autosave = True

## load scenes in direct environment ##

scene = bge.logic.getCurrentScene()
fp_dump = None
if game_file:
	for dump in backup_manager.last_backup['characters']:
		if dump['id'] == config['object_id']:
			fp_dump = dump

if fp_dump == None :
	spawner = scene.addObject("first player spawn", scene.active_camera)
	spawner['character_name'] = config['nickname']
	spawner['skin'] = config['skin']	
else:
	scene.active_camera.worldPosition = fp_dump['pos']
	scenes.thread_loader()
	backup_manager.thread_loader()
	avatar.init_noauto(config, fp_dump)

root = scene.addObject("root", scene.active_camera)
root['FXAA']         = config['filter_FXAA']
root['bloom']        = config['filter_bloom']
root['history_mode'] = config['filter_history_mode']
root['field_depth']  = config['filter_field_depth']

scenes.load_async = True
item.load_async = True
character.load_async = True
print('Game initialized')