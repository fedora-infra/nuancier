# -*- coding: utf-8 -*-
#
# Copyright © 2013  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

'''
nuancier default configuration.
'''

import os

from datetime import timedelta

# Set the time after which the session expires
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

# The length of time a CSRF token is valid in seconds. If you are running
# flask-wtf-0.10.1 or greater, you can set this to ``None`` to bind the CSRF
# lifetime to the life of the session.
WTF_CSRF_TIME_LIMIT = 3600

# url to the database server:
DB_URL = 'sqlite:////var/tmp/nuancier_lite.sqlite'

# secret key used to generate unique csrf token
SECRET_KEY = '<insert here your own key>'

# FAS group for the nuancier admin
#ADMIN_GROUP = 'sysadmin-nuancier'
ADMIN_GROUP = ('sysadmin-main', 'sysadmin-nuancier')

# FAS group for the nuancier reviewers
REVIEW_GROUP = ('designteam')

# FAS group of users having a higher vote
WEIGHTED_GROUP = ('sysadmin-nuancier', 'designteam')

# Pictures folder
PICTURE_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'pictures')

# Cache folder
CACHE_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'cache')

# Size of the thumbnails (keeping the ratio)
THUMB_SIZE = (256, 256)

# The default backend for dogpile
# Options are listed at:
# http://dogpilecache.readthedocs.org/en/latest/api.html  (backend section)
NUANCIER_CACHE_BACKEND = 'dogpile.cache.memory'

ALLOWED_EXTENSIONS = ['svg', 'png', 'jpeg', 'jpg']
ALLOWED_MIMETYPES = [
    'image/jpeg',
    'image/jpg',
    'image/png',
]

# allow portrait oriented pictures
ALLOW_PORTRAIT = False

PICTURE_MIN_WIDTH = 1600
PICTURE_MIN_HEIGHT = 1200

# Flask configuration option
# Set the maximum size of an upload someone may do, defaults here to 16MB
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# A boolean specifying wether to send email notifications are not when a
# submission is rejected.
NUANCIER_EMAIL_NOTIFICATIONS = False
# The email address that the notifications are sent from
NUANCIER_EMAIL_FROM = 'nobody@fedoraproject.org'
# The smtp server to use to send the notifications
NUANCIER_EMAIL_SMTP_SERVER = 'localhost'
# The email address to send error report to
NUANCIER_EMAIL_ERROR_TO = 'pingou@pingoured.fr'

FEDMENU_URL = 'https://apps.fedoraproject.org/fedmenu'
FEDMENU_DATA_URL = 'https://apps.fedoraproject.org/js/data.js'
