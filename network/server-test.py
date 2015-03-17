#!/usr/bin/python3
from server import *
from time import *
from pprint import pprint

s = GameServer(15000)
s.start()
s.accept()
while True:
	print(s.hosts)
	pprint(s.datas)
	sleep(1)
