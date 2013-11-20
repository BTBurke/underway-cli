from underway.parser import ParseError, TopoCompiler
import pytest

def test_parser_ParseError_raise():
	with pytest.raises(ParseError):
		raise ParseError()

def test_parser_ParseError_attributes():
	ex = ParseError(msg='Test Message', code=400)
	assert hasattr(ex, 'msg')
	assert hasattr(ex, 'code')
	assert ex.msg == 'Test Message'
	assert ex.code == 400
	assert ex.__str__() == 'ERROR: ParseError: {code: 400, msg: Test Message}'

def test_parser_2ndlevel_recursive_include():
	s = {'test': {'test': {'include': 'test'}}}
	world = {'root': s, 'test': {'test': 1, 'test2': 2}, 'recursive': {'recursive': 1, 'include': 'test'} }
	out = TopoCompiler(world).parse(world['root'])
	assert out == {'test': {'test': {'test': 1, 'test2': 2}}}

def test_parser_1stlevel_list_include():
	s = {'test': [{'include': 'test'}, {'include': 'recursive'}]}
	world = {'root': s, 'test': {'test': 1, 'test2': 2}, 'recursive': {'recursive': 1, 'include': 'test'} }
	out = TopoCompiler(world).parse(world['root'])
	assert out == {'test': [{'test': 1, 'test2': 2}, {'recursive': 1, 'test': 1, 'test2': 2}]}

def test_parser_2ndlevel_list_include():
	s = {'test': {'test': [{'include': 'test'}, {'include': 'test'}]}}
	world = {'root': s, 'test': {'test': 1, 'test2': 2}, 'recursive': {'recursive': 1, 'include': 'test'} }
	out = TopoCompiler(world).parse(world['root'])
	assert out == {'test': {'test': [{'test': 1, 'test2': 2}, {'test': 1, 'test2': 2}]}}

def test_parser_nonterminating_recursive_include_raises_parseerror():
	s = {'test': {'include': 'forever'}}
	world = {'root': s, 'forever': {'include': 'forever'}}
	with pytest.raises(ParseError):
		TopoCompiler(world).parse(world['root'])

def test_parser_include_not_found():
	s = {'test': {'include': 'notfound'}}
	world = {'root': s}
	with pytest.raises(ParseError):
		TopoCompiler(world).parse(world['root'])

def test_parser_filter():
	s = [{'name': 'test'}, {'name': 'test2'}]
	t = TopoCompiler({'root': None})
	f = t._make_filter('name', 'test')
	result = t._filter_list(f, s)
	assert len(result) == 1
	assert result[0] == s[0]
	assert t._filter_list(f,[]) == []