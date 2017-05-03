# -*- coding: utf-8 -*-
#
# Copyright © 2013-2017  Red Hat, Inc.
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
nuancier tests for the internal api lib.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os
from datetime import timedelta

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import nuancier.lib as nuancierlib
from nuancier.lib import model
from tests import (Modeltests, create_elections, create_candidates,
                   create_votes, CACHE_FOLDER, PICTURE_FOLDER, TODAY)


class NuancierLibtests(Modeltests):
    """ NuancierLib tests. """

    def test_get_candidates(self):
        """ Test the get_candidates function. """
        create_elections(self.session)
        create_candidates(self.session)

        candidates = nuancierlib.get_candidates(self.session, 1, False)
        self.assertEqual(2, len(candidates))
        self.assertEqual('Image too narrow', candidates[0].candidate_name)
        self.assertEqual('Image ok', candidates[1].candidate_name)

        candidates = nuancierlib.get_candidates(self.session, 1, True)
        self.assertEqual(0, len(candidates))

        candidates = nuancierlib.get_candidates(self.session, 3, False)
        self.assertEqual(4, len(candidates))
        self.assertEqual('Image too small2.0', candidates[0].candidate_name)
        self.assertEqual('Image too small2.1', candidates[1].candidate_name)
        self.assertEqual('Image too small2.2', candidates[2].candidate_name)
        self.assertEqual('Image too small2.3', candidates[3].candidate_name)

        candidates = nuancierlib.get_candidates(self.session, 2, True)
        self.assertEqual(0, len(candidates))

    def test_get_candidate(self):
        """ Test the get_candidate function. """
        create_elections(self.session)
        create_candidates(self.session)

        candidate = nuancierlib.get_candidate(self.session, 1)
        self.assertEqual('Image ok', candidate.candidate_name)

        candidate = nuancierlib.get_candidate(self.session, 10)
        self.assertEqual(None, candidate)

    def test_get_elections(self):
        """ Test the get_elections function. """
        create_elections(self.session)

        elections = nuancierlib.get_elections(self.session)
        self.assertEqual(3, len(elections))
        self.assertEqual('Wallpaper F21', elections[0].election_name)
        self.assertEqual('Wallpaper F20', elections[1].election_name)
        self.assertEqual('Wallpaper F19', elections[2].election_name)

    def test_get_election(self):
        """ Test the get_election function. """
        create_elections(self.session)

        election = nuancierlib.get_election(self.session, 3)
        self.assertEqual('Wallpaper F21', election.election_name)

    def test_get_elections_open(self):
        """ Test the get_elections_open function. """
        create_elections(self.session)

        elections = nuancierlib.get_elections_open(self.session)
        self.assertEqual(1, len(elections))
        self.assertEqual('Wallpaper F20', elections[0].election_name)

    def test_get_elections_public(self):
        """ Test the get_elections_public function. """
        create_elections(self.session)

        elections = nuancierlib.get_elections_public(self.session)
        self.assertEqual(1, len(elections))
        self.assertEqual('Wallpaper F19', elections[0].election_name)

    def test_get_elections_to_contribute(self):
        """ Test the get_elections_to_contribute function. """
        create_elections(self.session)

        elections = nuancierlib.get_elections_to_contribute(self.session)
        self.assertEqual(1, len(elections))
        self.assertEqual('Wallpaper F21', elections[0].election_name)

    def test_get_votes_user(self):
        """ Test the get_votes_user function. """
        create_elections(self.session)
        create_candidates(self.session)
        create_votes(self.session)

        votes = nuancierlib.get_votes_user(self.session, 1, 'pingou')
        self.assertEqual(2, len(votes))
        self.assertEqual(1, votes[0].candidate_id)
        self.assertEqual(2, votes[1].candidate_id)

    def test_get_results(self):
        """ Test the get_results function. """
        create_elections(self.session)
        create_candidates(self.session)
        create_votes(self.session)

        results = nuancierlib.get_results(self.session, 1)
        self.assertEqual(2, len(results))
        self.assertEqual('Image ok', results[0][0].candidate_name)  # candidate
        self.assertEqual(3, results[0][1])  # number of votes
        self.assertEqual('Image too narrow', results[1][0].candidate_name)
        self.assertEqual(2, results[1][1])

    def test_add_election(self):
        """ Test the add_election function. """
        self.assertRaises(
            nuancierlib.NuancierException,
            nuancierlib.add_election,
            session=self.session,
            election_name='Test',
            election_folder='test',
            election_year='2013',
            submission_date_start=TODAY - timedelta(days=1),
            submission_date_end=TODAY + timedelta(days=1),
            election_date_start=TODAY + timedelta(days=3),
            election_date_end=TODAY + timedelta(days=7),
            election_n_choice=2,
            user_n_candidates=5,
            election_badge_link='http://...',
        )

        nuancierlib.add_election(
            session=self.session,
            election_name='Test',
            election_folder='test',
            election_year='2013',
            submission_date_start=TODAY - timedelta(days=1),
            submission_date_end=TODAY + timedelta(days=1),
            election_date_start=TODAY + timedelta(days=3),
            election_date_end=TODAY + timedelta(days=7),
            election_n_choice=2,
            user_n_candidates=5,
            election_badge_link='http://...',
            user='pingou',
        )
        self.session.commit()

        elections = nuancierlib.get_elections(self.session)
        self.assertEqual(1, len(elections))
        self.assertEqual('Test', elections[0].election_name)
        self.assertEqual('test', elections[0].election_folder)
        self.assertEqual(2013, elections[0].election_year)
        self.assertEqual(
            TODAY + timedelta(days=3), elections[0].election_date_start)
        self.assertEqual(
            TODAY + timedelta(days=7), elections[0].election_date_end)
        self.assertEqual(
            TODAY - timedelta(days=1), elections[0].submission_date_start)
        self.assertEqual(
            TODAY + timedelta(days=1), elections[0].submission_date_end)
        self.assertEqual(False, elections[0].election_public)
        self.assertEqual(2, elections[0].election_n_choice)
        self.assertEqual('http://...', elections[0].election_badge_link)

    def test_add_candidate(self):
        """ Test the add_candidate function. """
        create_elections(self.session)

        self.assertRaises(
            nuancierlib.NuancierException,
            nuancierlib.add_candidate,
            session=self.session,
            candidate_file='test.png',
            candidate_name='test image',
            candidate_author='pingou',
            candidate_license='CC-BY-SA',
            candidate_submitter='pingou',
            submitter_email='pingou@fp.o',
            candidate_original_url=None,
            election_id=2,
        )

        nuancierlib.add_candidate(
            session=self.session,
            candidate_file='test.png',
            candidate_name='test image',
            candidate_author='pingou',
            candidate_license='CC-BY-SA',
            candidate_submitter='pingou',
            submitter_email='pingou@fp.o',
            candidate_original_url=None,
            election_id=2,
            user='pingou',
        )
        self.session.commit()

        candidates = nuancierlib.get_candidates(self.session, 2, False)
        self.assertEqual(1, len(candidates))
        self.assertEqual('test image', candidates[0].candidate_name)
        self.assertEqual('test.png', candidates[0].candidate_file)

        candidates = nuancierlib.get_candidates(self.session, 2, True)
        self.assertEqual(0, len(candidates))

        self.assertRaises(
            nuancierlib.NuancierException,
            nuancierlib.add_candidate,
            session=self.session,
            candidate_file='test.png',
            candidate_name='test image',
            candidate_author='pingou',
            candidate_license='CC-BY-SA',
            candidate_submitter='pingou',
            submitter_email='pingou@fp.o',
            candidate_original_url='http://example.org',
            election_id=2,
            user='pingou',
        )

    def test_add_vote(self):
        """ Test the add_vote function. """
        create_elections(self.session)
        create_candidates(self.session)

        nuancierlib.add_vote(
            session=self.session,
            candidate_id=2,
            username='pingou'
        )

        self.session.commit()

        votes = nuancierlib.get_votes_user(self.session, 1, 'pingou')
        self.assertEqual(1, len(votes))
        self.assertEqual(2, votes[0].candidate_id)

    def test_edit_election(self):
        """ Test the edit_election function. """
        create_elections(self.session)
        election = nuancierlib.get_election(self.session, 2)

        self.assertRaises(
            nuancierlib.NuancierException,
            nuancierlib.edit_election,
            session=self.session,
            election=election,
            election_name='elec name',
            election_folder='Test',
            election_year=2048,
            election_date_start=TODAY,
            election_date_end=TODAY + timedelta(days=2),
            submission_date_start=TODAY - timedelta(days=2),
            submission_date_end=TODAY - timedelta(days=1),
            election_n_choice=42,
            user_n_candidates=5,
            election_badge_link='http://badges.fp.o/1234',
        )

        new_election = nuancierlib.edit_election(
            self.session,
            election=election,
            election_name='elec name',
            election_folder='Test',
            election_year=2048,
            election_date_start=TODAY,
            election_date_end=TODAY + timedelta(days=2),
            submission_date_start=TODAY - timedelta(days=2),
            submission_date_end=TODAY - timedelta(days=1),
            election_n_choice=42,
            user_n_candidates=5,
            election_badge_link='http://badges.fp.o/1234',
            user='pingou',
        )

        self.assertEqual(new_election.election_name, 'elec name')
        self.assertEqual(new_election.election_folder, 'Test')
        self.assertEqual(new_election.election_year, 2048)
        self.assertEqual(new_election.election_date_start, TODAY)
        self.assertEqual(
            new_election.election_date_end, TODAY + timedelta(days=2))
        self.assertEqual(
            new_election.submission_date_start, TODAY - timedelta(days=2))
        self.assertEqual(
            new_election.submission_date_end, TODAY - timedelta(days=1))
        self.assertEqual(new_election.election_n_choice, 42)
        self.assertEqual(
            new_election.election_badge_link, 'http://badges.fp.o/1234')

    def test_generate_cache(self):
        """ Test the generate_cache function. """

        create_elections(self.session)
        create_candidates(self.session)
        election = nuancierlib.get_election(self.session, 2)

        self.assertFalse(os.path.exists(CACHE_FOLDER))

        nuancierlib.generate_cache(
            session=self.session,
            election=election,
            picture_folder=PICTURE_FOLDER,
            cache_folder=CACHE_FOLDER,
            size=(128, 128)
        )

        self.assertTrue(os.path.exists(CACHE_FOLDER))

    def test_generate_cache_no_picture_folder(self):
        """ Test the generate_cache function. """

        create_elections(self.session)
        election = nuancierlib.get_election(self.session, 2)

        self.assertRaises(
            nuancierlib.NuancierException,
            nuancierlib.generate_cache,
            session=self.session,
            election=election,
            picture_folder='none',
            cache_folder=CACHE_FOLDER,
            size=(128, 128)
        )

    def test_generate_cache_cache_folder_is_file(self):
        """ Test the generate_cache function. """

        create_elections(self.session)
        election = nuancierlib.get_election(self.session, 2)

        stream = open(CACHE_FOLDER, 'w')
        stream.write('test')
        stream.close()

        self.assertRaises(
            nuancierlib.NuancierException,
            nuancierlib.generate_cache,
            session=self.session,
            election=election,
            picture_folder=PICTURE_FOLDER,
            cache_folder=CACHE_FOLDER,
            size=(128, 128)
        )

    def test_generate_cache_cache_folder_is_file2(self):
        """ Test the generate_cache function. """

        create_elections(self.session)
        election = nuancierlib.get_election(self.session, 2)

        os.mkdir(CACHE_FOLDER)
        cache_folder = os.path.join(CACHE_FOLDER, election.election_folder)

        stream = open(cache_folder, 'w')
        stream.write('test')
        stream.close()

        self.assertRaises(
            nuancierlib.NuancierException,
            nuancierlib.generate_cache,
            session=self.session,
            election=election,
            picture_folder=PICTURE_FOLDER,
            cache_folder=CACHE_FOLDER,
            size=(128, 128)
        )

    def test_get_stats(self):
        """ Test the get_stats function. """
        create_elections(self.session)
        create_candidates(self.session)
        create_votes(self.session)

        stats = nuancierlib.get_stats(self.session, 1)
        self.assertEqual(5, stats['votes'])
        self.assertEqual(3, stats['voters'])
        self.assertEqual([[1, 1], [2, 2]], stats['data'])


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(NuancierLibtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
