# -*- coding: utf-8 -*-

import socket, time, random



class SecurityV01(object) :
	"""
	La classe Security(object) représente les normes de sécurisation de la connexion sécurisée pour les classes
	SecuredServer et SecuredClient. Cette classe permet normalement de n'avoir pas à gerer le codage et les
	normes de sécurité dans le client et dans le serveur. Cela évite des bugs liés à des oublis.

	Le principe de ce codage est que la clé change en fonction du temps, selon une règle définie.

	ATTENTION: ce cryptage fonctionne mal avec des caractères accentués mème encodés.
	"""
	version = "0.1"
	def __init__(self, key, offset, time_interval=60, time_offset=0) :
		"""
		(bytes|str) key             est la clef initiale au début de la connexion (elle le demeure pendant le
		                            time_interval). key est une chaine d'octets.
		(int) offset                est le décalage qui s'opère à chaque fin du time_interval.
		(int|float) time_interval   est l'interval de temps en secondes entre chaque changement de clef.
		(int|float) time_offset     est le décalage entre l'horloge locale et celle de l'interlocuteur.
		"""
		self.time_interval = time_interval
		self.time_offset = time_offset
		self.offset = offset
		self.key = key
	
	def __repr__(self) :
		"""x  <==>  eval(x.__repr__())"""
		return "{}(key={}, offset={}, time_interval={}, time_offset={})".format(
			self.__class__.__name__,
			repr(self.key),
			repr(self.offset),
			repr(self.time_interval),
			repr(self.time_offset),
			);

	def encode(self, buffer) :
		"""
		(bytes|str) buffer	est la chaine d'octets à encoder.
		(bytes) return	la chaine d'octets encodée.
		"""
		buffer = bytes(buffer)
		crypted = b""
		for i in range(len(buffer)) :
			byte = chr((
				buffer[i]
				+ int(self.key[i%len(self.key)])
				+ int(self.offset[i%len(self.offset)]) * int(time.time()/self.time_interval)
				) % 127)
			crypted += byte.encode()
		return crypted

	def decode(self, buffer) :
		"""
		(bytes|str) buffer	est la chaine d'octets à décoder.
		(bytes) return	la chaine d'octets décodée.
		"""
		buffer = bytes(buffer)
		decrypted = b""
		for i in range(len(buffer)) :
			byte = chr((
				buffer[i]
				- int(self.key[i%len(self.key)])
				- int(self.offset[i%len(self.offset)]) * int(time.time()/self.time_interval)
				) % 127)
			decrypted += byte.encode()
		return decrypted





class SecurityV02(SecurityV01) :
	"""
	La classe Security(object) représente les normes de sécurisation de la connexion sécurisée pour les classes
	SecuredServer et SecuredClient. Cette classe permet normalement de n'avoir pas à gerer le codage et les
	normes de sécurité dans le client et dans le serveur. Cela évite des bugs liés à des oublis.

	Le principe de ce codage est que la clé change en fonction du temps, selon une règle définie.

	Ce codage prend en charge les accents, et tous les caracteres reconnus par les chaines Python (str).
	Ce codage est aussi plus sécurisé que SecurityV01 car le codage des caracteres de la classe str se fait sur plusieurs octets et donc la clés de cryptage est plus grande. De plus pour casser le code, il faut que le logiciel utilisé prennent en compte ce codage.
	"""
	version = "0.2";  # Seul un protocole est utilisé par la suite, il peut etre interessant de pouvoir connaitre laquelle.
	MAX_CHR = 0x10ffff; # chiffre tiré de la page help() de chr()
	
	def __init__(self, key, offset, time_interval=60, time_offset=0) :
		"""
		(str) key                   est la clef initiale au début de la connexion (elle le demeure pendant le
		                            time_interval). key est une chaine de caractères.
		(str) offset                est le décalage (par caractère) qui s'opère à chaque fin du time_interval.
		(int|float) time_interval   est l'interval de temps en secondes entre chaque changement de clef.
		(int|float) time_offset     est le décalage entre l'horloge locale et celle de l'interlocuteur. Si
		                            l'horloge de l'interlocuteur est en avance par rappport à celle locale, il fait que
		                            cette valeur soit positive.
		"""
		self.time_interval = time_interval;
		self.time_offset = time_offset;
		self.offset = offset;
		self.key = key;

	def encode(self, buffer) :
		"""
		(bytes|str) buffer  est la chaine de caractères à encoder.
		(str) return	    la chaine de caractères encodée (sur une chaine de caractères).
		"""
		if type(buffer) == bytes : buffer = buffer.decode();
		crypted = ""
		for i in range(len(buffer)) :
			char = chr((
				ord(buffer[i])
				+ ord(self.key[i%len(self.key)])
				+ ord(self.offset[i%len(self.offset)]) * int(time.time()/self.time_interval)
				) % self.MAX_CHR)
			crypted += char;
		return crypted

	def decode(self, buffer) :
		"""
		(bytes|str) buffer  est la chaine de caractères à décoder.
		(str) return        la chaine de caractères décodée.
		"""
		if type(buffer) == bytes : buffer = buffer.decode();
		decrypted = ""
		for i in range(len(buffer)) :
			char = chr((
				ord(buffer[i])
				- ord(self.key[i%len(self.key)])
				- ord(self.offset[i%len(self.offset)]) * int(time.time()/self.time_interval)
				) % self.MAX_CHR)
			decrypted += char;
		return decrypted





Security = SecurityV02;


def jury(key, offset) :
	"""
	Default tool to determine if a key and an offset are secured. It return's True if the key and the
	offset can be considered as secured and False otherwise.
	"""
	max_chr = 0x10ffff # chiffre tiré de help(chr)

	minkeysize = 4 # minimal size of key required
	minoffsize = 3 # minimal size of offset required
	# number of key possibilities (offset is not a part of the key, and offset musn't have the same length the key lenght's)
	possibilities = max_chr ** len(key) + max_chr ** len(offset) * (len(offset) != len(key))
	minpossibilities = max_chr ** minkeysize + max_chr ** minoffsize * (minoffsize != minkeysize)
	if possibilities >= minpossibilities : return True
	else : return False



if __name__ == "__main__" :
	
	help(Security)
	if Security.version == "0.1" :
		secu = Security(b"trucen boite et choses en vrac", b"25t   67")
		print("Sécurité :", repr(secu))
		print("\n*** Sans accents dans le message original ***")
		o = "truc sans accents partout !"
		c = secu.encode(o.encode())
		d = secu.decode(c)
		print(o)
		print(o.encode())
		print(c)
		print(d)
		print(d.decode())
		print("\n*** Avec des accents partout ***")
		o = "truc àvec dés äccènts pârtôüt !"
		c = secu.encode(o.encode())
		d = secu.decode(c)
		print(o)
		print(o.encode())
		print(c)
		print(d)
		print(d.decode())
	
	elif Security.version =="0.2":
		secu = Security("trucen boité et choses en vrac", "25t ä  67")
		print("Sécurité :", repr(secu))
		print("\n*** Sans accents dans le message original ***")
		o = "truc sans accents partout !"
		c = secu.encode(o)
		d = secu.decode(c)
		print(o)
		print(c.encode())
		print(d)
		print("\n*** Avec des accents partout ***")
		o = "truc àvec dés äccènts pârtôüt !"
		c = secu.encode(o)
		d = secu.decode(c)
		print(o)
		print(c.encode())
		print(d)
	