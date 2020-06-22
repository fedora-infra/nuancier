#!/usr/bin/env python
import os

os.system('pip install --upgrade pip')
os.system('pip3 install -r requirements.txt')
os.system('python3 createdb.py')
os.system('sudo firewall-cmd --add-port 5000/tcp --permanent')
os.system('sudo firewall-cmd --reload')
os.system('python3 runserver.py --host 0.0.0.0')
