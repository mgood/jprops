import codecs
import io
from io import BytesIO, StringIO, TextIOBase

import pytest
from pytest import raises

import jprops
from jprops import text_type


@pytest.mark.parametrize('lines', [
  b'a\nb\nc\n',       # Unix
  b'a\r\nb\r\nc\r\n', # Windows
  b'a\rb\rc\r',       # Mac
])
def test_property_lines_platform_line_endings(lines):
  expected = [u'a', u'b', u'c']
  property_lines = lambda fp: list(jprops._property_lines(fp))
  assert property_lines(BytesIO(lines)) == expected
  assert property_lines(StringIO(lines.decode('ascii'))) == expected


@pytest.mark.parametrize('lines,expected', [
  # skips blanks
  (b'a\nb\n \t \n\nc\n', [u'a', u'b', u'c']),
  # includes comments
  (b'a\nb\n#foo\n!bar\nc\n', [u'a', u'b', u'#foo', u'!bar', u'c']),
  # continuation
  (b'a\nb\\\nc\nd\n', [u'a', u'bc', u'd']),
  # continuation includes trailing blanks
  (b'a\nb \\\nc\nd\n', [u'a', u'b c', u'd']),
  # continuation skips leading blanks
  (b'a\nb\\\n c\nd\n', [u'a', u'bc', u'd']),
  # escaped backslash is not a continuation
  (b'a\nb\\\\\nc\nd\n', [u'a', u'b\\\\', u'c', u'd']),
  # escaped backslash before continuation
  (b'a\nb\\\\\\\nc\nd\n', [u'a', u'b\\\\c', u'd']),
])
def test_property_lines_splitting(lines, expected):
  property_lines = lambda fp: list(jprops._property_lines(fp))
  assert property_lines(BytesIO(lines)) == expected
  assert property_lines(StringIO(lines.decode('ascii'))) == expected


@pytest.mark.parametrize('line,expected', [
  # with equals separator
  (u'a=b', (u'a', u'b')),
  (u'a= b', (u'a', u'b')),
  (u'a = b', (u'a', u'b')),
  (u'a =b', (u'a', u'b')),

  # with colon separator
  (u'a:b', (u'a', u'b')),
  (u'a: b', (u'a', u'b')),
  (u'a : b', (u'a', u'b')),
  (u'a :b', (u'a', u'b')),

  # only space separator
  (u'a b', (u'a', u'b')),

  # additional key terminator after already terminated
  (u'a : : b', (u'a', u': b')),
  (u'a::b', (u'a', u':b')),
  (u'a = = b', (u'a', u'= b')),
  (u'a==b', (u'a', u'=b')),
  (u'a = : b', (u'a', u': b')),
  (u'a : = b', (u'a', u'= b')),

  # key terminator escaped
  (u'a\\=b = c', (u'a\\=b', u'c')),
  (u'a\\:b\\=c : d', (u'a\\:b\\=c', u'd')),

  # empty value
  (u'a', (u'a', u'')),

  # comment
  (u'#foo', (jprops.COMMENT, u'foo')),

  # non-ascii
  (u'\u00ff=\u00fe', (u'\u00ff', u'\u00fe')),
])
def test_split_key_value(line, expected):
  assert jprops._split_key_value(line) == expected


@pytest.mark.parametrize('value,expected', [
  # basic whitespace escapes
  (u'\\t', '\t'),
  (u'\\n', '\n'),
  (u'\\f', '\f'),
  (u'\\r', '\r'),

  # unrecognized escape should just return the character
  (u'\\=', '='),
  (u'\\:', ':'),
  (u'\\b', 'b'),

  # unicode \u escapes
  (u'\\u00ff', u'\u00ff'),

  # backslash encoded as \u unicode escape
  (u'\\u005cb', '\\b'),

  # unicode with escaped backslashes
  (u'\\\\u00ff', '\\u00ff'),
  (u'\\\\\\u00ff', u'\\\u00ff'),
  (u'\\\\\\\\u00ff', '\\\\u00ff'),
])
def test_unescape(value, expected):
  actual = jprops._unescape(value)
  assert actual == expected
  assert type(actual) == type(expected)


@pytest.mark.parametrize('value,expected', [
  # basic
  (u'\\', u'\\\\'),
  (u'\t', u'\\t'),
  (u'\n', u'\\n'),
  (u'\f', u'\\f'),
  (u'\r', u'\\r'),

  # escape comment markers
  (u'#', u'\\#'),
  (u'!', u'\\!'),
])
def test_escape(value, expected):
  actual = jprops._escape(value)
  assert actual == expected
  assert type(actual) == type(expected)


@pytest.mark.parametrize('value,expected', [
  # leading whitespace in value
  (u'  x\ty ', u'\\ \\ x\\ty '),

  # key terminator in value
  (u'=', u'\\='),
  (u':', u'\\:'),
])
def test_escape_value(value, expected):
  actual = jprops._escape_value(value)
  assert actual == expected
  assert type(actual) == type(expected)


@pytest.mark.parametrize('key,expected', [
  (u'=', u'\\='),
  (u':', u'\\:'),
  (u' x ', u'\\ x\\ '),
])
def test_escape_keys(key, expected):
  actual = jprops._escape_key(key)
  assert actual == expected
  assert type(actual) == type(expected)


@pytest.mark.parametrize('comment,expected', [
  # newlines in comments should start the next line with a comment
  (u'foo\nbar', u'#foo\n#bar'),
  (u'foo\n\nbar', u'#foo\n#\n#bar'),
  (u'foo\rbar', u'#foo\n#bar'),
  (u'foo\r\rbar', u'#foo\n#\n#bar'),
  (u'foo\r\nbar', u'#foo\n#bar'),
  (u'foo\r\n\r\nbar', u'#foo\n#\n#bar'),
  (u'foo\n', u'#foo\n#'),

  # if the newline is already followed by a comment marker, keep it
  (u'foo\n#bar', u'#foo\n#bar'),
  (u'foo\n!bar', u'#foo\n!bar'),
])
def test_escape_comment_newline(comment, expected):
  assert jprops._escape_comment(comment) == expected


@pytest.mark.parametrize('key,value,expected', [
  (u'\x00',   u'', b'\\u0000='),
  (u'\u0000', u'', b'\\u0000='),
  (u'\x19',   u'', b'\\u0019='),
  (u'\u0019', u'', b'\\u0019='),
  (u'\x7f',   u'', b'\\u007f='),
  (u'\u007f', u'', b'\\u007f='),
  (u'\uffff', u'', b'\\uffff='),

  (jprops.COMMENT, u'\u00ff', b'#\xff'),
  (jprops.COMMENT, u'\u0100', b'#\\u0100'),
])
def test_escape_unicode_in_bytes_output(key, value, expected):
  b = BytesIO()
  jprops.write_property(b, key, value)
  actual = b.getvalue()[:-1] # strip the trailing newline
  assert actual == expected


@pytest.mark.parametrize('key,value,expected', [
  (u'\x00',   u'', u'\u0000='),
  (u'\u0000', u'', u'\u0000='),
  (u'\x19',   u'', u'\u0019='),
  (u'\u0019', u'', u'\u0019='),
  (u'\x7f',   u'', u'\u007f='),
  (u'\u007f', u'', u'\u007f='),
  (u'\uffff', u'', u'\uffff='),

  (jprops.COMMENT, u'\u00ff', u'#\xff'),
  (jprops.COMMENT, u'\u0100', u'#\u0100'),
])
def test_unicode_in_text_output_not_escaped(key, value, expected):
  b = StringIO()
  jprops.write_property(b, key, value)
  actual = b.getvalue()[:-1] # strip the trailing newline
  assert actual == expected


def test_write_non_string_is_an_error():
  with raises(TypeError):
    jprops.write_property(BytesIO(), b'x', 1)
  with raises(TypeError):
    jprops.write_property(BytesIO(), 1, b'x')


def test_iter_properties_ignores_comments_by_default():
  fp = BytesIO(b'a\n#foo\nb\n')
  assert list(jprops.iter_properties(fp)) == [('a', ''), ('b', '')]


def test_iter_properties_includes_comments():
  fp = BytesIO(b'a\n#foo\nb\n')
  assert (list(jprops.iter_properties(fp, comments=True)) ==
          [('a', ''), (jprops.COMMENT, 'foo'), ('b', '')])


def test_write_property_with_comment():
  fp = BytesIO()
  jprops.write_property(fp, jprops.COMMENT, 'foo')
  assert fp.getvalue() == b'#foo\n'


def test_read_text():
  fp = StringIO(u'a=\u00ff\n')
  assert list(jprops.iter_properties(fp)) == [(u'a', u'\u00ff')]


def test_read_bytes():
  fp = BytesIO(b'a=\\u00ff\n')
  assert list(jprops.iter_properties(fp)) == [(u'a', u'\u00ff')]


def test_write_text():
  fp = StringIO()
  jprops.write_property(fp, u'a', u'\u00ff')
  assert fp.getvalue() == u'a=\u00ff\n'


def test_write_bytes():
  fp = BytesIO()
  jprops.write_property(fp, u'a', u'\u00ff')
  assert fp.getvalue() == b'a=\\u00ff\n'


def builtin_open(path, mode, encoding, newline):
  if 'w' in mode and newline:
    # jprops handles newline splitting on read, but relies on the underlying
    # file for writing
    raise pytest.skip("built-in open doesn't support newline for writing")
  if 'r' in mode and not newline:
    # for reading use universal-newlines support if newline is None or ''
    mode += 'U'
  if encoding is None:
    return open(path, mode)
  elif jprops.PY2:
    raise pytest.skip("Python 2 built-in open doesn't support encoding")
  return open(path, mode, encoding=encoding)


def codecs_open(path, mode, encoding, newline):
  if 'w' in mode and newline:
    # jprops handles newline splitting on read, but relies on the underlying
    # file for writing
    pytest.skip("codecs.open doesn't support newline modes")
  return codecs.open(path, mode, encoding=encoding)


def io_open(path, mode, encoding, newline):
  if 'b' in mode and newline is not None:
    raise pytest.skip("io.open binary mode doesn't take a newline argument")
  return io.open(path, mode, encoding=encoding, newline=newline)


@pytest.mark.parametrize('opener', [
  builtin_open,
  codecs_open,
  io_open,
])
@pytest.mark.parametrize('encoding,file_data', [
  (None,    b'a=\\u0100\n'),
  ('utf-8', u'a=\u0100\n'.encode('utf-8')),
])
@pytest.mark.parametrize('mode', [
  'r', 'w',
])
@pytest.mark.parametrize('newline', [
  None, '', '\n', '\r', '\r\n',
])
def test_file_modes(tmpdir, opener, encoding, file_data, mode, newline):
  # check common combinations of various methods of opening files with different
  # encodings and line-endings

  if encoding is None:
    mode += 'b'
  expected_props = {u'a': u'\u0100'}

  if newline:
    file_data = file_data.replace(b'\n', newline.encode('ascii'))

  open_path = lambda path: opener(
    str(path),
    mode,
    encoding=encoding,
    newline=newline,
  )

  if 'r' in mode:
    read_path = tmpdir.join('reading.properties')
    read_path.write_binary(file_data)
    with open_path(read_path) as fp:
      actual_props = jprops.load_properties(fp)
    assert actual_props == expected_props

  else:
    write_path = tmpdir.join('writing.properties')
    with open_path(write_path) as fp:
      jprops.store_properties(fp, expected_props, timestamp=False)
    actual_data = write_path.read_binary()
    assert actual_data == file_data
