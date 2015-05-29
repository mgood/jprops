from io import BytesIO

import pytest

import jprops


@pytest.mark.parametrize('data,props', [
  # Key value with equals
  (b'a=b', {'a': 'b'}),
  (b'a= b', {'a': 'b'}),
  (b'a = b', {'a': 'b'}),
  (b'a =b', {'a': 'b'}),

  # Key value with colon
  (b'a:b', {'a': 'b'}),
  (b'a: b', {'a': 'b'}),
  (b'a : b', {'a': 'b'}),
  (b'a :b', {'a': 'b'}),

  # Key terminator after terminator
  (b'a : : b', {'a': ': b'}),
  (b'a::b', {'a': ':b'}),
  (b'a = = b', {'a': '= b'}),
  (b'a==b', {'a': '=b'}),
  (b'a = : b', {'a': ': b'}),
  (b'a : = b', {'a': '= b'}),

  # Key terminator escaped
  (br'a\=b = c', {r'a=b': 'c'}),
  (br'a\:b\=c : d', {r'a:b=c': 'd'}),

  # Key value with space only
  (b'a b', {'a': 'b'}),

  # Key value empty value
  (b'a', {'a': ''}),

  # Escaping
  # Basic backslash escapes
  (b'a \\t', {'a': '\t'}),
  (b'a \\n', {'a': '\n'}),
  (b'a \\f', {'a': '\f'}),
  (b'a \\r', {'a': '\r'}),

  # Unrecognized escapes
  (br'a \=', {'a': '='}),
  (br'a \:', {'a': ':'}),
  (br'a \b', {'a': 'b'}),

  # Unicode escape
  (br'a \u00ff', {'a': u'\u00ff'}),

  # Unicode encoded backslash
  (br'a \u005cb', {'a': u'\\b'}),

  # Unicode with preceding escaped backslashes
  (br'a \\u00ff', {'a': r'\u00ff'}),
  (br'a \\\u00ff', {'a': u'\\\u00ff'}),
  (br'a \\\\u00ff', {'a': r'\\u00ff'}),

  # Latin-1 encoded bytes
  (b'a \x7f', {'a': u'\x7f'}),

  # Escaped backslash
  (b'a \\\\x7f', {'a': '\\x7f'}),

  # Line endings
  # Simple
  (b'a\nb\nc\n', {'a': '', 'b': '', 'c': ''}),
  # Windows newlines
  (b'a\r\nb\r\nc\r\n', {'a': '', 'b': '', 'c': ''}),
  # Mac newlines
  (b'a\rb\rc\r', {'a': '', 'b': '', 'c': ''}),
  # Blank lines
  (b'a\nb\n \t \n\nc\n', {'a': '', 'b': '', 'c': ''}),
  # Line continuation
  (b'a\nb\\\nc\nd\n', {'a': '', 'bc': '', 'd': ''}),
  # Line continuation trailing blanks
  (b'a\nb \\\nc\nd\n', {'a': '', 'b': 'c', 'd': ''}),
  # Line continuation skips leading blanks
  (b'a\nb\\\n c\nd\n', {'a': '', 'bc': '', 'd': ''}),
  # Escaped backslash not continuation
  (b'a\nb\\\\\nc\nd\n', {'a': '', 'b\\': '', 'c': '', 'd': ''}),
  # Escaped backslash before continuation
  (b'a\nb\\\\\\\nc\nd\n', {'a': '', 'b\\c': '', 'd': ''}),
])
def test_load(data, props):
  assert jprops.load_properties(BytesIO(data)) == props


@pytest.mark.parametrize('props,data', [
  # Simple
  ({'a': 'b'}, b'a=b'),

  # Escaping basic
  ({'a': '\\'}, b'a=\\\\'),
  ({'a': 'x \t'}, br'a=x \t'),
  ({'a': 'x \n'}, br'a=x \n'),
  ({'a': 'x \f'}, br'a=x \f'),
  ({'a': 'x \r'}, br'a=x \r'),

  # Escape whitespace-only value
  ({'a': '\t'}, br'a=\t'),
  ({'a': '\n'}, br'a=\n'),
  ({'a': '\f'}, br'a=\f'),
  ({'a': '\r'}, br'a=\r'),

  # Escape unicode
  ({'a': '\x00'}, br'a=\u0000'),
  ({'a': u'\u0000'}, br'a=\u0000'),
  ({'a': '\x19'}, br'a=\u0019'),
  ({'a': u'\u0019'}, br'a=\u0019'),
  ({'a': '\x7f'}, br'a=\u007f'),
  ({'a': u'\u007f'}, br'a=\u007f'),
  ({'a': u'\uffff'}, br'a=\uffff'),

  # Escape value leading whitespace
  ({'a': '  x\ty '}, br'a=\ \ x\ty '),

  # Escape key terminators
  ({'=': ''}, br'\=='),
  ({':': ''}, br'\:='),
  ({' x ': ''}, br'\ x\ ='),

  # Escape key terminators in value
  ({'a': '='}, br'a=\='),
  ({'a': ':'}, br'a=\:'),

  # Escape comment markers
  ({'a': '#'}, br'a=\#'),
  ({'a': '!'}, br'a=\!'),
])
def test_store(props, data):
  fp = BytesIO()
  jprops.store_properties(fp, props, timestamp=False)
  assert fp.getvalue() == data + b'\n'
