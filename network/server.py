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
				if dst != host and dst != 'all': server.queue[host].append(packet)
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
			for other in server.hosts:
				if other in server.avatars.keys() and server.avatars[other] == idbytes: 
					print('error: avatar_callback: an other host got already avatar', idbytes)
					return True
			server.avatars[host] = idbytes
			server.datas[idbytes].host = server.hosts.index(host)
		# only registered avatars associated with the good host can provid theses informations
		elif server.avatars[host] == idbytes:
			# send to all except to source host
			for dst in server.hosts:
				if dst != host and dst != 'all': server.queue[dst].append(b'character'+packet[6:])
		else:
			return False
		return True
	return False
			

network.Server.avatars = {} # list of ID's of avatars for each host (as bytes), referenced by host
network.Server.callbacks.append(avatar_callback)
