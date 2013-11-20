class ParseError(Exception):
	def __init__(self, code=0, msg=None):
		self.msg = msg
		self.code = code

	def __str__(self):
		return 'ERROR: ParseError: {code: %s, msg: %s}' % (str(self.code), self.msg)


class TopoCompiler(object):

	def __init__(self, world):
		self.world = world
		if 'root'  not in world.keys():
			raise ParseError(msg='Cannot find the root topology file.', code=404.0)
		self._recursion_depth = 0

	def _make_filter(self, k, v):
		return lambda d: d[k] == v

	def _filter_list(self, f, l):
		return filter(f,l)

	def _get_include(self, inc):
		if inc in self.world.keys():
			return self.parse(self.world[inc])
		else:
			raise ParseError(msg='Included topology file %s not found.' % inc, code=404.4)

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
		A recursive dictionary parser that expands included files through the keyword 'include'. Expands 
		one recursion depth on each call.  Call multiple times to expand to lower levels.

		:param: d A dictionary input

		:returns: A dictionary with included files expanded up to a recursion depth of 1.
		"""

		out = {}
		for (k, v) in d.items():
			print (k, v)
			if k == 'include':
				d_insert = self._get_include(v)
				out.update(d_insert)
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

	def parse(self, datastruct, max_recursion_depth = 10):
		self._recursion_depth += 1
		if self._recursion_depth >= max_recursion_depth:
			raise ParseError(msg='Recursion depth exceeded %s. This is usually caused by a recursive include in a topology file that never terminates.' % str(max_recursion_depth), code=203.1)
		if type(datastruct) != type({}):
			raise ParseError(msg='Input must be a hash, not list.', code=501.1)

		return self._process_dict(datastruct)