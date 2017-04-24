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
nuancier tests for the sqlalchemy model
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

from datetime import timedelta, datetime

import six
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import nuancier.lib as nuancierlib
from nuancier.lib import model
from tests import (Modeltests, create_elections, create_candidates,
                   create_votes, CACHE_FOLDER, PICTURE_FOLDER, TODAY)


class NuancierModeltests(Modeltests):
    """ Model tests. """

    def test_elections_repr(self):
        """ Test the __repr__ function of Elections. """
        create_elections(self.session)
        create_candidates(self.session)

        election = nuancierlib.get_election(self.session, 1)
        if six.PY2:
            self.assertEqual(
                election.__repr__(),
                "Elections(id:1, name:u'Wallpaper F19', year:2013)"
            )
        else:
            self.assertEqual(
                election.__repr__(),
                "Elections(id:1, name:'Wallpaper F19', year:2013)"
            )

    def test_candidates_repr(self):
        """ Test the __repr__ function of Candidates. """
        create_elections(self.session)
        create_candidates(self.session)

        candidate = nuancierlib.get_candidate(self.session, 1)
        if six.PY2:
            self.assertTrue(
                candidate.__repr__().startswith(
                    "Candidates(file:u'ok.JPG', "
                    "name:u'Image ok', "
                    "election_id:1, "
                )
            )
        else:
            self.assertTrue(
                candidate.__repr__().startswith(
                    "Candidates(file:'ok.JPG', "
                    "name:'Image ok', "
                    "election_id:1, "
                )
            )

    def test_votes_repr(self):
        """ Test the __repr__ function of Votes. """
        create_elections(self.session)
        create_candidates(self.session)
        create_votes(self.session)

        votes = nuancierlib.get_votes_user(self.session, 1, 'pingou')
        if six.PY2:
            self.assertTrue(
                votes[0].__repr__().startswith(
                    "Votes(name:u'pingou', candidate_id:1, created:"
                )
            )
        else:
            self.assertTrue(
                votes[0].__repr__().startswith(
                    "Votes(name:'pingou', candidate_id:1, created:"
                )
            )

    def test_elections_api_repr(self):
        """ Test the api_repr function of Elections. """
        create_elections(self.session)
        create_candidates(self.session)

        election = nuancierlib.get_election(self.session, 1)
        self.assertEqual(
            election.api_repr(1),
            {
                'date_end': TODAY - timedelta(days=8),
                'date_start': TODAY - timedelta(days=10),
                'id': 1,
                'name': u'Wallpaper F19',
                'submission_date_start': TODAY - timedelta(days=15),
                'year': 2013
            }
        )

    def test_candidates_api_repr(self):
        """ Test the api_repr function of Elections. """
        create_elections(self.session)
        create_candidates(self.session)

        candidate = nuancierlib.get_candidate(self.session, 1)
        self.assertEqual(
            candidate.api_repr(1),
            {
                'author': u'pingou',
                'license': u'CC-BY-SA',
                'name': u'Image ok',
                'original_url': None,
                'submitter': u'pingou',
            }
        )

    def test_election_open(self):
        """ Test the election_open property of Elections. """
        create_elections(self.session)

        election = nuancierlib.get_election(self.session, 1)
        self.assertEqual(election.election_open, False)

        election = nuancierlib.get_election(self.session, 2)
        self.assertEqual(election.election_open, True)

        election = nuancierlib.get_election(self.session, 3)
        self.assertEqual(election.election_open, False)

    def test_election_public(self):
        """ Test the election_public property of Elections. """
        create_elections(self.session)

        election = nuancierlib.get_election(self.session, 1)
        self.assertEqual(election.election_public, True)

        election = nuancierlib.get_election(self.session, 2)
        self.assertEqual(election.election_public, False)

        election = nuancierlib.get_election(self.session, 3)
        self.assertEqual(election.election_public, False)

    def test_submission_open_today(self):
        """ Test the submission_open property for today. """
        today = datetime.utcnow().date()
        election = model.Elections(
            election_name='Wallpaper F19',
            election_folder='F19',
            election_year='2013',
            election_n_choice=2,
            submission_date_start=today,
            election_date_start=today + timedelta(days=2),
            election_date_end=today + timedelta(days=4),
        )
        self.session.add(election)
        self.session.commit()

        election = nuancierlib.get_election(self.session, 1)
        self.assertEqual(election.submission_open, True)
        self.assertEqual(election.election_open, False)
        self.assertEqual(election.election_public, False)

    def test_election_open_today(self):
        """ Test the election_open property for today. """
        today = datetime.utcnow().date()
        election = model.Elections(
            election_name='Wallpaper F19',
            election_folder='F19',
            election_year='2013',
            election_n_choice=2,
            submission_date_start=today - timedelta(days=2),
            election_date_start=today,
            election_date_end=today + timedelta(days=2),
        )
        self.session.add(election)
        self.session.commit()

        election = nuancierlib.get_election(self.session, 1)
        self.assertEqual(election.submission_open, False)
        self.assertEqual(election.election_open, True)
        self.assertEqual(election.election_public, False)

    def test_election_public_today(self):
        """ Test the election_public property for today. """
        today = datetime.utcnow().date()
        election = model.Elections(
            election_name='Wallpaper F19',
            election_folder='F19',
            election_year='2013',
            election_n_choice=2,
            submission_date_start=today - timedelta(days=4),
            election_date_start=today - timedelta(days=2),
            election_date_end=today,
        )
        self.session.add(election)
        self.session.commit()

        election = nuancierlib.get_election(self.session, 1)
        self.assertEqual(election.submission_open, False)
        self.assertEqual(election.election_open, False)
        self.assertEqual(election.election_public, True)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(NuancierModeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
