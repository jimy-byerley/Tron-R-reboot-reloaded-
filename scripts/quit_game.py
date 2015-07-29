import os, signal
import bge
import scenes

owner = bge.logic.getCurrentController().owner

# restart parent process
if bge.logic.launcher_process != None and 'game_launcher_stop' in bge.logic.config and bge.logic.config['game_launcher_stop']:
    os.kill(bge.logic.launcher_process, signal.SIGCONT)

# stop client
if bge.logic.client:
    bge.logic.client.stop()

# stop game if it is possible
if bge.logic.canstop == 0:
	print('quitting')
	bge.logic.endGame()

