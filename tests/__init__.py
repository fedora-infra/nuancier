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
nuancier tests.
'''
from __future__ import print_function

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import shutil
import sys
import os

from datetime import datetime
from datetime import date
from datetime import timedelta

from contextlib import contextmanager
from flask import appcontext_pushed, g

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from nuancier.lib import model

DB_PATH = 'sqlite:///:memory:'
PICTURE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pictures')
CACHE_FOLDER = os.path.join(os.path.dirname(__file__), 'cache')
TODAY = datetime.utcnow().date()
FAITOUT_URL = 'http://faitout.fedorainfracloud.org/'

if os.environ.get('BUILD_ID'):
    try:
        import requests
        req = requests.get('%s/new' % FAITOUT_URL)
        if req.status_code == 200:
            DB_PATH = req.text
            print('Using faitout at: %s' % DB_PATH)
    except:
        pass


@contextmanager
def user_set(APP, user):
    """ Set the provided user as fas_user in the provided application."""

    # Hack used to remove the before_request function set by
    # flask.ext.fas_openid.FAS which otherwise kills our effort to set a
    # flask.g.fas_user.
    APP.before_request_funcs[None] = []

    def handler(sender, **kwargs):
        g.fas_user = user

    with appcontext_pushed.connected_to(handler, APP):
        yield


class FakeFasUser(object):
    """ Fake FAS user used for the tests. """
    id = 100
    username = 'pingou'
    cla_done = True
    groups = ['packager', 'cla_done']
    email = 'pingou'


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        self.session = model.create_tables(DB_PATH, debug=False)

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        if os.path.exists(CACHE_FOLDER):
            if os.path.isdir(CACHE_FOLDER):
                shutil.rmtree(CACHE_FOLDER)
            elif os.path.isfile(CACHE_FOLDER):
                os.unlink(CACHE_FOLDER)
            else:
                print('Check %s, it cannot be removed' % CACHE_FOLDER,
                      file=sys.stderr)

        self.session.rollback()

        ## Empty the database if it's not a sqlite
        if self.session.bind.driver != 'pysqlite':
            self.session.execute('DROP TABLE "Votes" CASCADE;')
            self.session.execute('DROP TABLE "Candidates" CASCADE;')
            self.session.execute('DROP TABLE "Elections" CASCADE;')
            self.session.commit()


def create_elections(session):
    """ Create some basic elections for testing. """
    # Election in the past, closed and results opened
    election = model.Elections(
        election_name='Wallpaper F19',
        election_folder='F19',
        election_year='2013',
        election_n_choice=2,
        election_date_start=TODAY - timedelta(days=10),
        election_date_end=TODAY - timedelta(days=8),
        submission_date_start=TODAY - timedelta(days=15),
        submission_date_end=TODAY - timedelta(days=13),
    )
    session.add(election)

    # Election currently opened for voting
    election = model.Elections(
        election_name='Wallpaper F20',
        election_folder='F20',
        election_year='2013',
        election_n_choice=2,
        submission_date_start=TODAY - timedelta(days=6),
        submission_date_end=TODAY - timedelta(days=3),
        election_date_start=TODAY - timedelta(days=2),
        election_date_end=TODAY + timedelta(days=3),
        election_badge_link="http://badges.fp.org",
    )
    session.add(election)

    # Future election, open for submission
    election = model.Elections(
        election_name='Wallpaper F21',
        election_folder='F21',
        election_year='2014',
        election_n_choice=2,
        user_n_candidates=3,
        submission_date_start=TODAY - timedelta(days=2),
        submission_date_end=TODAY + timedelta(days=1),
        election_date_start=TODAY + timedelta(days=3),
        election_date_end=TODAY + timedelta(days=6),
    )
    session.add(election)
    session.commit()


def create_candidates(session):
    """ Create some basic candidates for testing. """
    #id 1
    candidate = model.Candidates(
        candidate_file='ok.JPG',
        candidate_name='Image ok',
        candidate_author='pingou',
        candidate_license='CC-BY-SA',
        candidate_submitter='pingou',
        submitter_email='pingou@fp.o',
        election_id=1,
    )
    session.add(candidate)

    #id 2
    candidate = model.Candidates(
        candidate_file='narrow.JPG',
        candidate_name='Image too narrow',
        candidate_author='pingou',
        candidate_license='CC-BY-SA',
        candidate_submitter='pingou',
        submitter_email='pingou@fp.o',
        election_id=1,
    )
    session.add(candidate)

    #id 3
    candidate = model.Candidates(
        candidate_file='small.JPG',
        candidate_name='Image too small',
        candidate_author='pingou',
        candidate_license='CC-BY-SA',
        candidate_submitter='pingou',
        submitter_email='pingou@fp.o',
        election_id=2,
    )
    session.add(candidate)

    #id 4
    candidate = model.Candidates(
        candidate_file='small2.JPG',
        candidate_name='Image too small2',
        candidate_author='pingou',
        candidate_license='CC-BY-SA',
        candidate_submitter='pingou',
        submitter_email='pingou@fp.o',
        election_id=2,
    )
    session.add(candidate)

    #id 5
    candidate = model.Candidates(
        candidate_file='small3.JPG',
        candidate_name='Image too small3',
        candidate_author='pingou',
        candidate_license='CC-BY-SA',
        candidate_submitter='pingou',
        submitter_email='pingou@fp.o',
        election_id=2,
    )
    session.add(candidate)

    #id 6
    candidate = model.Candidates(
        candidate_file='small2.0.JPG',
        candidate_name='Image too small2.0',
        candidate_author='pingou',
        candidate_license='CC-BY-SA',
        candidate_submitter='pingou',
        submitter_email='pingou@fp.o',
        election_id=3,
    )
    session.add(candidate)

    #id 7
    candidate = model.Candidates(
        candidate_file='small2.1.JPG',
        candidate_name='Image too small2.1',
        candidate_author='pingou',
        candidate_license='CC-BY-SA',
        candidate_submitter='pingou',
        submitter_email='pingou@fp.o',
        election_id=3,
    )
    session.add(candidate)

    #id 8
    candidate = model.Candidates(
        candidate_file='small2.2.JPG',
        candidate_name='Image too small2.2',
        candidate_author='pingou',
        candidate_license='CC-BY-SA',
        candidate_submitter='pingou',
        submitter_email='pingou@fp.o',
        election_id=3,
    )
    session.add(candidate)

    #id 9
    candidate = model.Candidates(
        candidate_file='small2.3.JPG',
        candidate_name='Image too small2.3',
        candidate_author='pingou',
        candidate_license='CC-BY-SA',
        candidate_submitter='toshio',
        submitter_email='pingou@fp.o',
        election_id=3,
    )
    session.add(candidate)

    session.commit()


def approve_candidate(session):
    """ Approve some candidates for testing. """

    for ids in [1, 2, 3, 4, 5, 8]:
        candidate = model.Candidates.by_id(session, ids)
        candidate.approved = True

        session.add(candidate)

    session.commit()


def deny_candidate(session):
    """ Deny some candidates for testing. """

    for ids in [6, 7]:
        candidate = model.Candidates.by_id(session, ids)
        candidate.approved = False
        candidate.approved_motif = 'Denied'

        session.add(candidate)

    session.commit()


def create_votes(session):
    """ Add some votes to a some candidates. """

    vote = model.Votes(
        user_name='pingou',
        candidate_id=1,
    )
    session.add(vote)

    vote = model.Votes(
        user_name='ralph',
        candidate_id=1,
    )
    session.add(vote)

    vote = model.Votes(
        user_name='pingou',
        candidate_id=2,
    )
    session.add(vote)

    vote = model.Votes(
        user_name='toshio',
        candidate_id=1,
    )
    session.add(vote)

    vote = model.Votes(
        user_name='toshio',
        candidate_id=2,
    )
    session.add(vote)

    vote = model.Votes(
        user_name='pingou',
        candidate_id=3,
    )
    session.add(vote)

    vote = model.Votes(
        user_name='ralph',
        candidate_id=3,
    )
    session.add(vote)

    vote = model.Votes(
        user_name='ralph',
        candidate_id=4,
    )
    session.add(vote)

    session.commit()


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
