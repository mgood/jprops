import re
import string
import time


def load_properties(fh, mapping=dict):
  """
    Reads properties from a Java .properties file.

    Returns a dict (or provided mapping) of properties.

    :param fh: a readable file-like object
    :param mapping: mapping type to load properties into
  """
  return mapping(iter_properties(fh))


def store_properties(fh, props, comment=None, timestamp=True):
  """
    Writes properties to the file in Java properties format.

    :param fh: a writable file-like object
    :param props: a mapping (dict) or iterable of key/value pairs
    :param comment: comment to write to the beginning of the file
    :param timestamp: boolean indicating whether to write a timestamp comment
  """
  if comment is not None:
    write_comment(fh, comment)

  if timestamp:
    write_comment(fh, time.strftime('%a %b %d %H:%M:%S %Z %Y'))

  if hasattr(props, 'keys'):
    for key in props:
      write_property(fh, key, props[key])
  else:
    for key, value in props:
      write_property(fh, key, value)


def write_comment(fh, comment):
  """
    Writes a comment to the file in Java properties format.

    Newlines in the comment text are automatically turned into a continuation
    of the comment by adding a "#" to the beginning of each line.

    :param fh: a writable file-like object
    :param comment: comment string to write
  """
  fh.write(_escape_comment(comment))
  fh.write('\n')


def write_property(fh, key, value):
  """
    Write a single property to the file in Java properties format.

    :param fh: a writable file-like object
    :param key: the key to write
    :param value: the value to write
  """
  fh.write(_escape_key(key))
  fh.write('=')
  fh.write(_escape_value(value))
  fh.write('\n')


def iter_properties(fh):
  """
    Incrementally read properties from a Java .properties file.

    Yields tuples of key/value pairs.

    :param fh: a readable file-like object
  """
  for line in _property_lines(fh):
    key, value = _split_key_value(line)
    yield _unescape(key), _unescape(value)


################################################################################
# Helpers for property parsing/writing
################################################################################


_COMMENT_CHARS = '#!'
_LINE_PATTERN = re.compile(r'^\s*(?P<body>.*?)(?P<backslashes>\\*)$')
_KEY_TERMINATORS_EXPLICIT = '=:'
_KEY_TERMINATORS = _KEY_TERMINATORS_EXPLICIT + string.whitespace


_escapes = {
  't': '\t',
  'n': '\n',
  'f': '\f',
  'r': '\r',
}
_escapes_rev = dict((v, '\\' + k) for k,v in _escapes.iteritems())
for c in '\\' + _COMMENT_CHARS + _KEY_TERMINATORS_EXPLICIT:
  _escapes_rev.setdefault(c, '\\' + c)


def _unescape(value):
  try:
    value.decode('ascii')
  except UnicodeDecodeError:
    value = value.decode('latin-1')

  def unirepl(m):
    backslashes = m.group(1)
    charcode = m.group(2)

    # if preceded by even number of backslashes, the \u is escaped
    if len(backslashes) % 2 == 0:
      return m.group(0)

    c = unichr(int(charcode, 16))
    # if unicode decodes to '\', re-escape it to unescape in the second step
    if c == '\\':
      c = u'\\\\'

    return backslashes + c

  value = re.sub(r'(\\+)u([0-9a-fA-F]{4})', unirepl, value)

  def bslashrepl(m):
    code = m.group(1)
    return _escapes.get(code, code)

  return re.sub(r'\\(.)', bslashrepl, value)


def _escape_comment(comment):
  comment = comment.replace('\r\n', '\n').replace('\r', '\n')
  comment = re.sub(r'\n(?![#!])', '\n#', comment)
  if isinstance(comment, unicode):
    comment = re.sub(u'[\u0100-\uffff]', _unicode_replace, comment)
    comment = comment.encode('latin-1')
  return '#' + comment


def _escape_key(key):
  return _escape(key, _KEY_TERMINATORS)


def _escape_value(value):
  tail = value.lstrip()
  if len(tail) < len(value):
    head = value[:-len(tail)]
    # escape any leading whitespace, but leave other spaces intact
    return _escape(head, string.whitespace) + _escape(tail)
  else:
    return _escape(value)


def _escape(value, chars=''):
  escape_chars = set(_escapes_rev)
  escape_chars.update(chars)
  escape_pattern = '[%s]' % re.escape(''.join(escape_chars))

  def esc(m):
    c = m.group(0)
    return _escapes_rev.get(c) or '\\' + c
  value = re.sub(escape_pattern, esc, value)

  value = re.sub(u'[\u0000-\u0019\u007f-\uffff]', _unicode_replace, value)

  return value.encode('latin-1')


def _unicode_replace(m):
  c = m.group(0)
  return r'\u%.4x' % ord(c)


def _split_key_value(line):
  escaped = False
  key_buf = []

  for idx, c in enumerate(line):
    if not escaped and c in _KEY_TERMINATORS:
      key_terminated_fully = c in _KEY_TERMINATORS_EXPLICIT
      break

    key_buf.append(c)
    escaped = c == '\\'

  else:
    # no key terminator, key is full line & value is blank
    return line, ''

  value = line[idx+1:].lstrip()
  if not key_terminated_fully and value[:1] in _KEY_TERMINATORS_EXPLICIT:
    value = value[1:].lstrip()

  return ''.join(key_buf), value


def _universal_newlines(fp):
  """
    Wrap a file to convert newlines regardless of whether the file was opened
    with the "universal newlines" option or not.
  """
  # if file was opened with universal newline support we don't need to convert
  if 'U' in getattr(fp, 'mode', ''):
    for line in fp:
      yield line
  else:
    for line in fp:
      line = line.replace('\r\n', '\n').replace('\r', '\n')
      for piece in line.split('\n'):
        yield piece


def _property_lines(fp):
  buf = []
  for line in _universal_newlines(fp):
    m = _LINE_PATTERN.match(line)

    body = m.group('body')
    backslashes = m.group('backslashes')

    if len(backslashes) % 2 == 0:
      body += backslashes
      continuation = False
    else:
      body += backslashes[:-1]
      continuation = True

    if not body or body[0] in _COMMENT_CHARS:
      continue

    buf.append(body)

    if not continuation:
      yield ''.join(buf)
      buf = []
