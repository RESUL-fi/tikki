[![Build Status](https://travis-ci.com/tikki-fi/tikki.svg?branch=master)](https://travis-ci.com/tikki-fi/tikki)
[![PyPI version](https://img.shields.io/pypi/v/tikki.svg)](https://badge.fury.io/py/tikki)
[![codecov](https://codecov.io/gh/tikki-fi/tikki/branch/master/graph/badge.svg)](https://codecov.io/gh/tikki-fi/tikki)
[![PyPI](https://img.shields.io/pypi/pyversions/tikki.svg)](https://www.python.org/downloads/)
[![PyPI license](https://img.shields.io/pypi/l/tikki.svg)](https://opensource.org/licenses/MIT)

# Tikki #

Tikki is the application for collection and management of field aptitude 
perfomance data of Finnish reservists. Key features are easy and fast result 
recording and controlled authorization of results. The development of the 
app is managed by Lisää liikettä program, led by the Finnish Reservist 
Sports Federation (RESUL).

## Organisation ##

Tikki is an open source project managed by the Reserviläisurheiluliitto Ry
(RESUL). https://resul.fi/

## Requirements ##

The service runs on Python 3.6, and currently supports Postgres 9.3+. Since database
connections are done using SQLAlchemy, support can easily be added for other database
types that support full JSON semantics.

## Developer's guide ##

Below are instructions for initializing and operating the development environment.

### Initializing development environment ###

We recomment using pipenv for managing a virtualenv, which can be installed as follows:

```bash
pip install pipenv
pipenv --install --three -r requirements.txt
```

### Installing local development database ###

We recommend installing using a dockerized Postgres 9.3+ database for development.
To do this, run the following

```bash
docker run -d -p 5432:5432 --name tikki-postgres -e POSTGRES_PASSWORD=tikkipwd postgres
```

### Creating new database migration ###

Tikki uses alembic to manage database revisions. To create a new migration run tikki
using the `--create` (or `-c` for short):

```bash
python tikki --create "my new migration"
```

### Bumping dependencies ###

`requirements.txt` is dynamically generated with pinned versions using pip-compile from 
`setup.py` and `requirements-dev.in`, tha latter which contains dependencies only needed 
for developent. It is recommended to regenerate requirements every once in a while with
the following command:

```bash
pip-compile -U --output-file requirements.txt setup.py requirements-dev.in
```

This overwrites the old version of `requirements.txt` with the most recent pinned
versions of all dependencies.
