from io import BytesIO

from nose.tools import eq_, assert_raises

import jprops
from jprops import text_type


def test_property_lines():
  fp = BytesIO(b'a\nb\nc\n')
  eq_([b'a', b'b', b'c'], list(jprops._property_lines(fp)))


def test_property_lines_windows():
  fp = BytesIO(b'a\r\nb\r\nc\r\n')
  eq_([b'a', b'b', b'c'], list(jprops._property_lines(fp)))


def test_property_lines_mac():
  fp = BytesIO(b'a\rb\rc\r')
  eq_([b'a', b'b', b'c'], list(jprops._property_lines(fp)))


def test_property_lines_skips_blanks():
  fp = BytesIO(b'a\nb\n \t \n\nc\n')
  eq_([b'a', b'b', b'c'], list(jprops._property_lines(fp)))


def test_property_lines_skips_comments():
  fp = BytesIO(b'a\nb\n#foo\n!bar\nc\n')
  eq_([b'a', b'b', b'c'], list(jprops._property_lines(fp)))


def test_property_lines_continuation():
  fp = BytesIO(b'a\nb\\\nc\nd\n')
  eq_([b'a', b'bc', b'd'], list(jprops._property_lines(fp)))


def test_property_lines_continuation_includes_trailing_blanks():
  fp = BytesIO(b'a\nb \\\nc\nd\n')
  eq_([b'a', b'b c', b'd'], list(jprops._property_lines(fp)))


def test_property_lines_continuation_skips_leading_blanks():
  fp = BytesIO(b'a\nb\\\n c\nd\n')
  eq_([b'a', b'bc', b'd'], list(jprops._property_lines(fp)))


def test_property_lines_escaped_backslash_not_continuation():
  fp = BytesIO(b'a\nb\\\\\nc\nd\n')
  eq_([b'a', b'b\\\\', b'c', b'd'], list(jprops._property_lines(fp)))


def test_property_lines_escaped_backslash_before_continuation():
  fp = BytesIO(b'a\nb\\\\\\\nc\nd\n')
  eq_([b'a', b'b\\\\c', b'd'], list(jprops._property_lines(fp)))


# TODO test lines with trailing spaces


def test_split_key_value_equals():
  eq_((b'a', b'b'), jprops._split_key_value(b'a=b'))
  eq_((b'a', b'b'), jprops._split_key_value(b'a= b'))
  eq_((b'a', b'b'), jprops._split_key_value(b'a = b'))
  eq_((b'a', b'b'), jprops._split_key_value(b'a =b'))


def test_split_key_value_colon():
  eq_((b'a', b'b'), jprops._split_key_value(b'a:b'))
  eq_((b'a', b'b'), jprops._split_key_value(b'a: b'))
  eq_((b'a', b'b'), jprops._split_key_value(b'a : b'))
  eq_((b'a', b'b'), jprops._split_key_value(b'a :b'))


def test_key_terminator_after_terminated():
  eq_((b'a', b': b'), jprops._split_key_value(b'a : : b'))
  eq_((b'a', b':b'), jprops._split_key_value(b'a::b'))
  eq_((b'a', b'= b'), jprops._split_key_value(b'a = = b'))
  eq_((b'a', b'=b'), jprops._split_key_value(b'a==b'))
  eq_((b'a', b': b'), jprops._split_key_value(b'a = : b'))
  eq_((b'a', b'= b'), jprops._split_key_value(b'a : = b'))


def test_key_terminator_escaped():
  eq_((br'a\=b', b'c'), jprops._split_key_value(br'a\=b = c'))
  eq_((br'a\:b\=c', b'd'), jprops._split_key_value(br'a\:b\=c : d'))


def test_split_key_value_space():
  eq_((b'a', b'b'), jprops._split_key_value(b'a b'))


def test_split_key_value_empty_value():
  eq_((b'a', b''), jprops._split_key_value(b'a'))


def test_unescape_basic():
  eq_('\t', jprops._unescape(b'\\t'))
  eq_('\n', jprops._unescape(b'\\n'))
  eq_('\f', jprops._unescape(b'\\f'))
  eq_('\r', jprops._unescape(b'\\r'))


def test_unescape_unrecognized():
  eq_('=', jprops._unescape(br'\='))
  eq_(':', jprops._unescape(br'\:'))
  eq_('b', jprops._unescape(br'\b'))


def test_unescape_unicode():
  eq_(u'\u00ff', jprops._unescape(br'\u00ff'))


def test_unescape_unicode_encoded_backslassh():
  eq_(u'\\b', jprops._unescape(br'\u005cb'))


def test_unescape_unicode_escaped():
  eq_(r'\u00ff', jprops._unescape(br'\\u00ff'))
  eq_(u'\\\u00ff', jprops._unescape(br'\\\u00ff'))
  eq_(r'\\u00ff', jprops._unescape(br'\\\\u00ff'))


def test_unescape_decodes_ascii_to_native_string():
  eq_(str, type(jprops._unescape(b'x')))
  eq_(str, type(jprops._unescape(b'\x7f')))


def test_unescape_decodes_latin1_to_unicode():
  eq_(text_type, type(jprops._unescape(b'\xff')))
  eq_(text_type, type(jprops._unescape(b'\x80')))


def test_escape_basic():
  eq_(b'\\\\', jprops._escape('\\'))
  eq_(br'\t', jprops._escape('\t'))
  eq_(br'\n', jprops._escape('\n'))
  eq_(br'\f', jprops._escape('\f'))
  eq_(br'\r', jprops._escape('\r'))


def test_escape_unicode():
  eq_(br'\u0000', jprops._escape('\x00'))
  eq_(br'\u0000', jprops._escape(u'\u0000'))
  eq_(br'\u0019', jprops._escape('\x19'))
  eq_(br'\u0019', jprops._escape(u'\u0019'))
  eq_(br'\u007f', jprops._escape('\x7f'))
  eq_(br'\u007f', jprops._escape(u'\u007f'))
  eq_(br'\uffff', jprops._escape(u'\uffff'))

  eq_(bytes, type(jprops._escape(u'\uffff')))


def test_escape_value_leading_whitespace():
  eq_(br'\ \ x\ty ', jprops._escape_value('  x\ty '))


def test_escape_keys():
  eq_(br'\=', jprops._escape_key('='))
  eq_(br'\:', jprops._escape_key(':'))
  eq_(br'\ x\ ', jprops._escape_key(' x '))


def test_escape_comment_newline():
  eq_(b'#foo\n#bar', jprops._escape_comment('foo\nbar'))
  eq_(b'#foo\n#\n#bar', jprops._escape_comment('foo\n\nbar'))
  eq_(b'#foo\n#bar', jprops._escape_comment('foo\rbar'))
  eq_(b'#foo\n#\n#bar', jprops._escape_comment('foo\r\rbar'))
  eq_(b'#foo\n#bar', jprops._escape_comment('foo\r\nbar'))
  eq_(b'#foo\n#\n#bar', jprops._escape_comment('foo\r\n\r\nbar'))
  eq_(b'#foo\n#', jprops._escape_comment('foo\n'))


def test_escape_comment_newline_already_commented():
  eq_(b'#foo\n#bar', jprops._escape_comment('foo\n#bar'))
  eq_(b'#foo\n!bar', jprops._escape_comment('foo\n!bar'))


def test_escape_comment_unicode():
  eq_(b'#\xff', jprops._escape_comment(u'\u00ff'))
  eq_(br'#\u0100', jprops._escape_comment(u'\u0100'))


def test_write_non_string():
  assert_raises(TypeError, jprops.write_property, BytesIO(), b'x', 1)
  assert_raises(TypeError, jprops.write_property, BytesIO(), 1, b'x')
