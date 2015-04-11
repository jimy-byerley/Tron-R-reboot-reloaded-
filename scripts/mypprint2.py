indent_s = '\t'

def pprint(obj):
	print(pformat(obj))

def pformat(obj):
	return _pformat(obj)[0]

def _pformat(obj, indent=0, reindent=None):
	buff = ""
	n_lines = 0
	if reindent == None: reindent = indent+1	
	
	if type(obj) == dict:
		if len(obj) > 3 or n_lines:
			buff += indent_s*indent+"{"
			for key in obj:
				rep_key, key_lines = _pformat(key, reindent)
				if key_lines:  val_indent = 1
				else:          val_indent = 0
				rep_val, val_lines = _pformat(obj[key], 0, reindent=reindent+1+val_indent)
				buff += "\n%s : %s," % (rep_key, rep_val)
				n_lines += key_lines + val_lines
			buff += "\n%s}" % (indent_s*(reindent-1),)
		else:
			buff += "{"
			inloop = False
			for key in obj:
				if inloop:  buff += ", "
				else: inloop = True
				rep_key, key_lines = _pformat(key, 0, reindent)
				rep_val, val_lines = _pformat(obj[key], 0, reindent)
				buff += "%s : %s" % (rep_key, rep_val)
				n_lines += key_lines + val_lines
			buff += "}"
	
	
	elif type(obj) == list:
		
		if len(obj) > 4 or n_lines:
			buff += indent_s*indent+"["
			for val in obj:
				rep_val, val_lines = _pformat(val, reindent)
				buff += "\n%s," % (rep_val,)
				n_lines += val_lines
			buff += "\n%s]" % (indent_s*(reindent-1),)
		else:
			buff += "["
			inloop = False
			for val in obj:
				if inloop:  buff += ", "
				else: inloop = True
				rep, l = _pformat(val, 0, reindent)
				buff += rep
				n_lines += l
			buff += "]"
	
	
	elif type(obj) == tuple:
		
		if len(obj) > 4 or n_lines:
			buff += indent_s*indent+"("
			for val in obj:
				rep_val, val_lines = _pformat(val, reindent)
				buff += "\n%s," % (rep_val,)
				n_lines += val_lines
			indent -= 1
			buff += "\n%s)" % (indent_s*(reindent-1),)
		else:
			buff += "("
			inloop = False
			for val in obj:
				if inloop:  buff += ", "
				else: inloop = True
				rep, l = _pformat(val, 0, reindent)
				buff += rep
				n_lines += l
			buff += ")"
	
	
	elif hasattr(obj, "__repr__"):
		buff = indent*indent_s+repr(obj)
	else:
		buff = indent*indent_s+"None"
	
	
	return buff, n_lines