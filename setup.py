# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

setup(
    name='tikki',
    version='0.999',
    description='Tikki Field Aptitude Performance Data Collection Platform',
    long_description=readme,
    author='Reserviläisurheiluliitto Ry',
    author_email='info@resul.fi',
    url='https://github.com/tikki-fi/tikki',
    packages=find_packages(exclude=('tests', 'docs'))
)
