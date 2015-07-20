#!/usr/bin/python3

import sys, threading

sys.path.append('.')

import network

port = 30000
if len(sys.argv) > 1: port = int(sys.argv[1])
server = network.Server(port)
server.setblocking(False)
run = True

def f():
	while run:
		server.step()

t = threading.Thread()
t.run = f
t.start()

input('type enter to stop.')

run = False
server.stop()
t.join()
server.close()
