import bge
import sys, os, signal

# use argv
config_file = None
game_file = None
game_server = None
launcher_process = None

# game arguments are passed after a '-'
i = 0
while i < len(sys.argv) and sys.argv[i] != '-' : i += 1
# analys all arguments
i += 1
while i < len(sys.argv):
	arg = sys.argv[i]
	if arg in ('-c', '--config'):
		if len(sys.argv) < i+2:
			print('missing config file after -c or --config')
		else:
			config_file = sys.argv[i+1]
		i += 1
	elif arg in ('-l', '--load'):
		if len(sys.argv) < i+2:
			print('missing game backup file after -l or --load')
		else:
			game_file = sys.argv[i+1]
		i += 1
	elif arg in ('-n', '--network'):
		if len(sys.argv) < i+5:
			print('missing server address, server port, username and password after -l or --network')
		elif not sys.argv[i+2].isnumeric():
			print('server port must be a positive integer')
		else:
			game_server = (sys.argv[i+1], int(sys.argv[i+2]), sys.argv[i+3], sys.argv[i+4])
		i += 4
	elif arg in ('-p', '--process'):
		launcher_process = int(sys.argv[i+1])
		i += 1
	else:
		print('unknown argument', arg)
		#bge.logic.endGame()
	i += 1

# normaly the main scene is located in scenes directory
game_path = bge.logic.expandPath('//../')
bge.logic.game_path = game_path

sys.path.append(game_path+'scripts')
sys.path.append(game_path+'network')
sys.path.append(game_path+'mods')

bge.logic.scene_path = game_path+'scenes'
bge.logic.models_path = game_path+'models'
bge.logic.sounds_path = game_path+'sounds'
bge.logic.filters_path = game_path+'filters'
bge.logic.shaders_path = game_path+'shaders'

import scenes
import backup_manager
import avatar
import item
import character
import filters
import client


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

## parent process (menu) stop, to optimize CPU consumption ##

bge.logic.launcher_process = launcher_process
if launcher_process != None and 'game_launcher_stop' in config and config['game_launcher_stop']:
	os.kill(launcher_process, signal.SIGTSTP)

### thread usage ###

bge.logic.canstop = 0
# when creating a thread, add 1 to this value, when thread ends, substract 1 to this value


## connect to server ##

if game_server:
	address, port, user, password = game_server
	bge.logic.client = client.Client((address, port))
	bge.logic.client.authentify(user, password)
else: 
	bge.logic.client = None

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
	if game_server:
		# in LAN game, the character must take a different name from others bots and players
		for dump in backup_manager.last_backup['characters']:
			if dump['name'] == game_server[2]:
				fp_dump = dump
				break
	else:
		# in local game, the character can take the name he wants, so the config file use the object ID to avoid confusion with a bot with the same name
		for dump in backup_manager.last_backup['characters']:
			if dump['id'] == config['object_id']:
				fp_dump = dump
				break

if fp_dump == None :
	fp_dump = {
		'name': config['nickname'],
		'skin': config['skin'],
		'id':   backup_manager.max_id,
		'pos':  (0,0,0), 
		'rot':  (0,0,0), 
		'inventory': {'hand':None},
		}
	backup_manager.max_id += 1

if game_server:
	config['nickname'] = game_server[2]
	config['skin'] = fp_dump['skin']
	config['object_id'] = fp_dump['id']
scene.active_camera.worldPosition = fp_dump['pos']
scenes.thread_loader()
backup_manager.thread_loader()
avatar.init_noauto(config, fp_dump)


## the game could be started ##
root = scene.addObject("root", scene.active_camera)
bge.logic.root = root
bge.logic.bootloader = bge.logic.getCurrentController().owner
if game_server: root['client'] = True

# setup 2D filters
for key in config.keys():
    if len(key)>7 and key[:7] == 'filter_' and config[key]:
        for filter in filters.filters:
            if filter[filters.FILTER_FILE].split('.')[0] == key[7:]:
                filters.enable_filter(filter[filters.FILTER_SHORTNAME])
                break

# setup dynamic loading
scenes.load_async = True
item.load_async = True
character.load_async = True

print('Game initialized')