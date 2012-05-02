from StringIO import StringIO

from nose.tools import eq_

import jprops


def test_property_lines():
  fp = StringIO('a\nb\nc\n')
  eq_(['a', 'b', 'c'], list(jprops._property_lines(fp)))


def test_property_lines_windows():
  fp = StringIO('a\r\nb\r\nc\r\n')
  eq_(['a', 'b', 'c'], list(jprops._property_lines(fp)))


def test_property_lines_mac():
  fp = StringIO('a\rb\rc\r')
  eq_(['a', 'b', 'c'], list(jprops._property_lines(fp)))


def test_property_lines_skips_blanks():
  fp = StringIO('a\nb\n \t \n\nc\n')
  eq_(['a', 'b', 'c'], list(jprops._property_lines(fp)))


def test_property_lines_skips_comments():
  fp = StringIO('a\nb\n#foo\n!bar\nc\n')
  eq_(['a', 'b', 'c'], list(jprops._property_lines(fp)))


def test_property_lines_continuation():
  fp = StringIO('a\nb\\\nc\nd\n')
  eq_(['a', 'bc', 'd'], list(jprops._property_lines(fp)))


def test_property_lines_continuation_includes_trailing_blanks():
  fp = StringIO('a\nb \\\nc\nd\n')
  eq_(['a', 'b c', 'd'], list(jprops._property_lines(fp)))


def test_property_lines_continuation_skips_leading_blanks():
  fp = StringIO('a\nb\\\n c\nd\n')
  eq_(['a', 'bc', 'd'], list(jprops._property_lines(fp)))


def test_property_lines_escaped_backslash_not_continuation():
  fp = StringIO('a\nb\\\\\nc\nd\n')
  eq_(['a', 'b\\\\', 'c', 'd'], list(jprops._property_lines(fp)))


def test_property_lines_escaped_backslash_before_continuation():
  fp = StringIO('a\nb\\\\\\\nc\nd\n')
  eq_(['a', 'b\\\\c', 'd'], list(jprops._property_lines(fp)))


# TODO test lines with trailing spaces


def test_split_key_value_equals():
  eq_(('a', 'b'), jprops._split_key_value('a=b'))
  eq_(('a', 'b'), jprops._split_key_value('a= b'))
  eq_(('a', 'b'), jprops._split_key_value('a = b'))
  eq_(('a', 'b'), jprops._split_key_value('a =b'))


def test_split_key_value_colon():
  eq_(('a', 'b'), jprops._split_key_value('a:b'))
  eq_(('a', 'b'), jprops._split_key_value('a: b'))
  eq_(('a', 'b'), jprops._split_key_value('a : b'))
  eq_(('a', 'b'), jprops._split_key_value('a :b'))


def test_key_terminator_after_terminated():
  eq_(('a', ': b'), jprops._split_key_value('a : : b'))
  eq_(('a', ':b'), jprops._split_key_value('a::b'))
  eq_(('a', '= b'), jprops._split_key_value('a = = b'))
  eq_(('a', '=b'), jprops._split_key_value('a==b'))
  eq_(('a', ': b'), jprops._split_key_value('a = : b'))
  eq_(('a', '= b'), jprops._split_key_value('a : = b'))


def test_key_terminator_escaped():
  eq_((r'a\=b', 'c'), jprops._split_key_value(r'a\=b = c'))
  eq_((r'a\:b\=c', 'd'), jprops._split_key_value(r'a\:b\=c : d'))


def test_split_key_value_space():
  eq_(('a', 'b'), jprops._split_key_value('a b'))


def test_split_key_value_empty_value():
  eq_(('a', ''), jprops._split_key_value('a'))


def test_unescape_basic():
  eq_('\t', jprops._unescape(r'\t'))
  eq_('\n', jprops._unescape(r'\n'))
  eq_('\f', jprops._unescape(r'\f'))
  eq_('\r', jprops._unescape(r'\r'))


def test_unescape_unrecognized():
  eq_('=', jprops._unescape(r'\='))
  eq_(':', jprops._unescape(r'\:'))
  eq_('b', jprops._unescape(r'\b'))


def test_unescape_unicode():
  eq_(u'\u00ff', jprops._unescape(r'\u00ff'))


def test_unescape_unicode_encoded_backslassh():
  eq_(ur'\b', jprops._unescape(r'\u005cb'))


def test_unescape_unicode_escaped():
  eq_(r'\u00ff', jprops._unescape(r'\\u00ff'))
  eq_(u'\\\u00ff', jprops._unescape(r'\\\u00ff'))
  eq_(r'\\u00ff', jprops._unescape(r'\\\\u00ff'))


def test_unescape_decodes_ascii_to_str():
  eq_(str, type(jprops._unescape('x')))
  eq_(str, type(jprops._unescape(chr(127))))


def test_unescape_decodes_latin1_to_unicode():
  eq_(unicode, type(jprops._unescape('\xff')))
  eq_(unicode, type(jprops._unescape(chr(128))))


def test_escape_basic():
  eq_('\\\\', jprops._escape('\\'))
  eq_(r'\t', jprops._escape('\t'))
  eq_(r'\n', jprops._escape('\n'))
  eq_(r'\f', jprops._escape('\f'))
  eq_(r'\r', jprops._escape('\r'))


def test_escape_unicode():
  eq_(r'\u0000', jprops._escape('\x00'))
  eq_(r'\u0000', jprops._escape(u'\u0000'))
  eq_(r'\u0019', jprops._escape('\x19'))
  eq_(r'\u0019', jprops._escape(u'\u0019'))
  eq_(r'\u007f', jprops._escape('\x7f'))
  eq_(r'\u007f', jprops._escape(u'\u007f'))
  eq_(r'\uffff', jprops._escape(u'\uffff'))

  eq_(str, type(jprops._escape(u'\uffff')))


def test_escape_value_leading_whitespace():
  eq_(r'\ \ x\ty ', jprops._escape_value('  x\ty '))


def test_escape_keys():
  eq_(r'\=', jprops._escape_key('='))
  eq_(r'\:', jprops._escape_key(':'))
  eq_(r'\ x\ ', jprops._escape_key(' x '))


def test_escape_comment_newline():
  eq_('#foo\n#bar', jprops._escape_comment('foo\nbar'))
  eq_('#foo\n#\n#bar', jprops._escape_comment('foo\n\nbar'))
  eq_('#foo\n#bar', jprops._escape_comment('foo\rbar'))
  eq_('#foo\n#\n#bar', jprops._escape_comment('foo\r\rbar'))
  eq_('#foo\n#bar', jprops._escape_comment('foo\r\nbar'))
  eq_('#foo\n#\n#bar', jprops._escape_comment('foo\r\n\r\nbar'))
  eq_('#foo\n#', jprops._escape_comment('foo\n'))


def test_escape_comment_newline_already_commented():
  eq_('#foo\n#bar', jprops._escape_comment('foo\n#bar'))
  eq_('#foo\n!bar', jprops._escape_comment('foo\n!bar'))


def test_escape_comment_unicode():
  eq_('#\xff', jprops._escape_comment(u'\u00ff'))
  eq_(r'#\u0100', jprops._escape_comment(u'\u0100'))
