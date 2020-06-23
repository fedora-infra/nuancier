#!/usr/bin/env python
from os import system

if __name__ == "__main__":
    os.system('python3 createdb.py')
    os.system('python3 runserver.py --host 0.0.0.0')
