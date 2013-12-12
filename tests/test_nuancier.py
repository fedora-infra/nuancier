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
nuancier tests for the internal api lib.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import shutil
import sys
import os
from datetime import timedelta

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import nuancier
import nuancier.lib as nuancierlib
from nuancier.lib import model
from tests import (Modeltests, create_elections, create_candidates,
                   create_votes, FakeFasUser, user_set, approve_candidate,
                   CACHE_FOLDER, PICTURE_FOLDER, TODAY)


FILE_OK = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'pictures',
    'F20',
    'ok.JPG'
)
FILE_NOTOK = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'pictures',
    'F20',
    'small.JPG'
)
FILE_NOTOK2 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'pictures',
    'F20',
    'narrow.JPG'
)
FILE_NOTOK3 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'pictures',
    'F20',
    '__init__.JPG'
)
FILE_NOTOK4 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'pictures',
    'F20',
    'small.txt'
)


class Nuanciertests(Modeltests):
    """ Nuancier tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(Nuanciertests, self).setUp()

        nuancier.APP.config['TESTING'] = True
        nuancier.SESSION = self.session
        nuancier.APP.config['PICTURE_FOLDER'] = PICTURE_FOLDER
        nuancier.APP.config['CACHE_FOLDER'] = CACHE_FOLDER
        self.app = nuancier.APP.test_client()

    def test_is_nuancier_admin(self):
        """ Test the is_nuancier_admin function. """

        output = nuancier.is_nuancier_admin(None)
        self.assertFalse(output)

        user = FakeFasUser()
        user.groups = ['packager', 'cla_done']

        output = nuancier.is_nuancier_admin(user)
        self.assertFalse(output)

        user.groups = []

        output = nuancier.is_nuancier_admin(user)
        self.assertFalse(output)

        user.groups.append('sysadmin-main')

        output = nuancier.is_nuancier_admin(user)
        self.assertTrue(output)

    def test_login(self):
        """ Test the login function. """
        output = self.app.get('/login')
        self.assertEqual(output.status_code, 301)

    def test_logout(self):
        """ Test the logout function. """
        output = self.app.get('/logout')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/logout/')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/logout/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Nuancier-lite</h1>' in output.data)

        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/logout/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer logged-in</li>'
                in output.data)
            self.assertTrue('<h1>Nuancier-lite</h1>' in output.data)

    def test_base_picture(self):
        """ Test the base_picture function. """

        output = self.app.get('/pictures/F20/ok.JPG')
        self.assertEqual(output.status_code, 200)

    def test_base_cache(self):
        """ Test the base_cache function. """

        output = self.app.get('/cache/F20/ok.JPG')
        # cache hasn't been generated
        self.assertEqual(output.status_code, 404)

    def test_index(self):
        """ Test the index function. """

        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Nuancier-lite</h1>' in output.data)
        self.assertTrue('Nuancier-lite is a simple voting application'
                        in output.data)
        self.assertTrue('<p>No elections are opened to vote for the moment.'
                        '</p>' in output.data)
        self.assertTrue('<p>No elections are opened for contributions for '
                        'the moment.</p>' in output.data)

        create_elections(self.session)

        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Nuancier-lite</h1>' in output.data)
        self.assertTrue('Nuancier-lite is a simple voting application'
                        in output.data)
        self.assertTrue('href="/election/2/"' in output.data)
        self.assertTrue('Wallpaper F20 - 2013' in output.data)

        self.assertTrue('href="/election/3/"' in output.data)
        self.assertTrue('Wallpaper F21 - 2014' in output.data)

    def test_contribute_index(self):
        """ Test the contribute_index function. """

        output = self.app.get('/contribute')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/contribute/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Contribute a supplemental wallpaper</h1>'
                        in output.data)
        self.assertTrue('Contributor must have signed the'
                        in output.data)

    def test_contribute(self):
        """ Test the contribute function. """

        # Fails login required
        output = self.app.get('/contribute/1')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/contribute/1')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">No election found</li>'
                            in output.data)

        create_elections(self.session)
        upload_path = os.path.join(PICTURE_FOLDER, 'F19')

        with user_set(nuancier.APP, user):
            output = self.app.get('/contribute/1')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Contribute a supplemental wallpaper</h1>'
                            in output.data)
            self.assertTrue('You are going to submit a new supplemental'
                            in output.data)
            self.assertTrue('Election : Wallpaper F19 -- 2013'
                            in output.data)
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'candidate_name': 'name',
                'candidate_author': 'pingou',
                'candidate_file': None,
                'candidate_license': 'CC-BY-SA',
                'csrf_token': csrf_token,
            }

            self.assertFalse(os.path.exists(upload_path))

            # Wrong width
            with open(FILE_NOTOK) as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/1', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="message">The submitted candidate has a '
                    'width of 1280 pixels which is lower than the minimum '
                    '1600 pixels required</li>' in output.data
                )
                self.assertTrue('<h1>Contribute a supplemental wallpaper</h1>'
                                in output.data)

            self.assertFalse(os.path.exists(upload_path))

            # Wrong hight
            with open(FILE_NOTOK2) as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/1', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="message">The submitted candidate has a '
                    'height of 1166 pixels which is lower than the minimum '
                    '1200 pixels required</li>' in output.data
                )
                self.assertTrue('<h1>Contribute a supplemental wallpaper</h1>'
                                in output.data)

            self.assertFalse(os.path.exists(upload_path))

            # Is not an image
            with open(FILE_NOTOK3) as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/1', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="message">The submitted candidate could not '
                    'be opened as an Image</li>' in output.data
                )
                self.assertTrue('<h1>Contribute a supplemental wallpaper</h1>'
                                in output.data)

            self.assertFalse(os.path.exists(upload_path))

            # Wrong file extension
            with open(FILE_NOTOK4) as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/1', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="message">The submitted candidate has the '
                    'file extension "txt" which is not an allowed format'
                    in output.data
                )
                self.assertTrue('<h1>Contribute a supplemental wallpaper</h1>'
                                in output.data)

            self.assertFalse(os.path.exists(upload_path))

            # Right file, works as it should
            with open(FILE_OK) as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/1', data=data,
                                       follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="message">Thanks for your submission</li>'
                    in output.data
                )
                self.assertTrue('<h1>Nuancier-lite</h1>' in output.data)
                self.assertTrue(
                    'Nuancier-lite is a simple voting application'
                    in output.data)

            self.assertTrue(os.path.exists(upload_path))
            shutil.rmtree(upload_path)

            self.assertFalse(os.path.exists(upload_path))

            # Conflicting name
            with open(FILE_OK) as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/1', data=data,
                                       follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">A candidate with the name '
                    '"name" has already been submitted</li>'
                    in output.data)
                self.assertTrue('<h1>Contribute a supplemental wallpaper</h1>'
                                in output.data)

            self.assertFalse(os.path.exists(upload_path))

            # Conflicting file name
            with open(FILE_OK) as stream:
                data = {
                    'candidate_name': 'name2',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/1', data=data,
                                       follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">A candidate with the file name '
                    in output.data)
                self.assertTrue('<h1>Contribute a supplemental wallpaper</h1>'
                                in output.data)

            self.assertFalse(os.path.exists(upload_path))

    def test_elections_list(self):
        """ Test the elections_list function. """
        output = self.app.get('/elections')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/elections/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Elections</h1>' in output.data)
        self.assertTrue('Listed here are all the elections that are taking'
                        in output.data)

        create_elections(self.session)

        output = self.app.get('/elections/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Elections</h1>' in output.data)
        self.assertTrue('Listed here are all the elections that are taking'
                        in output.data)
        self.assertTrue('Wallpaper F21' in output.data)
        self.assertTrue('Wallpaper F19' in output.data)
        self.assertTrue('Wallpaper F20' in output.data)
        self.assertEqual(output.data.count('static/Approved.png'), 2)
        self.assertEqual(output.data.count('static/Denied.png'), 4)

    def test_election(self):
        """ Test the election function. """
        output = self.app.get('/election/1')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/election/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<li class="error">No election found</li>'
                        in output.data)

        create_elections(self.session)

        # Election exists but no candidates
        output = self.app.get('/election/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('h1>Election: Wallpaper F19 - 2013</h1>'
                        in output.data)
        self.assertTrue('Below are presented all the candidates of this'
                        in output.data)
        self.assertTrue('<p> No candidate have been registered for this '
                        'election (yet). </p>'
                        in output.data)

        create_candidates(self.session)
        approve_candidate(self.session)

        # Election exists and there are candidates
        output = self.app.get('/election/1/')
        print output.data
        self.assertEqual(output.status_code, 200)
        self.assertTrue('h1>Election: Wallpaper F19 - 2013</h1>'
                        in output.data)
        self.assertTrue('Below are presented all the candidates of this'
                        in output.data)
        self.assertTrue('Click on the picture to get a larger version'
                        in output.data)
        self.assertEqual(output.data.count("data-lightbox='Wallpaper F19"),
                         2)

        output = self.app.get('/election/3/')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/election/3/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<li class="error">This election is not open</li>'
                        in output.data)

        # Is open and redirects you to the voting page
        output = self.app.get('/election/2/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/election/2/')
            self.assertEqual(output.status_code, 302)
            self.assertTrue('target URL: <a href="/election/2/vote/">'
                            in output.data)

            output = self.app.get('/election/2/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Vote: Wallpaper F20 - 2013</h1>'
                            in output.data)
            self.assertTrue('var votelimit = 2 - 0;' in output.data)

        create_votes(self.session)

        with user_set(nuancier.APP, user):

            output = self.app.get('/election/2/')
            self.assertEqual(output.status_code, 302)
            self.assertTrue('target URL: <a href="/election/2/vote/">'
                            in output.data)

            output = self.app.get('/election/2/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Vote: Wallpaper F20 - 2013</h1>'
                            in output.data)
            self.assertTrue('var votelimit = 2 - 1;' in output.data)

        user.username = 'ralph'
        with user_set(nuancier.APP, user):

            output = self.app.get('/election/2/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('h1>Election: Wallpaper F20 - 2013</h1>'
                            in output.data)
            self.assertTrue('Below are presented all the candidates of this'
                            in output.data)
            self.assertTrue('Click on the picture to get a larger version'
                            in output.data)
            self.assertEqual(output.data.count("data-lightbox='Wallpaper F20"),
                             3)

    def test_vote(self):
        """ Test the vote function. """
        ## Login required
        output = self.app.get('/election/1/vote')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/election/1/vote/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        # Fails; not CLA + 1
        user.groups = []
        with user_set(nuancier.APP, user):
            output = self.app.get('/election/1/vote/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You must be in one more '
                            'group than the CLA</li>' in output.data)

        # Fails; CLA not signed
        user.groups = ['packager', 'cla_done']
        user.cla_done = False
        with user_set(nuancier.APP, user):
            output = self.app.get('/election/1/vote/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You must sign the CLA '
                            '(Contributor License Agreement to use nuancier'
                            '</li>' in output.data)

        # Works
        user.cla_done = True
        with user_set(nuancier.APP, user):
            output = self.app.get('/election/1/vote')
            self.assertEqual(output.status_code, 301)

            output = self.app.get('/election/1/vote/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">No election found</li>'
                            in output.data)

        create_elections(self.session)
        create_candidates(self.session)
        approve_candidate(self.session)

        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/election/1/vote/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/election/1/vote/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">This election is not open</li>'
                            in output.data)

            output = self.app.get('/election/2/vote/', follow_redirects=True)
            self.assertTrue('<h1>Vote: Wallpaper F20 - 2013</h1>'
                            in output.data)
            self.assertTrue('var votelimit = 2 - 0;' in output.data)

        create_votes(self.session)

        user.username = 'ralph'
        with user_set(nuancier.APP, user):
            output = self.app.get('/election/2/vote/', follow_redirects=True)
            self.assertTrue('<h1>Election: Wallpaper F20 - 2013</h1>'
                            in output.data)
            self.assertTrue('<li class="error">You have cast the maximal '
                            'number of votes allowed for this election.</li>'
                            in output.data)

    def test_process_vote(self):
        """ Test the process_vote function. """
        ## Login required
        output = self.app.post('/election/1/voted')
        self.assertEqual(output.status_code, 301)

        output = self.app.post('/election/1/voted/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        # Fails; not CLA + 1
        user.groups = []
        with user_set(nuancier.APP, user):
            output = self.app.post('/election/1/voted/',
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You must be in one more '
                            'group than the CLA</li>' in output.data)

        # Fails; CLA not signed
        user.groups = ['packager', 'cla_done']
        user.cla_done = False
        with user_set(nuancier.APP, user):
            output = self.app.post('/election/1/voted/',
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You must sign the CLA '
                            '(Contributor License Agreement to use nuancier'
                            '</li>' in output.data)

        # Fails: no elections
        user.cla_done = True
        with user_set(nuancier.APP, user):
            # Edit the first election
            output = self.app.get('/election/1/vote/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">No election found</li>'
                            in output.data)

        create_elections(self.session)
        create_candidates(self.session)
        approve_candidate(self.session)

        # Works
        with user_set(nuancier.APP, user):
            # No CSRF
            output = self.app.post('/election/1/voted/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">Wrong input submitted</li>'
                            in output.data)

            output = self.app.get('/election/2/vote/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Vote: Wallpaper F20 - 2013</h1>'
                            in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {'csrf_token': csrf_token}

            # Election does not exists
            output = self.app.post('/election/10/voted/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">No election found</li>'
                            in output.data)

            # Election closed
            output = self.app.post('/election/1/voted/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">This election is not open'
                            '</li>' in output.data)

            # Missing data
            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Vote: Wallpaper F20 - 2013</h1>'
                            in output.data)
            self.assertTrue('<li class="error">You did not select any '
                            'candidate to vote for.</li>' in output.data)

            # Incorrect selection data
            data = {
                'selection': 1,
                'csrf_token': csrf_token
            }

            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Vote: Wallpaper F20 - 2013</h1>'
                            in output.data)
            self.assertTrue('<li class="error">The selection you have made '
                            'contains element which are not part of this '
                            'election, please be careful.</li>' in output.data)

            # Selection too large
            data = {
                'selection': [3, 4, 5],
                'csrf_token': csrf_token
            }

            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Vote: Wallpaper F20 - 2013</h1>'
                            in output.data)
            self.assertTrue('<li class="error">You selected 3 wallpapers '
                            'while you are only allowed to select 2</li>'
                            in output.data)

            # Works
            data = {
                'selection': [3, 4],
                'csrf_token': csrf_token
            }

            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Elections</h1>' in output.data)
            self.assertTrue('<li class="message">Your vote has been '
                            'recorded, thank you for voting on Wallpaper'
                            ' F20 2013</li>' in output.data)

            # Already voted
            data = {
                'selection': [3, 4],
                'csrf_token': csrf_token
            }

            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Election: Wallpaper F20 - 2013</h1>'
                            in output.data)
            self.assertTrue('<li class="error">You have cast the maximal '
                            'number of votes allowed for this election.</li>'
                            in output.data)

    def test_results_list(self):
        """ Test the results_list function. """
        output = self.app.get('/results')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/results/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Election results</h1>' in output.data)
        self.assertTrue('<p class="error">No elections have their result '
                        'public (yet).</p>' in output.data)

        create_elections(self.session)
        create_candidates(self.session)
        approve_candidate(self.session)
        create_votes(self.session)

        output = self.app.get('/results/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Election results</h1>' in output.data)
        self.assertTrue('Wallpaper F19 - 2013' in output.data)
        self.assertEqual(output.data.count('href="/results/'), 2)

    def test_results(self):
        """ Test the results function. """
        output = self.app.get('/results/1')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/results/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<li class="error">No election found</li>'
                        in output.data)

        create_elections(self.session)
        create_candidates(self.session)
        approve_candidate(self.session)
        create_votes(self.session)

        output = self.app.get('/results/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Election results: Wallpaper F19 - 2013</h1>'
                        in output.data)
        self.assertTrue('Here below are presented the results of the elect'
                        in output.data)

        output = self.app.get('/results/2/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<li class="error">The results this election are '
                        'not public yet</li>' in output.data)
        self.assertTrue('<h1>Election results</h1>' in output.data)

        output = self.app.get('/results/3/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<li class="error">The results this election are '
                        'not public yet</li>' in output.data)
        self.assertTrue('<h1>Election results</h1>' in output.data)

    def test_admin_index(self):
        """ Test the admin_index function. """
        output = self.app.get('/admin')
        self.assertEqual(output.status_code, 301)

        # Redirects to the OpenID page
        output = self.app.get('/admin/')
        self.assertEqual(output.status_code, 302)

        # Fails - not an admin
        user = FakeFasUser()
        user.groups = ['packager', 'cla_done']
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You are not an administrator'
                            ' of nuancier-lite</li>' in output.data)

        # Fails - did not sign the CLA
        user.cla_done = False
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You must sign the CLA '
                            '(Contributor License Agreement to use nuancier'
                            '</li>' in output.data)
            self.assertTrue('<h1>Nuancier-lite</h1>' in output.data)
            self.assertTrue('Nuancier-lite is a simple voting application'
                            in output.data)

        # Fails - is not CLA + 1
        user.cla_done = True
        user.groups = []
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You must be in one more '
                            'group than the CLA</li>' in output.data)
            self.assertTrue('<h1>Nuancier-lite</h1>' in output.data)
            self.assertTrue('Nuancier-lite is a simple voting application'
                            in output.data)

        # Success
        user.groups = ['packager', 'cla_done', 'sysadmin-main']
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Nuancier-lite Admin -- Version'
                            in output.data)

            create_elections(self.session)
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Nuancier-lite Admin -- Version'
                            in output.data)
            self.assertTrue('Wallpaper F19' in output.data)
            self.assertTrue('Wallpaper F20' in output.data)
            self.assertTrue('Wallpaper F21' in output.data)
            self.assertEqual(
                output.data.count('src="/static/Denied.png"'), 4)
            self.assertEqual(
                output.data.count('src="/static/Approved.png"'), 2)

        user.groups = ['packager', 'cla_done']

    def test_admin_edit(self):
        """ Test the admin_edit function. """
        output = self.app.get('/admin/1/edit')
        self.assertEqual(output.status_code, 301)

        # Redirects to the OpenID page
        output = self.app.get('/admin/1/edit/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/1/edit/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/1/edit/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You are not an administrator'
                            ' of nuancier-lite</li>' in output.data)

        user.groups.append('sysadmin-main')
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/1/edit/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">No election found</li>'
                            in output.data)

        create_elections(self.session)

        with user_set(nuancier.APP, user):
            # Check the admin page before the edit
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Nuancier-lite Admin -- Version'
                            in output.data)
            self.assertFalse('election1' in output.data)
            self.assertTrue('Wallpaper F19' in output.data)
            self.assertTrue('Wallpaper F20' in output.data)
            self.assertTrue('Wallpaper F21' in output.data)

            # Edit the first election
            output = self.app.get('/admin/1/edit/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Edit election: Wallpaper F19 -- 2013</h1>'
                            in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'election_name': 'election1',
                'election_folder': 'pingou',
                'election_year': '2014',
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/1/edit/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            # Redirected to the admin index page, after the edit
            self.assertTrue('<h1>Nuancier-lite Admin -- Version'
                            in output.data)
            self.assertFalse('Wallpaper F19' in output.data)
            self.assertTrue('election1' in output.data)
            self.assertTrue('Wallpaper F20' in output.data)
            self.assertTrue('Wallpaper F21' in output.data)
            self.assertEqual(output.data.count('2014'), 2)

            # Edit failed: Name exists
            data = {
                'election_name': 'Wallpaper F20',
                'election_folder': 'pingou',
                'election_year': '2013',
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/1/edit/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(' <li class="error">Could not edit this election'
                            ', is this name or folder already used?</li>'
                            in output.data)
            self.assertTrue('<h1>Edit election: election1 -- 2014</h1>'
                            in output.data)

            # Edit failed: folder exists
            data = {
                'election_name': 'election1',
                'election_folder': 'F20',
                'election_year': '2013',
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/1/edit/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(' <li class="error">Could not edit this election'
                            ', is this name or folder already used?</li>'
                            in output.data)
            self.assertTrue('<h1>Edit election: election1 -- 2014</h1>'
                            in output.data)

        user.groups = ['packager', 'cla_done']

    def test_admin_new(self):
        """ Test the admin_new function. """
        output = self.app.get('/admin/new')
        self.assertEqual(output.status_code, 301)

        # Redirects to the OpenID page
        output = self.app.get('/admin/new/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        user.groups = ['packager', 'cla_done']
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/new/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/new/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You are not an administrator'
                            ' of nuancier-lite</li>' in output.data)

        user.groups.append('sysadmin-main')
        create_elections(self.session)

        with user_set(nuancier.APP, user):
            # Check the admin page before the edit
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Nuancier-lite Admin -- Version'
                            in output.data)
            self.assertFalse('election1' in output.data)
            self.assertFalse('election2' in output.data)
            self.assertTrue('Wallpaper F19' in output.data)
            self.assertTrue('Wallpaper F20' in output.data)
            self.assertTrue('Wallpaper F21' in output.data)
            self.assertEqual(output.data.count('2014'), 1)
            self.assertEqual(output.data.count('2013'), 9)

            # Add the new election
            output = self.app.get('/admin/new/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>New election</h1>' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # election_n_choice should be a number
            data = {
                'election_name': 'election1',
                'election_folder': 'pingou',
                'election_year': '2014',
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 'abc',
                'generate_cache': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>New election</h1>' in output.data)
            self.assertTrue('<td class="errors">Field must contain a '
                            'number</td>' in output.data)

            data = {
                'election_name': 'election1',
                'election_folder': 'pingou',
                'election_year': '2014',
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'generate_cache': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            # Redirected to the admin index page, after the creation
            self.assertTrue('<h1>Nuancier-lite Admin -- Version'
                            in output.data)
            self.assertTrue('<li class="error">The folder said to contain '
                            'the pictures of this election'
                            in output.data)
            self.assertTrue('<li class="message">Election created</li>'
                            in output.data)
            self.assertTrue('election1' in output.data)
            self.assertFalse('election2' in output.data)
            self.assertTrue('Wallpaper F19' in output.data)
            self.assertTrue('Wallpaper F20' in output.data)
            self.assertTrue('Wallpaper F21' in output.data)
            self.assertEqual(output.data.count('2014'), 2)
            self.assertEqual(output.data.count('2013'), 11)

            data = {
                'election_name': 'election2',
                'election_folder': 'pingou2',
                'election_year': '2014',
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            # Redirected to the admin index page, after the creation
            self.assertTrue('<h1>Nuancier-lite Admin -- Version'
                            in output.data)
            self.assertTrue('<li class="message">Election created</li>'
                            in output.data)
            self.assertFalse('<li class="error">The folder said to contain '
                             'the pictures of this election'
                             in output.data)
            self.assertTrue('election1' in output.data)
            self.assertTrue('election2' in output.data)
            self.assertTrue('Wallpaper F19' in output.data)
            self.assertTrue('Wallpaper F20' in output.data)
            self.assertTrue('Wallpaper F21' in output.data)
            self.assertEqual(output.data.count('2014'), 3)
            self.assertEqual(output.data.count('2013'), 13)

            # Edit failed: Name exists
            data = {
                'election_name': 'Wallpaper F20',
                'election_folder': 'pingou',
                'election_year': '2013',
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(' <li class="error">Could not add this election'
                            ', is this name or folder already used?</li>'
                            in output.data)
            self.assertTrue('<h1>New election</h1>' in output.data)

            # Edit failed: folder exists
            data = {
                'election_name': 'election1',
                'election_folder': 'F20',
                'election_year': '2013',
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(' <li class="error">Could not add this election'
                            ', is this name or folder already used?</li>'
                            in output.data)
            self.assertTrue('<h1>New election</h1>' in output.data)

        user.groups = ['packager', 'cla_done']

    def test_admin_review(self):
        """ Test the admin_review function. """
        output = self.app.get('/admin/review/1')
        self.assertEqual(output.status_code, 301)

        # Redirects to the OpenID page
        output = self.app.get('/admin/review/1/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        user.groups = ['packager', 'cla_done']
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/review/1/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/review/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You are not an administrator'
                            ' of nuancier-lite</li>' in output.data)

        user.groups.append('sysadmin-main')

        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/review/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">No election found</li>'
                            in output.data)

        create_elections(self.session)

        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/review/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">The results of this election'
                            ' are already public, this election can no '
                            'longer be changed</li>' in output.data)

            output = self.app.get('/admin/review/2/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">This election is already open'
                            ' to public votes and can no longer be changed'
                            '</li>' in output.data)

            output = self.app.get('/admin/review/3/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<p class="error">No candidates found for this '
                            'election.</p>' in output.data)

            create_candidates(self.session)

            output = self.app.get('/admin/review/3/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Review election: Wallpaper F21 - 2014</h1>'
                            in output.data)
            self.assertEqual(output.data.count('name="candidates_id"'), 2)

        user.groups = ['packager', 'cla_done']

    def test_admin_process_review(self):
        """ Test the admin_process_review function. """
        output = self.app.post('/admin/review/1/process')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        user.groups = ['packager', 'cla_done']
        with user_set(nuancier.APP, user):
            output = self.app.post('/admin/review/1/process')
            self.assertEqual(output.status_code, 302)

            output = self.app.post('/admin/review/1/process',
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You are not an administrator'
                            ' of nuancier-lite</li>' in output.data)

        user.groups.append('sysadmin-main')
        create_elections(self.session)
        create_candidates(self.session)

        with user_set(nuancier.APP, user):
            output = self.app.post('/admin/review/1/process',
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">Wrong input submitted</li>'
                            in output.data)

            output = self.app.get('/admin/review/3/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Review election: Wallpaper F21 - 2014</h1>'
                            in output.data)
            self.assertEqual(output.data.count('name="candidates_id"'), 2)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {'csrf_token': csrf_token}

            output = self.app.post('/admin/review/10/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">No election found</li>'
                            in output.data)

        with user_set(nuancier.APP, user):
            # Check the review page before changes
            output = self.app.get('/admin/review/3/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Review election: Wallpaper F21 - 2014</h1>'
                            in output.data)
            self.assertEqual(output.data.count('="/static/Denied.png"'), 2)
            self.assertEqual(output.data.count('="/static/Approved.png"'), 0)

            # Fails: results public
            output = self.app.post('/admin/review/1/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">The results of this election'
                            ' are already public, this election can no '
                            'longer be changed</li>' in output.data)

            # Fails: vote open
            output = self.app.post('/admin/review/2/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">This election is already open'
                            ' to public votes and can no longer be changed'
                            '</li>' in output.data)

            # Fails: no input submitted (beside the csrf_token)
            output = self.app.post('/admin/review/3/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">Only the actions "Approved" '
                            'or "Denied" are accepted</li>' in output.data)

            # Fails: candidate is part of election 1 not 3
            data = {
                'action': 'Approved',
                'motifs': '',
                'candidates_id': '2',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/review/3/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(' <li class="error">One of the candidate '
                            'submitted was not candidate in this election'
                            '</li>' in output.data)

            # Fails: candidate does not exists
            data = {
                'action': 'Approved',
                'motifs': '',
                'candidates_id': '10',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/review/3/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(' <li class="error">One of the candidate '
                            'submitted was not candidate in this election'
                            '</li>' in output.data)

            # Check again the review page - no changes
            output = self.app.get('/admin/review/3/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Review election: Wallpaper F21 - 2014</h1>'
                            in output.data)
            self.assertEqual(output.data.count('="/static/Denied.png"'), 2)
            self.assertEqual(output.data.count('="/static/Approved.png"'), 0)

            # Valid submission
            data = {
                'action': 'Approved',
                'motifs': '',
                'candidates_id': '6',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/review/3/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="message">Candidate(s) updated</li>'
                            in output.data)

            # Check again the review page for changes
            output = self.app.get('/admin/review/3/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Review election: Wallpaper F21 - 2014</h1>'
                            in output.data)
            self.assertEqual(output.data.count('="/static/Denied.png"'), 1)
            self.assertEqual(output.data.count('="/static/Approved.png"'), 1)

            # Fails: no motif to reject candidate
            data = {
                'action': 'Denied',
                'motifs': '',
                'candidates_id': '6',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/review/3/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">You must provide a motif to '
                            'deny a candidate</li>' in output.data)

            # Fails: no motif to reject candidate
            data = {
                'action': 'Denied',
                'candidates_id': '6',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/review/3/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">You must provide a motif to '
                            'deny a candidate</li>' in output.data)

            # Valid submission
            data = {
                'action': 'Denied',
                'motifs': 'Candidate has a Fedora logo',
                'candidates_id': '6',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/review/3/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="message">Candidate(s) updated</li>'
                            in output.data)

            # Check again the review page for changes
            output = self.app.get('/admin/review/3/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Review election: Wallpaper F21 - 2014</h1>'
                            in output.data)
            self.assertEqual(output.data.count('="/static/Denied.png"'), 2)
            self.assertEqual(output.data.count('="/static/Approved.png"'), 0)

    def test_admin_cache(self):
        """ Test the admin_cache function. """

        self.assertFalse(os.path.exists(CACHE_FOLDER))

        # Redirects to the OpenID page
        output = self.app.get('/admin/cache/2')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        user.groups = ['packager', 'cla_done']
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/cache/2')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/cache/2', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="errors">You are not an administrator'
                            ' of nuancier-lite</li>' in output.data)

        user.groups.append('sysadmin-main')

        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/cache/2', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">No election found</li>'
                            in output.data)

        create_elections(self.session)

        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/cache/2', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="message">Cache regenerated for '
                            'election Wallpaper F20</li>' in output.data)

            output = self.app.get('/admin/cache/1', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">The folder said to contain '
                            'the pictures of this election' in output.data)

        self.assertTrue(os.path.exists(CACHE_FOLDER))

    def test_stats(self):
        """ Test the stats function. """
        output = self.app.get('/stats/2/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<li class="error">No election found</li>'
                        in output.data)

        create_elections(self.session)

        output = self.app.get('/stats/2/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Election results</h1>' in output.data)
        self.assertTrue('<li class="error">The results this election are '
                        'not public yet</li>' in output.data)

        create_candidates(self.session)
        create_votes(self.session)

        output = self.app.get('/stats/1/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<h1>Election statistics</h1>' in output.data)
        self.assertTrue('<div id="placeholder" class="demo-placeholder">'
                        '</div>' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Nuanciertests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
