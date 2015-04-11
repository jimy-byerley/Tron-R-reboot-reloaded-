import bge
import scenes

owner = bge.logic.getCurrentController().owner

if bge.logic.canstop == 0:
	print('quitting')
	bge.logic.endGame()

