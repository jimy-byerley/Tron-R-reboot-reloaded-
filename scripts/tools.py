import bge
import threading
import time

## replacement of bge.logic.LibLoad() to avoid crashes ##

can_load = True
class LibLoader(threading.Thread):
	def __init__(self, blend, type, load_actions, verbose, load_scripts, async):
		threading.Thread.__init__(self)
		self.blend        = blend
		self.type         = type
		self.load_actions = load_actions
		self.verbose      = verbose
		self.load_scripts = load_scripts
		self.async        = async
	def run(self):
		global can_load
		while not can_load:   time.sleep(0.05)
		can_load = False
		self.status = bge.logic.LibLoad( self.blend, self.type, 
			load_actions = self.load_actions, 
			verbose      = self.verbose, 
			load_scripts = self.load_scripts, 
			async        = True)
		time.sleep(1)
		can_load = True
"""
def LibLoad(blend, type, load_actions=False, verbose=False, load_scripts=True, async=False):
	loader = LibLoader(blend, type, load_actions, verbose, load_scripts, async)
	if async:   loader.start()
	else:       loader.run()
	return loader.status
"""

def finish_loading(status):
	global can_load
	print('called')
	delay(1)
	can_load = True

def LibLoad(blend, type, load_actions=False, verbose=False, load_scripts=True, async=False):
	global can_load
	while not can_load:
		print('ok')
		time.sleep(0.5)
	can_load = False
	status = bge.logic.LibLoad(blend, type, load_actions=load_actions, verbose=verbose, load_scripts=load_scripts, async=async)
	if async:
		status.onFinish = finish_loading
	else:
		can_load = True