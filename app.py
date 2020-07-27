#!/usr/bin/env python
from os import system

if __name__ == "__main__":
    system('python3 createdb.py')
    system('pip install -e git+https://github.com/jontrossbach/flask-oidc.git#egg=flask-oidc')
    system('oidc-register https://iddev.fedorainfracloud.org/ http://localhost:8080/oidc_callback')
    system('cp client_secrets.json nuancier/client_secrets.json')
    system('python3 runserver.py --host 0.0.0.0 --port 8080 -c config')

