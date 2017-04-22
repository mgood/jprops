#!/usr/bin/python

import os
import setuptools


here = os.path.abspath(os.path.dirname(__file__))

try:
  README = open(os.path.join(here, 'README.rst')).read()
  CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
except:
  README = ''
  CHANGES = ''


setuptools.setup(
  name = 'jprops',
  version = '2.0.2',
  license = 'BSD',
  description = 'Parser for Java .properties files',
  long_description=README + '\n\n' + CHANGES,
  author = 'Matt Good',
  author_email = 'matt@matt-good.net',
  url = 'http://github.com/mgood/jprops/',
  platforms = 'any',

  py_modules = ['jprops'],

  zip_safe = True,
  verbose = False,
)
