#!/bin/bash
#PKGDB_CONFIG=../tests/nuancier_test.cfg PYTHONPATH=nuancier nosetests \
PYTHONPATH=nuancier ./nosetests \
--with-coverage --cover-erase --cover-package=nuancier $*
