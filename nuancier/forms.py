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
## pylint cannot import flask extension correctly
# pylint: disable=E0611,F0401
from flask.ext import wtf as flask_wtf


## We apparently use old style super in our __init__
# pylint: disable=E1002
## One of our forms does not even have __init__
# pylint: disable=W0232
## Couple of our forms do not have enough methods
# pylint: disable=R0903

## Yes we do nothing with the form argument but it's required...
# pylint: disable=W0613
def is_number(form, field):
    ''' Check if the data in the field is a number and raise an exception
    if it is not.
    '''
    try:
        float(field.data)
    except ValueError:
        raise wtf.ValidationError('Field must contain a number')


class AddElectionForm(flask_wtf.Form):
    ''' Form to add a new election. '''
    election_name = wtf.TextField(
        'Election name <span class="error">*</span>',
        [wtf.validators.Required()])
    election_folder = wtf.TextField(
        'Name of the folder containing the pictures <span class="error">*</span>',
        [wtf.validators.Required()])
    election_year = wtf.TextField(
        'Year <span class="error">*</span>',
        [wtf.validators.Required()])
    submission_date_start = wtf.DateField(
        'Submission start date (in utc) <span class="error">*</span>',
        [wtf.validators.Required()])
    election_date_start = wtf.DateField(
        'Start date (in utc) <span class="error">*</span>',
        [wtf.validators.Required()])
    election_date_end = wtf.DateField(
        'End date (in utc) <span class="error">*</span>',
        [wtf.validators.Required()])
    election_badge_link = wtf.TextField(
        'URL to claim a badge for voting',
        [wtf.validators.URL(), wtf.validators.Optional()])
    election_n_choice = wtf.TextField(
        'Number of votes a user can make <span class="error">*</span>',
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


class AddCandidateForm(flask_wtf.Form):
    ''' Form to add a candidate to an election. '''
    candidate_name = wtf.TextField(
        'Title <span class="error">*</span>', [wtf.validators.Required()])
    candidate_author = wtf.TextField(
        'Author <span class="error">*</span>', [wtf.validators.Required()])
    candidate_original_url = wtf.TextField(
        'URL to the original artwork')
    candidate_file = wtf.FileField(
        'File <span class="error">*</span>', [wtf.validators.Required()])
    candidate_license = wtf.SelectField(
        'License <span class="error">*</span>', [wtf.validators.Required()],
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

        if 'author' in kwargs:
            self.candidate_author.data = kwargs['author']


class ConfirmationForm(flask_wtf.Form):
    ''' Simply, dummy form used for csrf validation. '''
    pass
