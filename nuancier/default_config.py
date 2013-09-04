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
nuancier-lite default configuration.
'''

import os

# url to the database server:
DB_URL = 'sqlite:////var/tmp/nuancier_lite.sqlite'

# secret key used to generate unique csrf token
SECRET_KEY = '<insert here your own key>'

# FAS group for the pkgdb admin
#ADMIN_GROUP = 'sysadmin-nuancier'
ADMIN_GROUP = 'sysadmin-main'

# Pictures folder
PICTURE_FOLDER = os.path.join(os.path.dirname(__file__), 'pictures')

# Cache folder
CACHE_FOLDER = os.path.join(os.path.dirname(__file__), 'cache')

# Size of the thumbnails (keeping the ratio)
THUMB_SIZE = (256, 256)
