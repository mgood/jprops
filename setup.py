#!/usr/bin/python

import setuptools

setuptools.setup(
  name = 'jprops',
  version = '0.2',
  license = 'BSD',
  description = open('README.txt').read(),
  author = 'Matt Good',
  author_email = 'matt@matt-good.net',
  url = 'http://mgood.github.com/jprops/',
  platforms = 'any',

  py_modules = ['jprops'],

  zip_safe = True,
  verbose = False,
)
