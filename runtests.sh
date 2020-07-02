#!/bin/bash
#PKGDB_CONFIG=../tests/nuancier_test.cfg PYTHONPATH=nuancier nosetests \
NUANCIER_CONFIG=`pwd`/tests/config \
PYTHONPATH=nuancier ./nosetests \
--with-coverage --cover-erase --cover-package=nuancier $*
