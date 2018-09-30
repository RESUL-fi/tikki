# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

setup(
    name='tikki',
    version='0.9.0',
    description='Tikki Field Aptitude Performance Data Collection Platform',
    long_description=readme,
    long_description_content_type="text/markdown",
    author='RESUL Ry',
    author_email='info@resul.fi',
    maintainer='Ville Brofeldt',
    maintainer_email='ville.brofeldt@streamroller.io',
    url='https://github.com/tikki-fi/tikki',
    license='MIT',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'alembic',
        'flask',
        'flask-cors',
        'flask-jwt-simple',
        'python-dateutil',
        'sqlalchemy',
        'sqlalchemy-utils',
        'werkzeug',
    ],
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
    ],
)
