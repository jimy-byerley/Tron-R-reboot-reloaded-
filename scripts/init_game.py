import bge
import sys

# normaly the main scene is located in scenes directory
gamepath = bge.logic.expandPath('//..')

sys.path.append(gamepath+'/scripts')
sys.path.append(gamepath+'/mods')
