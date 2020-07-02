#!/usr/bin/env python2

# These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.8', 'jinja2 >= 2.4']
import pkg_resources

import argparse
import sys
import os


parser = argparse.ArgumentParser(
    description='Run the web app')
parser.add_argument(
    '--config', '-c', dest='config',
    help='Configuration file to use for nuancier.')
parser.add_argument(
    '--debug', dest='debug', action='store_true',
    default=False,
    help='Expand the level of data returned.')
parser.add_argument(
    '--profile', dest='profile', action='store_true',
    default=False,
    help='Profile the web application.')
parser.add_argument(
    '--port', '-p', default=5005,
    help='Port where the app should run.')
parser.add_argument(
    '--host', default="127.0.0.1",
    help='Hostname to listen on. When set to 0.0.0.0 the server is available '
         'externally. Defaults to 127.0.0.1 making the it only visable on '
         'localhost')

args = parser.parse_args()

if args.config:
    config = args.config
    if not config.startswith('/'):
        config = os.path.join(os.getcwd(), config)
    os.environ['NUANCIER_CONFIG'] = config

from nuancier import APP

if args.profile:
    from werkzeug.contrib.profiler import ProfilerMiddleware
    APP.config['PROFILE'] = True
    APP.wsgi_app = ProfilerMiddleware(APP.wsgi_app, restrictions=[30])

APP.debug = True
APP.run(host=args.host, port=int(args.port))
