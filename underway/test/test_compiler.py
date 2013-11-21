from underway.compiler import CompileError, TopoCompiler
import pytest

def test_compiler_CompileError_raise():
	"""
	Compiler should be able to raise an error
	"""
	with pytest.raises(CompileError):
		raise CompileError()

def test_compiler_CompileError_attributes():
	"""
	Compiler should be able to raise an error with informative messages and a status code
	"""
	ex = CompileError(msg='Test Message', code=400)
	assert hasattr(ex, 'msg')
	assert hasattr(ex, 'code')
	assert ex.msg == 'Test Message'
	assert ex.code == 400
	assert ex.__str__() == 'ERROR: {code: 400, msg: Test Message}'

def test_compiler_2ndlevel_recursive_include():
	"""
	Compiler should be able to recursively include a file at the 2nd level
	"""
	s = {'test': {'test': {'include': 'test'}}}
	world = {'root': s, 'test': {'test': 1, 'test2': 2}, 'recursive': {'recursive': 1, 'include': 'test'} }
	out = TopoCompiler(world).compile(world['root'])
	assert out == {'test': {'test': {'test': 1, 'test2': 2}}}

def test_compiler_1stlevel_list_include():
	"""
	Compiler should be able to include contents of another YAML file with keyword include inside a list
	"""
	s = {'test': [{'include': 'test'}, {'include': 'recursive'}]}
	world = {'root': s, 'test': {'test': 1, 'test2': 2}, 'recursive': {'recursive': 1, 'include': 'test'} }
	out = TopoCompiler(world).compile(world['root'])
	assert out == {'test': [{'test': 1, 'test2': 2}, {'recursive': 1, 'test': 1, 'test2': 2}]}

def test_compiler_2ndlevel_list_include():
	"""
	Compiler should be able to recursively include files to an arbitrary depth less than the recursive include limit inside a list
	"""
	s = {'test': {'test': [{'include': 'test'}, {'include': 'test'}]}}
	world = {'root': s, 'test': {'test': 1, 'test2': 2}, 'recursive': {'recursive': 1, 'include': 'test'} }
	out = TopoCompiler(world).compile(world['root'])
	assert out == {'test': {'test': [{'test': 1, 'test2': 2}, {'test': 1, 'test2': 2}]}}

def test_compiler_nonterminating_recursive_include_raises_compileerror():
	"""
	Compiler should raise an error on a recursive include that doesn't terminate
	"""
	s = {'test': {'include': 'forever'}}
	world = {'root': s, 'forever': {'include': 'forever'}}
	with pytest.raises(CompileError):
		TopoCompiler(world).compile(world['root'])

def test_compiler_include_not_found():
	"""
	Compiler should raise an error if an included file cannot be found
	"""
	s = {'test': {'include': 'notfound'}}
	world = {'root': s}
	with pytest.raises(CompileError):
		TopoCompiler(world).compile(world['root'])

def test_compiler_filter():
	"""
	Compiler should filter a list of dicts based on the value of a specified key
	"""
	s = [{'name': 'test'}, {'name': 'test2'}]
	t = TopoCompiler({'root': None})
	f = t._make_filter('name', 'test')
	result = t._filter_list(f, s)
	assert len(result) == 1
	assert result[0] == s[0]
	assert t._filter_list(f,[]) == []

def test_compiler_should_pass_string_list():
	"""
	Compiler should pass lists of strings straight through
	"""
	s = {'test': {'list': ['string1', 'string2']}}
	world = {'root': s}
	out = TopoCompiler(world).compile(world['root'])
	assert out == s

def test_compiler_include_with_string_list():
	"""
	Compiler should pass lists of strings through with an embedded include
	"""
	s = {'test': {'list': ['string1', {'include': 'test'}, 'string2']}}
	world = {'root': s, 'test': {'name': 'included_string'}}
	t = TopoCompiler(world).compile(world['root'])
	assert t == {'test': {'list': ['string1', {'name': 'included_string'}, 'string2']}}

def test_compiler_include_with_extraction():
	"""
	Compiler should filter and select items in included files using syntax `include: filename[key: filtervalue][key_to_include]`
	"""
	s = {'test': {'list': ['string1', {'include': 'test[name: included_string][value]'}, 'string2']}}
	world = {'root': s, 'test': [{'name': 'included_string', 'value': 'included_value'}]}
	t = TopoCompiler(world).compile(world['root'])
	assert t == {'test': {'list': ['string1', 'included_value', 'string2']}}

