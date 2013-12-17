# -*- coding: utf-8 -*-

__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources
import os

os.environ['NUANCIER_CONFIG'] = '/etc/nuancier/nuancier.cfg'

from nuancier import APP, SESSION, lib

election = lib.get_election(SESSION, 1)
lib.generate_cache(
    SESSION,
    election,
    APP.config['PICTURE_FOLDER'],
    APP.config['CACHE_FOLDER'],
    APP.config['THUMB_SIZE'],
)
