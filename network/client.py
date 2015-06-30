import bge
import threading, socket, time
import network

class Client(socket.socket):
	packet_size = 1024
	
	def __init__(self, remote):
		self.remote = remote
		socket.socket.__init__(self, socket.AF_INET, socket.SOCK_DGRAM)
		socket.connect(remote)
	
	def step(self):
		
	
	# clear the socket's queue, return the list of packet received
	def clear_requests(self):
		queue = []
		received=b'\0'
		while len(received):
			received = self.recv()
			queue.append(received)
		return queue