import bge
import scenes

owner = bge.logic.getCurrentController().owner

if bge.logic.client:
    bge.logic.client.stop()

if bge.logic.canstop == 0:
	print('quitting')
	bge.logic.endGame()

