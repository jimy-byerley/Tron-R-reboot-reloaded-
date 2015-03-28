import bge
import sys

# normaly the main scene is located in scenes directory
game_path = bge.logic.expandPath('//..')
bge.logic.game_path = game_path

sys.path.append(game_path+'/scripts')
sys.path.append(game_path+'/mods')

import scenes

bge.logic.scene_path = game_path+'/scenes'

### thread usage ###

bge.logic.canstop = 0
# when creating a thread, add 1 to this value, when thread ends, substract 1 to this value
