import io
import os
import tempfile

import pytest
import jpype

import jprops


@pytest.fixture(scope="module")
def java(request):
  jpype.startJVM(jpype.getDefaultJVMPath(), "-ea")
  request.addfinalizer(jpype.shutdownJVM)
  return jpype.java


def java_load(data):
  java = jpype.java
  props = java.util.Properties()
  props.load(java.io.ByteArrayInputStream(data))
  return dict(props)


def jprops_load(data):
  return jprops.load_properties(io.BytesIO(data))


def jprops_store(fp, props):
  jprops.store_properties(fp, props, timestamp=False)


def jproperties_load(data):
  import jproperties
  props = jproperties.Properties()
  if str == bytes:
    buf = io.BytesIO(data)
  else:
    # jproperties on Python 3 doesn't support BytesIO, but we can decode
    # the data for it
    buf = io.StringIO(data.decode('latin-1'))
  props.load(buf)
  return dict(props.items())


def jproperties_store(fp, props):
  import jproperties
  p = jproperties.Properties()
  for k, v in props.items():
    p[k] = v
  data = str(p)
  if not isinstance(data, bytes):
    data = data.encode('latin-1')
  fp.write(data)


def pyjavaproperties_load(data):
  import pyjavaproperties

  p = pyjavaproperties.Properties()

  tmp = tempfile.NamedTemporaryFile(delete=False)
  try:
    with tmp:
      tmp.write(data)
    with open(tmp.name) as fp:
      p.load(fp)
  finally:
    os.remove(tmp.name)

  return p.getPropertyDict()


def pyjavaproperties_store(fp, props):
  import pyjavaproperties

  p = pyjavaproperties.Properties()
  for k, v in props.items():
    p[k] = v

  tmp = tempfile.NamedTemporaryFile(delete=False)
  try:
    p.store(tmp)
    with open(tmp.name, 'rb') as tmpfp:
      fp.write(tmpfp.read())
  finally:
    os.remove(tmp.name)


implementations = {
  'jprops': (jprops_load, jprops_store),
  'jproperties': (jproperties_load, jproperties_store),
  'pyjavaproperties': (pyjavaproperties_load, pyjavaproperties_store),
}


@pytest.fixture(params=sorted(implementations))
def properties_impl(request):
  impl_name = request.param

  if impl_name != 'jprops':
    request.applymarker(pytest.mark.xfail)
    request.applymarker(pytest.mark.third_party)

  return implementations[impl_name]


load_tests = [
  # Key value with equals
  b'a=b',
  b'a= b',
  b'a = b',
  b'a =b',

  # Key value with colon
  b'a:b',
  b'a: b',
  b'a : b',
  b'a :b',

  # Key terminator after terminator
  b'a : : b',
  b'a::b',
  b'a = = b',
  b'a==b',
  b'a = : b',
  b'a : = b',

  # Key terminator escaped
  br'a\=b = c',
  br'a\:b\=c : d',

  # Key value with space only
  b'a b',

  # Key value empty value
  b'a',

  # Escaping
  # Basic backslash escapes
  b'a \\t',
  b'a \\n',
  b'a \\f',
  b'a \\r',

  # Unrecognized escapes
  br'a \=',
  br'a \:',
  br'a \b',

  # Unicode escape
  br'a \u00ff',

  # Unicode encoded backslash
  br'a \u005cb',

  # Unicode with preceding escaped backslashes
  br'a \\u00ff',
  br'a \\\u00ff',
  br'a \\\\u00ff',

  # Latin-1 encoded bytes
  b'a \x7f',

  # Escaped backslash
  b'a \\\\x7f',

  # Line endings
  # Simple
  b'a\nb\nc\n',
  # Windows newlines
  b'a\r\nb\r\nc\r\n',
  # Mac newlines
  b'a\rb\rc\r',
  # Blank lines
  b'a\nb\n \t \n\nc\n',
  # Line continuation
  b'a\nb\\\nc\nd\n',
  # Line continuation trailing blanks
  b'a\nb \\\nc\nd\n',
  # Line continuation skips leading blanks
  b'a\nb\\\n c\nd\n',
  # Escaped backslash not continuation
  b'a\nb\\\\\nc\nd\n',
  # Escaped backslash before continuation
  b'a\nb\\\\\\\nc\nd\n',
]


@pytest.mark.parametrize('data', load_tests)
def test_load(properties_impl, data, java):
  reader, _  = properties_impl
  assert reader(data) == java_load(data)


store_tests = [
  # Simple
  {'a': 'b'},

  # Escaping basic
  {'a': '\\'},
  {'a': 'x \t'},
  {'a': 'x \n'},
  {'a': 'x \f'},
  {'a': 'x \r'},

  # Escape whitespace-only value
  {'a': '\t'},
  {'a': '\n'},
  {'a': '\f'},
  {'a': '\r'},

  # Escape unicode
  {'a': '\x00'},
  {'a': u'\u0000'},
  {'a': '\x19'},
  {'a': u'\u0019'},
  {'a': '\x7f'},
  {'a': u'\u007f'},
  {'a': u'\uffff'},

  # Escape value leading whitespace
  {'a': '  x\ty '},

  # Escape key terminators
  {'=': ''},
  {':': ''},
  {' x ': ''},

  # Escape key terminators in value
  {'a': '='},
  {'a': ':'},

  # Escape comment markers
  {'a': '#'},
  {'a': '!'},
]


@pytest.mark.parametrize('props', store_tests)
def test_store(properties_impl, props, java):
  _, writer  = properties_impl
  fp = io.BytesIO()
  writer(fp, props)
  assert java_load(fp.getvalue()) == props
