import sys
import bge

loc = bge.logic.expandPath('//')
sys.path.append(loc+"/boot")
sys.path.append(loc+"/env")
sys.path.append(loc+"/env/clouds")
sys.path.append(loc+"/lib")
sys.path.append(loc+"/lib/disk")
sys.path.append(loc+"/lib/character")
sys.path.append(loc+"/lib/character/specials")
sys.path.append(loc+"/aperture/avatar")

print(sys.path)