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
    election_date_start = wtf.DateField('Start date (in utc)',
                                        [wtf.validators.Required()])
    election_date_end = wtf.DateField('End date (in utc)',
                                      [wtf.validators.Required()])
    election_badge_link = wtf.TextField('URL to claim a badge for voting',
                                        [wtf.validators.URL(),
                                         wtf.validators.Optional()])
    election_n_choice = wtf.TextField('Number of votes a user can make',
                                      [wtf.validators.Required(),
                                       is_number])
    generate_cache = wtf.BooleanField('Generate cache')

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor and fill in additional information.
        """
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


class AddCandidateForm(flask_wtf.Form):
    candidate_name = wtf.TextField(
        'Name', [wtf.validators.Required()])
    candidate_author = wtf.TextField(
        'Author', [wtf.validators.Required()])
    candidate_file = wtf.FileField(
        'File', [wtf.validators.Required()])
    candidate_license = wtf.TextField(
        'License', [wtf.validators.Required()])

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor and fill in default values.
        """
        super(AddCandidateForm, self).__init__(*args, **kwargs)

        self.candidate_author.data = flask.g.fas_user.username
        self.candidate_license.data = 'CC-BY-SA'


class ConfirmationForm(flask_wtf.Form):
    pass
