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

import datetime

import wtforms as wtf
# pylint cannot import flask extension correctly
# pylint: disable=E0611,F0401
from flask.ext import wtf as flask_wtf

from nuancier import APP


# We apparently use old style super in our __init__
# pylint: disable=E1002
# One of our forms does not even have __init__
# pylint: disable=W0232
# Couple of our forms do not have enough methods
# pylint: disable=R0903

# Yes we do nothing with the form argument but it's required...
# pylint: disable=W0613
def is_number(form, field):
    ''' Check if the data in the field is a number and raise an exception
    if it is not.
    '''
    try:
        float(field.data)
    except ValueError:
        raise wtf.ValidationError('Field must contain a number')


class BaseForm(flask_wtf.Form):
    """
    Provide a base form class.

    For new versions of flask-wtf (greater than 0.10.0), this behaves exactly
    like :class:`flask_wtf.Form`.

    Versions of flask-wtf prior to 0.10.0 did not have or did not properly use
    the 'WTF_CSRF_TIME_LIMIT' setting. This configures the self.TIME_LIMIT
    value used by flask-wtf if the delta is not None and it's an old version of
    flask-wtf. See https://github.com/lepture/flask-wtf/issues/131 for more
    information.
    """

    def __init__(self, *args, **kwargs):
        delta = APP.config.get('WTF_CSRF_TIME_LIMIT', 3600)

        try:
            version_tuple = tuple(int(v) for v in flask_wtf.__version__.split('.'))
            old_version = version_tuple <= (0, 10, 0)
        except AttributeError:
            # Prior to 0.9.2, there was no __version__ attribute
            old_version = True

        if delta and old_version:
            # Annoyingly, in the old version this needs to be a timedelta, but later
            # versions expect it to be an integer.
            self.TIME_LIMIT = datetime.timedelta(seconds=delta)

        super(BaseForm, self).__init__(*args, **kwargs)


class AddElectionForm(BaseForm):
    ''' Form to add a new election. '''
    election_name = wtf.TextField(
        'Election name',
        [wtf.validators.Required()])
    election_folder = wtf.TextField(
        'Name of the folder containing the pictures',
        [wtf.validators.Required()])
    election_year = wtf.TextField(
        'Year',
        [wtf.validators.Required()])
    submission_date_start = wtf.DateField(
        'Submission start date (in utc)',
        [wtf.validators.Required()])
    election_date_start = wtf.DateField(
        'Start date (in utc)',
        [wtf.validators.Required()])
    election_date_end = wtf.DateField(
        'End date (in utc)',
        [wtf.validators.Required()])
    election_badge_link = wtf.TextField(
        'URL to claim a badge for voting',
        [wtf.validators.URL(), wtf.validators.Optional()])
    election_n_choice = wtf.TextField(
        'Number of votes an user can make',
        [wtf.validators.Required(), is_number])
    user_n_candidates = wtf.TextField(
        'Number of candidate an user can upload',
        [wtf.validators.Required(), is_number])
    generate_cache = wtf.BooleanField('Generate cache')

    def __init__(self, *args, **kwargs):
        ''' Calls the default constructor and fill in additional information.
        '''
        super(AddElectionForm, self).__init__(*args, **kwargs)

        if 'election' in kwargs:
            election = kwargs['election']
            self.election_name.data = election.election_name
            self.election_folder.data = election.election_folder
            self.election_year.data = election.election_year
            self.election_date_start.data = election.election_date_start
            self.election_date_end.data = election.election_date_end
            self.election_badge_link.data = election.election_badge_link
            self.election_n_choice.data = election.election_n_choice
            self.submission_date_start.data = election.submission_date_start
            self.user_n_candidates.data = election.user_n_candidates


class AddCandidateForm(BaseForm):
    ''' Form to add a candidate to an election. '''
    candidate_name = wtf.TextField(
        'Title', [wtf.validators.Required()])
    candidate_author = wtf.TextField(
        'Author', [wtf.validators.Required()])
    candidate_original_url = wtf.TextField(
        'URL to the original artwork')
    candidate_file = wtf.FileField(
        'File', [wtf.validators.Required()])
    candidate_license = wtf.SelectField(
        'License', [wtf.validators.Required()],
        choices=[
            (None, ''),
            ('CC0', 'CC0'),
            ('CC-BY', 'CC-BY'),
            ('CC-BY-SA', 'CC-BY-SA'),
            ('DSL', 'DSL'),
            ('Free Art', 'Free Art'),
        ])

    def __init__(self, *args, **kwargs):
        ''' Calls the default constructor and fill in default values.
        '''
        super(AddCandidateForm, self).__init__(*args, **kwargs)


class ConfirmationForm(BaseForm):
    ''' Simply, dummy form used for csrf validation. '''
    pass
