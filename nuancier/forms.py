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
WTF Forms of the nuancier Flask application.
'''

import flask
import wtforms as wtf
from flask.ext import wtf as flask_wtf


def is_number(form, field):
    try:
        float(field.data)
    except ValueError:
        raise wtf.ValidationError('Field must contain a number')


class AddElectionForm(flask_wtf.Form):
    election_name = wtf.TextField('Election name',
                                  [wtf.validators.Required()])
    election_folder = wtf.TextField(
        'Name of the folder containing the pictures',
        [wtf.validators.Required()])
    election_year = wtf.TextField('Year',
                                  [wtf.validators.Required()])
    election_open = wtf.BooleanField('Open')
    election_badge_link = wtf.TextField('URL to claim a badge for voting',
                                        [wtf.validators.URL(),
                                         wtf.validators.Optional()])
    election_n_choice = wtf.TextField('Number of votes a user can make',
                                      [wtf.validators.Required(),
                                       is_number])
    generate_cache = wtf.BooleanField('Generate cache')
