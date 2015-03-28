import bge
import scenes

owner = bge.logic.getCurrentController().owner

if bge.logic.canstop == 0:
	bge.logic.endGame()
