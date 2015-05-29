from io import BytesIO

from pytest import raises

import jprops
from jprops import text_type


def test_property_lines():
  fp = BytesIO(b'a\nb\nc\n')
  assert list(jprops._property_lines(fp)) == [b'a', b'b', b'c']


def test_property_lines_windows():
  fp = BytesIO(b'a\r\nb\r\nc\r\n')
  assert list(jprops._property_lines(fp)) == [b'a', b'b', b'c']


def test_property_lines_mac():
  fp = BytesIO(b'a\rb\rc\r')
  assert list(jprops._property_lines(fp)) == [b'a', b'b', b'c']


def test_property_lines_skips_blanks():
  fp = BytesIO(b'a\nb\n \t \n\nc\n')
  assert list(jprops._property_lines(fp)) == [b'a', b'b', b'c']


def test_property_lines_includes_comments():
  fp = BytesIO(b'a\nb\n#foo\n!bar\nc\n')
  assert list(jprops._property_lines(fp)) == [b'a', b'b', b'#foo', b'!bar', b'c']


def test_property_lines_continuation():
  fp = BytesIO(b'a\nb\\\nc\nd\n')
  assert list(jprops._property_lines(fp)) == [b'a', b'bc', b'd']


def test_property_lines_continuation_includes_trailing_blanks():
  fp = BytesIO(b'a\nb \\\nc\nd\n')
  assert list(jprops._property_lines(fp)) == [b'a', b'b c', b'd']


def test_property_lines_continuation_skips_leading_blanks():
  fp = BytesIO(b'a\nb\\\n c\nd\n')
  assert list(jprops._property_lines(fp)) == [b'a', b'bc', b'd']


def test_property_lines_escaped_backslash_not_continuation():
  fp = BytesIO(b'a\nb\\\\\nc\nd\n')
  assert list(jprops._property_lines(fp)) == [b'a', b'b\\\\', b'c', b'd']


def test_property_lines_escaped_backslash_before_continuation():
  fp = BytesIO(b'a\nb\\\\\\\nc\nd\n')
  assert list(jprops._property_lines(fp)) == [b'a', b'b\\\\c', b'd']


# TODO test lines with trailing spaces


def test_split_key_value_equals():
  assert jprops._split_key_value(b'a=b') == (b'a', b'b')
  assert jprops._split_key_value(b'a= b') == (b'a', b'b')
  assert jprops._split_key_value(b'a = b') == (b'a', b'b')
  assert jprops._split_key_value(b'a =b') == (b'a', b'b')


def test_split_key_value_colon():
  assert jprops._split_key_value(b'a:b') == (b'a', b'b')
  assert jprops._split_key_value(b'a: b') == (b'a', b'b')
  assert jprops._split_key_value(b'a : b') == (b'a', b'b')
  assert jprops._split_key_value(b'a :b') == (b'a', b'b')


def test_key_terminator_after_terminated():
  assert jprops._split_key_value(b'a : : b') == (b'a', b': b')
  assert jprops._split_key_value(b'a::b') == (b'a', b':b')
  assert jprops._split_key_value(b'a = = b') == (b'a', b'= b')
  assert jprops._split_key_value(b'a==b') == (b'a', b'=b')
  assert jprops._split_key_value(b'a = : b') == (b'a', b': b')
  assert jprops._split_key_value(b'a : = b') == (b'a', b'= b')


def test_key_terminator_escaped():
  assert jprops._split_key_value(br'a\=b = c') == (br'a\=b', b'c')
  assert jprops._split_key_value(br'a\:b\=c : d') == (br'a\:b\=c', b'd')


def test_split_key_value_space():
  assert jprops._split_key_value(b'a b') == (b'a', b'b')


def test_split_key_value_empty_value():
  assert jprops._split_key_value(b'a') == (b'a', b'')


def test_split_key_value_comment():
  assert jprops._split_key_value(b'#foo') == (jprops.COMMENT, b'foo')


def test_unescape_basic():
  assert jprops._unescape(b'\\t') == '\t'
  assert jprops._unescape(b'\\n') == '\n'
  assert jprops._unescape(b'\\f') == '\f'
  assert jprops._unescape(b'\\r') == '\r'


def test_unescape_unrecognized():
  assert jprops._unescape(br'\=') == '='
  assert jprops._unescape(br'\:') == ':'
  assert jprops._unescape(br'\b') == 'b'


def test_unescape_unicode():
  assert jprops._unescape(br'\u00ff') == u'\u00ff'


def test_unescape_unicode_encoded_backslassh():
  assert jprops._unescape(br'\u005cb') == u'\\b'


def test_unescape_unicode_escaped():
  assert jprops._unescape(br'\\u00ff') == r'\u00ff'
  assert jprops._unescape(br'\\\u00ff') == u'\\\u00ff'
  assert jprops._unescape(br'\\\\u00ff') == r'\\u00ff'


def test_unescape_decodes_ascii_to_native_string():
  assert type(jprops._unescape(b'x')) == str
  assert type(jprops._unescape(b'\x7f')) == str


def test_unescape_decodes_latin1_to_unicode():
  assert type(jprops._unescape(b'\xff')) == text_type
  assert type(jprops._unescape(b'\x80')) == text_type


def test_escape_basic():
  assert jprops._escape('\\') == b'\\\\'
  assert jprops._escape('\t') == br'\t'
  assert jprops._escape('\n') == br'\n'
  assert jprops._escape('\f') == br'\f'
  assert jprops._escape('\r') == br'\r'


def test_escape_unicode():
  assert jprops._escape('\x00') == br'\u0000'
  assert jprops._escape(u'\u0000') == br'\u0000'
  assert jprops._escape('\x19') == br'\u0019'
  assert jprops._escape(u'\u0019') == br'\u0019'
  assert jprops._escape('\x7f') == br'\u007f'
  assert jprops._escape(u'\u007f') == br'\u007f'
  assert jprops._escape(u'\uffff') == br'\uffff'

  assert type(jprops._escape(u'\uffff')) == bytes


def test_escape_value_leading_whitespace():
  assert jprops._escape_value('  x\ty ') == br'\ \ x\ty '


def test_escape_keys():
  assert jprops._escape_key('=') == br'\='
  assert jprops._escape_key(':') == br'\:'
  assert jprops._escape_key(' x ') == br'\ x\ '


def test_escape_comment_newline():
  assert jprops._escape_comment('foo\nbar') == b'#foo\n#bar'
  assert jprops._escape_comment('foo\n\nbar') == b'#foo\n#\n#bar'
  assert jprops._escape_comment('foo\rbar') == b'#foo\n#bar'
  assert jprops._escape_comment('foo\r\rbar') == b'#foo\n#\n#bar'
  assert jprops._escape_comment('foo\r\nbar') == b'#foo\n#bar'
  assert jprops._escape_comment('foo\r\n\r\nbar') == b'#foo\n#\n#bar'
  assert jprops._escape_comment('foo\n') == b'#foo\n#'


def test_escape_comment_newline_already_commented():
  assert jprops._escape_comment('foo\n#bar') == b'#foo\n#bar'
  assert jprops._escape_comment('foo\n!bar') == b'#foo\n!bar'


def test_escape_comment_unicode():
  assert jprops._escape_comment(u'\u00ff') == b'#\xff'
  assert jprops._escape_comment(u'\u0100') == br'#\u0100'


def test_write_non_string():
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
