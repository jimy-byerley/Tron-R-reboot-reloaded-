import network
from network import similar

def character_callback(server, packet, host):
	if similar(packet, b'character\0'):
		if packet.count(b'\0') < 3: return True
		uniqid = packet.split(b'\0')[2]
		if not uniqid.isdigit(): return True
		uniqid = int(uniqid)
		if uniqid not in server.datas.keys(): return True
		if server.datas[uniqid].host == server.hosts.index(host):
			# send to all except to source host
			for dst in server.hosts:
				if dst != host and dst != 'all': server.add_to_queue(packet, host)
			return True
	return False

network.Server.callbacks.append(character_callback)

def avatar_callback(server, packet, host):
	if similar(packet, b'avatar\0'):
		if packet.count(b'\0') < 3: return True
		idbytes = packet.split(b'\0')[2]
		if idbytes not in server.datas.keys(): 
			print('error: avatar_callback: avatar', idbytes, "doesn't exist")
			return True
	
		# if host has no known avatar, then register it.
		if host not in server.avatars.keys():
			for other in server.avatars.keys():
				if other in server.hosts and server.avatars[other] == idbytes: 
					print('error: avatar_callback: an other host got already avatar', idbytes)
					return True
			server.avatars[host] = idbytes
			server.datas[idbytes].host = server.hosts.index(host)
		# only registered avatars associated with the good host can provid theses informations
		elif server.avatars[host] == idbytes:
			# send to all except to source host
			for dst in server.hosts:
				if dst != host and dst != 'all': server.add_to_queue(b'character'+packet[6:], dst)
		else:
			return False
		return True
	return False
			

network.Server.avatars = {} # list of ID's of avatars for each host (as bytes), referenced by host
network.Server.callbacks.append(avatar_callback)

def vehicle_callback(server, packet, host):
	if similar(packet, b'vehicle\0'):
		if packet.count(b'\0') < 3: return True
		info, idbytes = packet.split(b'\0', maxsplit=3)[1:3]
		if idbytes not in server.datas.keys(): 
			print('error: vehicle_callback: vehicle', idbytes, "doesn't exist")
			return True
		'''
		# if host has no known vehicle, then register it.
		if host not in server.vehicles.keys():
			for other in server.vehicles.keys():
				if other in server.hosts and server.vehicles[other] == idbytes: 
					print('error: vehicle_callback: an other host drive already a vehicle', idbytes)
					return True
			server.vehicles[host] = idbytes
			server.datas[idbytes].host = server.hosts.index(host)
			# to tell the client that it is this ID that is driven by this character
			server.add_to_queue(b'drive\0'+str(server.hosts.index(host)).encode()+b'\0'+idbytes)
		# only registered vehicles associated with the good host can provide theses informations
		elif server.vehicles[host] == idbytes:
			if info == b'destroy':
				del server.vehicles[host]
			# send to all except to source host
			for dst in server.hosts:
				if dst != host and dst != 'all': server.add_to_queue(packet, dst)
		else:
			return False
		return True
		'''
		data = server.datas[idbytes]
		index = server.hosts.index(host)
		if data.host != index: 
			if data.host < index:
				data.host = index # an instance works as a pointer
			return True
		
		# on setting a new driver, the, use the same host to provide the vehicle informations
		if info == b'drive':
			if data.isdigit() and data in self.datas:
				data.host = self.datas[data].host
		
		elif info == b'destroy' or info == b'remove':
			del server.datas[idbytes]
			return True
		elif info == b'exit':
			data.host = None
		for dst in server.hosts:
			if dst != host: server.add_to_queue(packet, dst)
		
	return False
