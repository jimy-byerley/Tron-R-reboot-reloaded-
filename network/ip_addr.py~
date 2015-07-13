# imports
import errno
import socket

# localhost prefixes
_local_networks = ("127.", "0:0:0:0:0:0:0:1")

# ignore these prefixes -- localhost, unspecified, and link-local
_ignored_networks = _local_networks + ("0.", "0:0:0:0:0:0:0:0", "169.254.", "fe80:")

def detect_family(addr):
	if "." in addr:
		assert ":" not in addr
		return socket.AF_INET
	elif ":" in addr:
		return socket.AF_INET6
	else:
		raise ValueError("invalid ipv4/6 address: %r" % addr)

def expand_addr(addr):
	"""convert address into canonical expanded form --
	no leading zeroes in groups, and for ipv6: lowercase hex, no collapsed groups.
	"""
	family = detect_family(addr)
	addr = socket.inet_ntop(family, socket.inet_pton(family, addr))
	if "::" in addr:
		count = 8-addr.count(":")
		addr = addr.replace("::", (":0" * count) + ":")
		if addr.startswith(":"):
			addr = "0" + addr
	return addr

def _get_local_addr(family, remote):
	try:
		s = socket.socket(family, socket.SOCK_DGRAM)
		try:
			s.connect((remote, 9))
			return s.getsockname()[0]
		finally:
			s.close()
	except socket.error:
		return None

def get_local_addr(remote=None, ipv6=True):
	"""get LAN address of host

	:param remote:
		return  LAN address that host would use to access that specific remote address.
		by default, returns address it would use to access the public internet.

	:param ipv6:
		by default, attempts to find an ipv6 address first.
		if set to False, only checks ipv4.

	:returns:
		primary LAN address for host, or ``None`` if couldn't be determined.
	"""
	if remote:
		family = detect_family(remote)
		local = _get_local_addr(family, remote)
		if not local:
			return None
		if family == socket.AF_INET6:
			# expand zero groups so the startswith() test works.
			local = expand_addr(local)
		if local.startswith(_local_networks):
			# border case where remote addr belongs to host
			return local
	else:
		# NOTE: the two addresses used here are TESTNET addresses,
		#	   which should never exist in the real world.
		if ipv6:
			local = _get_local_addr(socket.AF_INET6, "2001:db8::1234")
			# expand zero groups so the startswith() test works.
			if local:
				local = expand_addr(local)
		else:
			local = None
		if not local:
			local = _get_local_addr(socket.AF_INET, "192.0.2.123")
			if not local:
				return None
	if local.startswith(_ignored_networks):
		return None
	return local





def speed_get_addr():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(('8.8.8.8', 0))  # connecting to a UDP address doesn't send packets
	return s.getsockname()[0]
