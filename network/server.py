import network
from network import similar

def character_callback(server, packet, host):
	if similar(packet, b'character\0'):
		if packet.count(b'\0') < 3: return True
		uniqid = packet.split(b'\0')[2]
		if not uniqid.isdigit(): return True
		uniqid = int(uniqid)
		if uniqid not in server.datas: return True
		if server.datas[uniqid].host == server.hosts.index(host):
			server.queue['all'].append(packet)
			return True
	return False

network.Server.callbacks.append(character_callback)

def avatar_callback(server, packet, host):
	if similar(packet, b'avatar\0'):
		if packet.count(b'\0') < 3: return True
		uniqid = packet.split(b'\0')[2]
		if not uniqid.isdigit(): return True
		uniqid = int(uniqid)
		if uniqid not in server.datas: return True
		# if host has no known avatar, then register it.
		if host not in server.avatars.keys():
			for other in server.hosts:
				if server.avatars[other] == uniqid: return True
			server.avatars[host] = uniqid
		# only registered avatars associated with the good host can provid theses informations
		elif server.avatars[host] == uniqid:
			server.queue['all'].append(packet)
		else:
			return False
		return True
	return False
			

network.Server.avatars = {} # list of ID's of avatars for each host, referenced by host
network.Server.callbacks.append(avatar_callback)
