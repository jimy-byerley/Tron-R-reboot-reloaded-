"""
Copyright 2014,2015 Yves Dejonghe

This file is part of Tron-R.

    Tron-R is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Tron-R is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Tron-R.  If not, see <http://www.gnu.org/licenses/>. 2
"""

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