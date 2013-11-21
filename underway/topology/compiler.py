import re

class CompileError(Exception):
	def __init__(self, code=0, msg=None):
		self.msg = msg
		self.code = code

	def __str__(self):
		return 'ERROR: {code: %s, msg: %s}' % (str(self.code), self.msg)


class TopoCompiler(object):

	def __init__(self, world):
		self.world = world
		if 'root'  not in world.keys():
			raise CompileError(msg='Cannot find the root topology file.', code=404.0)
		self._recursion_depth = 0

	def _make_filter(self, k, v):
		return lambda d: d[k] == v

	def _filter_list(self, f, l):
		return filter(f,l)

	def _get_include(self, inc):
		r_extraction = re.compile("([A-Za-z0-9\_]*)\[([a-zA-Z0-9]*):\s([A-Za-z0-9\_]*)\]\[([A-Za-z0-9\_]*)\]")
		r_include = re.compile("([A-Za-z0-9\_]*)\[([a-zA-Z0-9]*):\s([A-Za-z0-9\_]*)\]")
		r_fname = re.compile("([A-Za-z0-9\_]*)")

		inc_file = filterkey = filtervalue = extractionkey = None
		
		match = r_extraction.search(inc)
		if match and len(match.groups())==4:
			(inc_file, filterkey, filtervalue, extractionkey) = match.groups()
			#print "RE 4 Match on " +inc+ ": (%s, %s, %s, %s)" % (inc_file, filterkey, filtervalue, extractionkey)
		else:
			match = r_include.search(inc)
			if match and len(match.groups())==3:
				(inc_file, filterkey, filtervalue) = match.groups()
				#print "RE 3 match on " +inc+ ": (%s, %s, %s)" % (inc_file, filterkey, filtervalue)
			else:
				match = r_fname.search(inc)
				if match and len(match.groups())==1:
					inc_file = match.groups()
					if type(inc_file) == type((1,2)):
						inc_file = inc_file[0]
					#print "RE 1 match on " +inc+ ": (%s)" % inc_file
				else:
					raise CompileError(msg='Included file with spec = %s did not yield any match to a topology file. This is probably a malformed name for the include file.' % inc, code = 404.5)


		if inc_file in self.world.keys():
			if filterkey:
				filt = self._make_filter(filterkey, filtervalue)
				filt_result = self._filter_list(filt, self.world[inc_file])
				#print "filt results: ", filt_result
				if len(filt_result) == 0:
					raise CompileError(msg='Included file with filter spec = %s resulted in no matches.' % inc, code = 404.6)
				elif len(filt_result) > 1:
					raise CompileError(msg='Included file with filter spec = %s resulted in multiple matches.' % inc, code = 404.7)
				else:
					filt_result = filt_result[0]
				if extractionkey:
					if extractionkey in filt_result.keys():
						return self.compile(filt_result[extractionkey])
					else:
						raise CompileError(msg='Included file with filter spec = %s resulted in a match but property %s could not be found.' % (inc, extractionkey), code = 404.8)
				else:
					return self.compile(filt_result)

			return self.compile(self.world[inc_file])
		else:
			#print "Couldn't find %s in %s" % (inc_file, self.world.keys())
			raise CompileError(msg='Included topology file %s not found.' % inc, code=404.4)

	def _process_list(self, l):
		"""
		Companion to _process_dict that handles values of list type.  It expands lists of dictionaries
		recursively.
		"""

		out = []
		for item in l:
			if type(item) == type({}):
				out.append(self._process_dict(item))
			elif type(item) == type([]):
				out.append(self._process_list(item))
			else:
				out.append(item)
		return out

	def _process_dict(self, d):
		"""
		A recursive dictionary compiler that expands included files through the keyword 'include'. Expands 
		one recursion depth on each call.  Call multiple times to expand to lower levels.

		:param: d A dictionary input

		:returns: A dictionary with included files expanded up to a recursion depth of 1.
		"""

		out = {}
		for (k, v) in d.items():
			#print (k, v)
			if k == 'include':
				d_insert = self._get_include(v)
				if type(d_insert) == type({}):
					out.update(d_insert)
				else:
					# This return is useful when a filter and extraction key results only 
					# in a string to be included in a list
					return d_insert
			else:
				if type(v) == type({}):
					r1 = self._process_dict(v)
					out.update({k: r1})
				elif type(v) == type([]):
					r1 = self._process_list(v)
					out.update({k: r1})
				else:
					out.update({k: v})
		return out

	def compile(self, datastruct, max_recursion_depth = 10):
		self._recursion_depth += 1
		if self._recursion_depth >= max_recursion_depth:
			raise CompileError(msg='Recursion depth exceeded %s. This is usually caused by a recursive include in a topology file that never terminates.' % str(max_recursion_depth), code=203.1)
		#if type(datastruct) != type({}):
		#	raise CompileError(msg='Input must be a hash, not list.', code=501.1)

		if type(datastruct) == type({}):
			return self._process_dict(datastruct)
		elif type(datastruct) == type([]):
			return self._process_list(datastruct)
		elif type(datastruct) == type(''):
			return datastruct
		else:
			raise CompileError(msg='Unknown datastruct type %s' % type(datastruct), code=500.2)