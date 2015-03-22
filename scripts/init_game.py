import bge
import sys

# normaly the main scene is located in scenes directory
game_path = bge.logic.expandPath('//..')
bge.logic.game_path = game_path

sys.path.append(game_path+'/scripts')
sys.path.append(game_path+'/mods')
