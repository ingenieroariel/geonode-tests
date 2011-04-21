#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from distutils.core import setup, Command
from setuptools import setup, Command
from distutils.command.install_data import install_data
from distutils.command.install import INSTALL_SCHEMES
import os
import sys
import codecs

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

def add_dir(source_dir):
    for dirpath, dirnames, filenames in os.walk(source_dir):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'): del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(dirpath)))
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

add_dir('tests')

long_description = codecs.open('README.rst', 'r', 'utf-8').read()

setup(
    name='geonode-tests',
    version='0.1',
    description='GeoNode integration test suite',
    author='Jeffrey Johnson, Ariel Nunez',
    author_email='jjohnson@opengeo.org',
    url='http://geonode.org',
    platforms=['any'],
    license='GPL',
    packages=packages,
    data_files=data_files,
    scripts = ['scripts/geonode-test',
#               'scripts/geonode-clean',
              ],
    classifiers = [
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
   ],
   long_description=long_description,
)
