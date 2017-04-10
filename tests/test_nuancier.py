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
                   deny_candidate, CACHE_FOLDER, PICTURE_FOLDER, TODAY)


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
        nuancier.APP.logger.handlers = []
        nuancier.SESSION = self.session
        nuancier.admin.SESSION = self.session
        nuancier.ui.SESSION = self.session
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
        self.assertTrue(output.status_code in [301, 308])

    def test_logout(self):
        """ Test the logout function. """
        output = self.app.get('/logout')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/logout/')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/logout/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Nuancier</h1>' in output.data.decode('utf-8'))

        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/logout/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer logged-in</li>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<h1>Nuancier</h1>' in output.data.decode('utf-8'))

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
        self.assertTrue(
            '<h1>Nuancier</h1>' in output.data.decode('utf-8'))
        self.assertTrue(
            'Nuancier is a simple voting application'
            in output.data.decode('utf-8'))
        self.assertTrue(
            '<p>No elections are currently open for voting.</p>'
            in output.data.decode('utf-8'))
        self.assertTrue(
            '<p>No elections are opened for contributions for the moment.'
            '</p>' in output.data.decode('utf-8'))

        create_elections(self.session)

        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Nuancier</h1>' in output.data.decode('utf-8'))
        self.assertTrue(
            'Nuancier is a simple voting application'
            in output.data.decode('utf-8'))
        self.assertTrue(
            'href="/election/2/"' in output.data.decode('utf-8'))
        self.assertTrue(
            'Wallpaper F20 - 2013' in output.data.decode('utf-8'))

    def test_contribute_index(self):
        """ Test the contribute_index function. """

        output = self.app.get('/contribute')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/contribute/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Contribute a supplemental wallpaper</h1>'
            in output.data.decode('utf-8'))
        self.assertTrue(
            'Contributor must have signed the'
            in output.data.decode('utf-8'))

    def test_contribute(self):
        """ Test the contribute function. """

        # Fails login required
        output = self.app.get('/contribute/1')
        self.assertEqual(output.status_code, 302)

        # Fails - No election in the DB
        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/contribute/1')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No election found</li>'
                in output.data.decode('utf-8'))

        create_elections(self.session)
        upload_path = os.path.join(PICTURE_FOLDER, 'F21')

        # Fails - Election closed for submission
        with user_set(nuancier.APP, user):
            output = self.app.get('/contribute/2', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="error">This election is not open for submission</'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<h1>Elections</h1>' in output.data.decode('utf-8'))

        # Fails - CLA not done
        user.cla_done = False
        with user_set(nuancier.APP, user):
            output = self.app.get('/contribute/3')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/contribute/3', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You must sign the CLA (Contributor '
                'License Agreement to use nuancier</li>'
                in output.data.decode('utf-8'))

        user.cla_done = True
        with user_set(nuancier.APP, user):
            output = self.app.get('/contribute/3')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Contribute a supplemental wallpaper</h1>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                'You are going to submit a new supplemental'
                in output.data.decode('utf-8'))
            self.assertTrue(
                'Election : Wallpaper F21 -- 2014'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"'
                in output.data.decode('utf-8'))

            csrf_token = output.data.decode('utf-8').split(
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
            with open(FILE_NOTOK, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/3', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">The submitted candidate has a '
                    'width of 1280 pixels which is lower than the minimum '
                    '1600 pixels required</li>'
                    in output.data.decode('utf-8')
                )
                self.assertTrue(
                    '<h1>Contribute a supplemental wallpaper</h1>'
                    in output.data.decode('utf-8'))

            self.assertFalse(os.path.exists(upload_path))

            # Wrong hight
            with open(FILE_NOTOK2, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/3', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">The submitted candidate has a '
                    'height of 1166 pixels which is lower than the minimum '
                    '1200 pixels required</li>'
                    in output.data.decode('utf-8')
                )
                self.assertTrue('<h1>Contribute a supplemental wallpaper</h1>'
                                in output.data.decode('utf-8'))

            self.assertFalse(os.path.exists(upload_path))

            # Is not an image
            with open(FILE_NOTOK3, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/3', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">The submitted candidate could not '
                    'be opened as an Image</li>'
                    in output.data.decode('utf-8')
                )
                self.assertTrue(
                    '<h1>Contribute a supplemental wallpaper</h1>'
                    in output.data.decode('utf-8'))

            self.assertFalse(os.path.exists(upload_path))

            # Wrong file extension
            with open(FILE_NOTOK4, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/3', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">The submitted candidate has the '
                    'file extension "txt" which is not an allowed format'
                    in output.data.decode('utf-8')
                )
                self.assertTrue(
                    '<h1>Contribute a supplemental wallpaper</h1>'
                    in output.data.decode('utf-8'))

            self.assertFalse(os.path.exists(upload_path))

            # Right file, works as it should
            with open(FILE_OK, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribute/3', data=data,
                                       follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="message">Thanks for your submission</li>'
                    in output.data.decode('utf-8')
                )
                self.assertTrue(
                    '<h1>Nuancier</h1>' in output.data.decode('utf-8'))
                self.assertTrue(
                    'Nuancier is a simple voting application'
                    in output.data.decode('utf-8'))

            self.assertTrue(os.path.exists(upload_path))
            shutil.rmtree(upload_path)

            self.assertFalse(os.path.exists(upload_path))

            # Conflicting name/title for the same filename
            with open(FILE_OK, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }
                output = self.app.post('/contribute/3', data=data,
                                       follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">A candidate with the filename '
                    '"pingou-' in output.data.decode('utf-8'))
                self.assertTrue(
                    '<h1>Contribute a supplemental wallpaper</h1>'
                    in output.data.decode('utf-8'))

            self.assertEqual(
                os.listdir(upload_path), [])
            self.assertTrue(os.path.exists(upload_path))
            shutil.rmtree(upload_path)

            self.assertFalse(os.path.exists(upload_path))

    def test_elections_list(self):
        """ Test the elections_list function. """
        output = self.app.get('/elections')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/elections/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Elections</h1>' in output.data.decode('utf-8'))
        self.assertTrue(
            'Listed here are all current and past elections.'
            in output.data.decode('utf-8'))

        create_elections(self.session)

        output = self.app.get('/elections/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Elections</h1>' in output.data.decode('utf-8'))
        self.assertTrue(
            'Listed here are all current and past elections.'
            in output.data.decode('utf-8'))
        self.assertTrue(
            'Wallpaper F21' in output.data.decode('utf-8'))
        self.assertTrue(
            'Wallpaper F19' in output.data.decode('utf-8'))
        self.assertTrue(
            'Wallpaper F20' in output.data.decode('utf-8'))
        self.assertEqual(
            output.data.decode('utf-8').count('static/Approved.png'), 3)
        self.assertEqual(
            output.data.decode('utf-8').count('static/Denied.png'), 6)

    def test_election(self):
        """ Test the election function. """
        output = self.app.get('/election/1')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/election/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<li class="error">No election found</li>'
                        in output.data.decode('utf-8'))

        create_elections(self.session)

        # Election exists but no candidates
        output = self.app.get('/election/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Election: Wallpaper F19 - 2013</h1>'
            in output.data.decode('utf-8'))
        self.assertTrue(
            'Below is a list of candidates for this election.'
            in output.data.decode('utf-8'))
        self.assertTrue(
            '<p> No candidates have been registered for this election '
            '(yet). </p>' in output.data.decode('utf-8'))

        create_candidates(self.session)
        approve_candidate(self.session)

        # Election exists and there are candidates
        output = self.app.get('/election/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Election: Wallpaper F19 - 2013</h1>'
            in output.data.decode('utf-8'))
        self.assertTrue(
            'Below is a list of candidates for this election.'
            in output.data.decode('utf-8'))
        self.assertTrue(
            'Click on the picture to get a larger version'
            in output.data.decode('utf-8'))
        self.assertEqual(
            output.data.decode('utf-8').count(
                "data-lightbox='Wallpaper F19"),
            2)

        output = self.app.get('/election/3/')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/election/3/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="error">This election is not open</li>'
            in output.data.decode('utf-8'))

        # Is open and redirects you to the voting page
        output = self.app.get('/election/2/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/election/2/')
            self.assertEqual(output.status_code, 302)
            self.assertTrue(
                'target URL: <a href="/election/2/vote/">'
                in output.data.decode('utf-8'))

            output = self.app.get('/election/2/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Vote: Wallpaper F20 - 2013</h1>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                'var votelimit = 2 - 0;' in output.data.decode('utf-8'))

        create_votes(self.session)

        with user_set(nuancier.APP, user):

            output = self.app.get('/election/2/')
            self.assertEqual(output.status_code, 302)
            self.assertTrue(
                'target URL: <a href="/election/2/vote/">'
                in output.data.decode('utf-8'))

            output = self.app.get('/election/2/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Vote: Wallpaper F20 - 2013</h1>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                'var votelimit = 2 - 1;' in output.data.decode('utf-8'))

        user.username = 'ralph'
        with user_set(nuancier.APP, user):

            output = self.app.get('/election/2/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Election: Wallpaper F20 - 2013</h1>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                'Below is a list of candidates for this election.'
                in output.data.decode('utf-8'))
            self.assertTrue(
                'Click on the picture to get a larger version'
                in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count(
                    "data-lightbox='Wallpaper F20"),
                3)

    def test_vote(self):
        """ Test the vote function. """
        ## Login required
        output = self.app.get('/election/1/vote')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/election/1/vote/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        # Fails; not CLA + 1
        user.groups = []
        with user_set(nuancier.APP, user):
            output = self.app.get(
                '/election/1/vote/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You must be in one more '
                'group than the CLA</li>' in output.data.decode('utf-8'))

        # Fails; CLA not signed
        user.groups = ['packager', 'cla_done']
        user.cla_done = False
        with user_set(nuancier.APP, user):
            output = self.app.get(
                '/election/1/vote/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You must sign the CLA '
                '(Contributor License Agreement to use nuancier</li>'
                in output.data.decode('utf-8'))

        # Works
        user.cla_done = True
        with user_set(nuancier.APP, user):
            output = self.app.get('/election/1/vote')
            self.assertTrue(output.status_code in [301, 308])

            output = self.app.get('/election/1/vote/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No election found</li>'
                in output.data.decode('utf-8'))

        create_elections(self.session)
        create_candidates(self.session)
        approve_candidate(self.session)

        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/election/1/vote/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get(
                '/election/1/vote/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">This election is not open</li>'
                in output.data.decode('utf-8'))

            output = self.app.get(
                '/election/2/vote/', follow_redirects=True)
            self.assertTrue(
                '<h1>Vote: Wallpaper F20 - 2013</h1>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                'var votelimit = 2 - 0;' in output.data.decode('utf-8'))

        create_votes(self.session)

        user.username = 'ralph'
        with user_set(nuancier.APP, user):
            output = self.app.get(
                '/election/2/vote/', follow_redirects=True)
            self.assertTrue(
                '<h1>Election: Wallpaper F20 - 2013</h1>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="error">You have cast the maximal '
                'number of votes allowed for this election.</li>'
                in output.data.decode('utf-8'))

    def test_process_vote(self):
        """ Test the process_vote function. """
        ## Login required
        output = self.app.post('/election/1/voted')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.post('/election/1/voted/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        # Fails; not CLA + 1
        user.groups = []
        with user_set(nuancier.APP, user):
            output = self.app.post('/election/1/voted/',
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You must be in one more '
                'group than the CLA</li>' in output.data.decode('utf-8'))

        # Fails; CLA not signed
        user.groups = ['packager', 'cla_done']
        user.cla_done = False
        with user_set(nuancier.APP, user):
            output = self.app.post('/election/1/voted/',
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You must sign the CLA '
                '(Contributor License Agreement to use nuancier</li>'
                in output.data.decode('utf-8'))

        # Fails: no elections
        user.cla_done = True
        with user_set(nuancier.APP, user):
            # Edit the first election
            output = self.app.get('/election/1/vote/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No election found</li>'
                in output.data.decode('utf-8'))

        create_elections(self.session)
        create_candidates(self.session)
        approve_candidate(self.session)

        # Works
        with user_set(nuancier.APP, user):
            # No CSRF
            output = self.app.post('/election/1/voted/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">Wrong input submitted</li>'
                in output.data.decode('utf-8'))

            output = self.app.get('/election/2/vote/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Vote: Wallpaper F20 - 2013</h1>'
                in output.data.decode('utf-8'))

            csrf_token = output.data.decode('utf-8').split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {'csrf_token': csrf_token}

            # Election does not exists
            output = self.app.post('/election/10/voted/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No election found</li>'
                in output.data.decode('utf-8'))

            # Election closed
            output = self.app.post('/election/1/voted/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">This election is not open</li>'
                in output.data.decode('utf-8'))

            # Missing data
            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Vote: Wallpaper F20 - 2013</h1>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="error">You did not select any candidate to '
                'vote for.</li>' in output.data.decode('utf-8'))

            # Incorrect selection data
            data = {
                'selection': 1,
                'csrf_token': csrf_token
            }

            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Vote: Wallpaper F20 - 2013</h1>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="error">The selection you have made contains '
                'element which are not part of this election, please be '
                'careful.</li>' in output.data.decode('utf-8'))

            # Selection too large
            data = {
                'selection': [3, 4, 5],
                'csrf_token': csrf_token
            }

            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Vote: Wallpaper F20 - 2013</h1>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="error">You selected 3 wallpapers '
                'while you are only allowed to select 2</li>'
                in output.data.decode('utf-8'))

            # Works
            data = {
                'selection': [3, 4],
                'csrf_token': csrf_token
            }

            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Elections</h1>' in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="message">Your vote has been '
                'recorded, thank you for voting on Wallpaper'
                ' F20 2013</li>' in output.data.decode('utf-8'))

            # Already voted
            data = {
                'selection': [3, 4],
                'csrf_token': csrf_token
            }

            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Election: Wallpaper F20 - 2013</h1>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="error">You have cast the maximal '
                'number of votes allowed for this election.</li>'
                in output.data.decode('utf-8'))

        # Only 1 vote by 1 person registered
        results = nuancierlib.get_results(self.session, 2)
        self.assertEqual(2, len(results))
        self.assertEqual(1, results[0][1])  # number of votes

        # Works
        user.username = 'toshio'
        user.groups.append('designteam')
        with user_set(nuancier.APP, user):
            # Works
            data = {
                'selection': [3, 4],
                'csrf_token': csrf_token
            }

            output = self.app.post('/election/2/voted/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Elections</h1>' in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="message">Your vote has been '
                'recorded, thank you for voting on Wallpaper'
                ' F20 2013</li>' in output.data.decode('utf-8'))

        # 2 person voted but 3 votes recorded:
        results = nuancierlib.get_results(self.session, 2)
        self.assertEqual(2, len(results))
        self.assertEqual(3, results[0][1])  # number of votes

    def test_results_list(self):
        """ Test the results_list function. """
        output = self.app.get('/results')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/results/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Election results</h1>' in output.data.decode('utf-8'))
        self.assertTrue(
            '<p class="error">No election results have been '
            'made public (yet).</p>' in output.data.decode('utf-8'))

        create_elections(self.session)
        create_candidates(self.session)
        approve_candidate(self.session)
        create_votes(self.session)

        output = self.app.get('/results/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Election results</h1>' in output.data.decode('utf-8'))
        self.assertTrue(
            'Wallpaper F19 - 2013' in output.data.decode('utf-8'))
        self.assertEqual(
            output.data.decode('utf-8').count('href="/results/'), 2)

    def test_results(self):
        """ Test the results function. """
        output = self.app.get('/results/1')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/results/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<li class="error">No election found</li>'
                        in output.data.decode('utf-8'))

        create_elections(self.session)
        create_candidates(self.session)
        approve_candidate(self.session)
        create_votes(self.session)

        output = self.app.get('/results/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Election results: Wallpaper F19 - 2013</h1>'
            in output.data.decode('utf-8'))
        self.assertTrue(
            'Below are the results of the election Wallpaper F19'
            in output.data.decode('utf-8'))

        output = self.app.get('/results/2/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="error">The results this election are '
            'not public yet</li>' in output.data.decode('utf-8'))
        self.assertTrue(
            '<h1>Election results</h1>' in output.data.decode('utf-8'))

        output = self.app.get('/results/3/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="error">The results this election are '
            'not public yet</li>' in output.data.decode('utf-8'))
        self.assertTrue(
            '<h1>Election results</h1>' in output.data.decode('utf-8'))

    def test_admin_index(self):
        """ Test the admin_index function. """
        output = self.app.get('/admin')
        self.assertTrue(output.status_code in [301, 308])

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
            self.assertTrue(
                '<li class="error">You are neither an administrator or a '
                'reviewer of nuancier</li>' in output.data.decode('utf-8'))

        # Fails - did not sign the CLA
        user.cla_done = False
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You must sign the CLA '
                '(Contributor License Agreement to use nuancier</li>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<h1>Nuancier</h1>' in output.data.decode('utf-8'))
            self.assertTrue(
                'Nuancier is a simple voting application'
                in output.data.decode('utf-8'))

        # Fails - is not CLA + 1
        user.cla_done = True
        user.groups = []
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You must be in one more '
                'group than the CLA</li>' in output.data.decode('utf-8'))
            self.assertTrue(
                '<h1>Nuancier</h1>' in output.data.decode('utf-8'))
            self.assertTrue(
                'Nuancier is a simple voting application'
                in output.data.decode('utf-8'))

        # Success
        user.groups = ['packager', 'cla_done', 'sysadmin-main']
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Nuancier Admin -- Version'
                in output.data.decode('utf-8'))

            create_elections(self.session)
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Nuancier Admin -- Version'
                in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F19' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F20' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F21' in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('src="/static/Denied.png"'), 6)
            self.assertEqual(
                output.data.decode('utf-8').count('src="/static/Approved.png"'), 3)

        user.groups = ['packager', 'cla_done']

    def test_admin_edit(self):
        """ Test the admin_edit function. """
        output = self.app.get('/admin/1/edit')
        self.assertTrue(output.status_code in [301, 308])

        # Redirects to the OpenID page
        output = self.app.get('/admin/1/edit/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/1/edit/')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/1/edit/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You are neither an administrator or a '
                'reviewer of nuancier</li>' in output.data.decode('utf-8'))

        user.groups.append('designteam')
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/1/edit/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You are not an administrator'
                ' of nuancier</li>' in output.data.decode('utf-8'))

        user.groups.append('sysadmin-main')
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/1/edit/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No election found</li>'
                in output.data.decode('utf-8'))

        create_elections(self.session)

        with user_set(nuancier.APP, user):
            # Check the admin page before the edit
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Nuancier Admin -- Version'
                in output.data.decode('utf-8'))
            self.assertFalse(
                'election1' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F19' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F20' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F21' in output.data.decode('utf-8'))

            # Edit the first election
            output = self.app.get('/admin/1/edit/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Edit election: Wallpaper F19 -- 2013</h1>'
                in output.data.decode('utf-8'))

            csrf_token = output.data.decode('utf-8').split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'election_name': 'election1',
                'election_folder': 'pingou',
                'election_year': '2014',
                'submission_date_start': TODAY - timedelta(days=15),
                'submission_date_end': TODAY - timedelta(days=13),
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'user_n_candidates': 5,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/1/edit/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            # Redirected to the admin index page, after the edit
            self.assertTrue(
                '<h1>Nuancier Admin -- Version'
                in output.data.decode('utf-8'))
            self.assertFalse(
                'Wallpaper F19' in output.data.decode('utf-8'))
            self.assertTrue(
                'election1' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F20' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F21' in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('2014'), 3)
            self.assertEqual(
                output.data.decode('utf-8').count(str(TODAY.year)), 9)


            # Edit failed: Name exists
            data = {
                'election_name': 'Wallpaper F20',
                'election_folder': 'pingou',
                'election_year': '2013',
                'submission_date_start': TODAY - timedelta(days=15),
                'submission_date_end': TODAY - timedelta(days=13),
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'user_n_candidates': 5,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/1/edit/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(' <li class="error">Could not edit this election'
                            ', is this name or folder already used?</li>'
                            in output.data.decode('utf-8'))
            self.assertTrue('<h1>Edit election: election1 -- 2014</h1>'
                            in output.data.decode('utf-8'))

            # Edit failed: folder exists
            data = {
                'election_name': 'election1',
                'election_folder': 'F20',
                'election_year': '2013',
                'submission_date_start': TODAY - timedelta(days=15),
                'submission_date_end': TODAY - timedelta(days=13),
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'user_n_candidates': 5,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/1/edit/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                ' <li class="error">Could not edit this election'
                ', is this name or folder already used?</li>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<h1>Edit election: election1 -- 2014</h1>'
                in output.data.decode('utf-8'))

        user.groups = ['packager', 'cla_done']

    def test_admin_new(self):
        """ Test the admin_new function. """
        output = self.app.get('/admin/new')
        self.assertTrue(output.status_code in [301, 308])

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
            self.assertTrue(
                '<li class="error">You are neither an administrator or a '
                'reviewer of nuancier</li>' in output.data.decode('utf-8'))

        user.groups.append('designteam')
        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/new/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You are not an administrator'
                ' of nuancier</li>' in output.data.decode('utf-8'))

        user.groups.append('sysadmin-main')
        create_elections(self.session)

        with user_set(nuancier.APP, user):
            # Check the admin page before the edit
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Nuancier Admin -- Version'
                in output.data.decode('utf-8'))
            self.assertFalse(
                'election1' in output.data.decode('utf-8'))
            self.assertFalse(
                'election2' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F19' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F20' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F21' in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('2014'), 2)
            self.assertEqual(
                output.data.decode('utf-8').count(str(TODAY.year)), 9)
            self.assertEqual(
                output.data.decode('utf-8').count('2013'), 3)

            # Add the new election
            output = self.app.get('/admin/new/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>New election</h1>' in output.data.decode('utf-8'))

            csrf_token = output.data.decode('utf-8').split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # election_n_choice should be a number
            data = {
                'election_name': 'election1',
                'election_folder': 'pingou',
                'election_year': '2014',
                'submission_date_start': TODAY - timedelta(days=15),
                'submission_date_end': TODAY - timedelta(days=13),
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 'abc',
                'generate_cache': True,
                'user_n_candidates': 5,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>New election</h1>' in output.data.decode('utf-8'))
            self.assertTrue('<td class="error">Field must contain a '
                            'number</td>' in output.data.decode('utf-8'))

            data = {
                'election_name': 'election1',
                'election_folder': 'pingou',
                'election_year': '2014',
                'submission_date_start': TODAY - timedelta(days=15),
                'submission_date_end': TODAY - timedelta(days=13),
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'user_n_candidates': 5,
                'generate_cache': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            # Redirected to the admin index page, after the creation
            self.assertTrue(
                '<h1>Nuancier Admin -- Version'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="error">The folder said to contain '
                'the pictures of this election'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="message">Election created</li>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                'election1' in output.data.decode('utf-8'))
            self.assertFalse(
                'election2' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F19' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F20' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F21' in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('2014'), 3)
            self.assertEqual(
                output.data.decode('utf-8').count(str(TODAY.year)), 12)
            self.assertEqual(
                output.data.decode('utf-8').count('2013'), 3)

            data = {
                'election_name': 'election2',
                'election_folder': 'pingou2',
                'election_year': '2014',
                'submission_date_start': TODAY - timedelta(days=15),
                'submission_date_end': TODAY - timedelta(days=13),
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'user_n_candidates': 5,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            # Redirected to the admin index page, after the creation
            self.assertTrue(
                '<h1>Nuancier Admin -- Version'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="message">Election created</li>'
                in output.data.decode('utf-8'))
            self.assertFalse(
                '<li class="error">The folder said to contain '
                'the pictures of this election'
                in output.data.decode('utf-8'))
            self.assertTrue(
                'election1' in output.data.decode('utf-8'))
            self.assertTrue(
                'election2' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F19' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F20' in output.data.decode('utf-8'))
            self.assertTrue(
                'Wallpaper F21' in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('2014'), 4)
            self.assertEqual(
                output.data.decode('utf-8').count(str(TODAY.year)), 15)
            self.assertEqual(
                output.data.decode('utf-8').count('2013'), 3)

            # Edit failed: Name exists
            data = {
                'election_name': 'Wallpaper F20',
                'election_folder': 'pingou',
                'election_year': '2013',
                'submission_date_start': TODAY - timedelta(days=15),
                'submission_date_end': TODAY - timedelta(days=13),
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'user_n_candidates': 5,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                ' <li class="error">Could not add this election'
                ', is this name or folder already used?</li>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<h1>New election</h1>' in output.data.decode('utf-8'))

            # Edit failed: folder exists
            data = {
                'election_name': 'election1',
                'election_folder': 'F20',
                'election_year': '2013',
                'submission_date_start': TODAY - timedelta(days=15),
                'submission_date_end': TODAY - timedelta(days=13),
                'election_date_start': TODAY - timedelta(days=10),
                'election_date_end': TODAY - timedelta(days=8),
                'election_badge_link': 'http://badges.fp.org',
                'election_n_choice': 3,
                'user_n_candidates': 5,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                ' <li class="error">Could not add this election'
                ', is this name or folder already used?</li>'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<h1>New election</h1>' in output.data.decode('utf-8'))

        user.groups = ['packager', 'cla_done']

    def test_admin_review(self):
        """ Test the admin_review function. """
        output = self.app.get('/admin/review/1')
        self.assertTrue(output.status_code in [301, 308])

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
            self.assertTrue(
                '<li class="error">You are neither an administrator or a '
                'reviewer of nuancier</li>' in output.data.decode('utf-8'))

        user.groups.append('sysadmin-main')

        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/review/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No election found</li>'
                in output.data.decode('utf-8'))

        create_elections(self.session)

        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/review/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">The results of this election'
                ' are already public, this election can no longer be '
                'changed</li>' in output.data.decode('utf-8'))

            output = self.app.get('/admin/review/2/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">This election is already open'
                ' to public votes and can no longer be changed'
                '</li>' in output.data.decode('utf-8'))

            output = self.app.get('/admin/review/3/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<p class="error">No candidates found for this '
                'election.</p>' in output.data.decode('utf-8'))

            create_candidates(self.session)

            output = self.app.get('/admin/review/3/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Review election: Wallpaper F21 - 2014</h1>'
                in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('name="candidates_id"'),
                4)

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
            self.assertTrue(
                '<li class="error">You are neither an administrator or a '
                'reviewer of nuancier</li>' in output.data.decode('utf-8'))

        user.groups.append('designteam')
        with user_set(nuancier.APP, user):
            output = self.app.post('/admin/review/1/process',
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You are not an administrator of '
                'nuancier</li>' in output.data.decode('utf-8'))

        user.groups.append('sysadmin-main')
        create_elections(self.session)
        create_candidates(self.session)

        with user_set(nuancier.APP, user):
            output = self.app.post('/admin/review/1/process',
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<li class="error">Wrong input submitted</li>'
                            in output.data.decode('utf-8'))

            output = self.app.get(
                '/admin/review/3/all', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Review election: Wallpaper F21 - 2014</h1>'
                in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('name="candidates_id"'),
                4)

            csrf_token = output.data.decode('utf-8').split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {'csrf_token': csrf_token}

            output = self.app.post('/admin/review/10/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No election found</li>'
                in output.data.decode('utf-8'))

        with user_set(nuancier.APP, user):
            # Check the review page before changes
            output = self.app.get('/admin/review/3/all')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Review election: Wallpaper F21 - 2014</h1>'
                in output.data.decode('utf-8'))

            self.assertEqual(
                output.data.decode('utf-8').count('="/static/New.png"'),
                4)
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/Approved.png"'),
                0)
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/Denied.png"'),
                0)

            # Fails: results public
            output = self.app.post('/admin/review/1/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">The results of this election'
                ' are already public, this election can no '
                'longer be changed</li>' in output.data.decode('utf-8'))

            # Fails: vote open
            output = self.app.post('/admin/review/2/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">This election is already open to public '
                'votes and can no longer be changed</li>'
                in output.data.decode('utf-8'))

            # Fails: no input submitted (beside the csrf_token)
            output = self.app.post('/admin/review/3/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">Only the actions "Approved" or "Denied" '
                'are accepted</li>' in output.data.decode('utf-8'))

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
            self.assertTrue(
                ' <li class="error">One of the candidate submitted was not '
                'candidate in this election</li>'
                in output.data.decode('utf-8'))

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
            self.assertTrue(
                ' <li class="error">One of the candidate submitted was not '
                'candidate in this election</li>'
                in output.data.decode('utf-8'))

            # Check again the review page - no changes
            output = self.app.get('/admin/review/3/all')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Review election: Wallpaper F21 - 2014</h1>'
                in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/New.png"'),
                4)
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/Approved.png"'),
                0)
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/Denied.png"'),
                0)

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
            self.assertTrue(
                '<li class="message">Candidate(s) updated</li>'
                in output.data.decode('utf-8'))

            # Check again the review page for changes
            output = self.app.get('/admin/review/3/all')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Review election: Wallpaper F21 - 2014</h1>'
                in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/New.png"'),
                3)
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/Approved.png"'),
                1)
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/Denied.png"'),
                0)

            # Check again the review page for changes
            output = self.app.get('/admin/review/3/pending')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Review election: Wallpaper F21 - 2014</h1>'
                in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/New.png"'),
                3)
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/Approved.png"'),
                0)
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/Denied.png"'),
                0)

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
            self.assertTrue(
                '<li class="error">You must provide a reason to deny a '
                'candidate</li>' in output.data.decode('utf-8'))

            # Fails: no motif to reject candidate
            data = {
                'action': 'Denied',
                'candidates_id': '6',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/review/3/process', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You must provide a reason to deny a '
                'candidate</li>' in output.data.decode('utf-8'))

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
            self.assertTrue(
                '<li class="message">Candidate(s) updated</li>'
                in output.data.decode('utf-8'))

            # Check again the review page for changes
            output = self.app.get('/admin/review/3/denied')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Review election: Wallpaper F21 - 2014</h1>'
                            in output.data.decode('utf-8'))
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/New.png"'),
                0)
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/Approved.png"'),
                0)
            self.assertEqual(
                output.data.decode('utf-8').count('="/static/Denied.png"'),
                1)

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
            self.assertTrue(
                '<li class="error">You are neither an administrator or a '
                'reviewer of nuancier</li>' in output.data.decode('utf-8'))

        user.groups.append('sysadmin-main')

        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/cache/2', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No election found</li>'
                in output.data.decode('utf-8'))

        create_elections(self.session)

        with user_set(nuancier.APP, user):
            output = self.app.get('/admin/cache/2', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Cache regenerated for election '
                'Wallpaper F20</li>' in output.data.decode('utf-8'))

            output = self.app.get(
                '/admin/cache/2?next=/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Cache regenerated for election '
                'Wallpaper F20</li>' in output.data.decode('utf-8'))
            self.assertTrue(
                '<h1>Nuancier</h1>' in output.data.decode('utf-8'))
            self.assertTrue(
                '<h3>Vote</h3>' in output.data.decode('utf-8'))
            self.assertTrue(
                '<h3>Contribute</h3>' in output.data.decode('utf-8'))

            output = self.app.get('/admin/cache/1', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">The folder said to contain the pictures '
                'of this election' in output.data.decode('utf-8'))

        self.assertTrue(os.path.exists(CACHE_FOLDER))

    def test_stats(self):
        """ Test the stats function. """
        output = self.app.get('/stats/2/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<li class="error">No election found</li>'
                        in output.data.decode('utf-8'))

        create_elections(self.session)

        output = self.app.get('/stats/2/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Election results</h1>' in output.data.decode('utf-8'))
        self.assertTrue(
            '<li class="error">The results this election are not public '
            'yet</li>' in output.data.decode('utf-8'))

        create_candidates(self.session)
        create_votes(self.session)

        output = self.app.get('/stats/1/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h1>Election statistics</h1>'
            in output.data.decode('utf-8'))
        self.assertTrue(
            '<div id="placeholder" class="demo-placeholder"></div>'
            in output.data.decode('utf-8'))

    def test_contributions(self):
        """ Test the contributions function. """
        output = self.app.get('/contributions')
        self.assertTrue(output.status_code in [301, 308])

        # Redirects to the OpenID page
        output = self.app.get('/contributions/')
        self.assertEqual(output.status_code, 302)

        user = FakeFasUser()
        user.groups = ['packager', 'cla_done']

        create_elections(self.session)
        create_candidates(self.session)
        deny_candidate(self.session)

        with user_set(nuancier.APP, user):
            output = self.app.get('/contributions/')
            self.assertEqual(output.status_code, 200)

            self.assertTrue(
                '<a href="/contribution/6/update">'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<a href="/contribution/7/update">'
                in output.data.decode('utf-8'))

    def test_update_candidate(self):
        """ Test the update_candidate function. """

        # Fails login required
        output = self.app.get('/contribution/6/update')
        self.assertEqual(output.status_code, 302)

        create_elections(self.session)
        create_candidates(self.session)
        approve_candidate(self.session)
        deny_candidate(self.session)

        user = FakeFasUser()
        with user_set(nuancier.APP, user):
            output = self.app.get('/contribution/60/update')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">No candidate found</li>'
                in output.data.decode('utf-8'))

            output = self.app.get(
                '/contribution/4/update', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">The election of this candidate is not '
                'open for submission</li>' in output.data.decode('utf-8'))

            output = self.app.get(
                '/contribution/8/update', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">This candidate was already approved, you '
                'cannot update it</li>' in output.data.decode('utf-8'))

            output = self.app.get(
                '/contribution/9/update', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You are not the person that submitted '
                'this candidate, you may not update it</li>'
                in output.data.decode('utf-8'))

        upload_path = os.path.join(PICTURE_FOLDER, 'F21')

        with user_set(nuancier.APP, user):
            output = self.app.get('/contributions/')
            self.assertEqual(output.status_code, 200)

            self.assertTrue(
                '<a href="/contribution/6/update">'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<a href="/contribution/7/update">'
                in output.data.decode('utf-8'))

        with user_set(nuancier.APP, user):
            output = self.app.get('/contribution/6/update')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Update your candidate</h1>'
                            in output.data.decode('utf-8'))
            self.assertTrue(
                '<img src="/cache/F21/small2.0.JPG" alt="img small2.0.JPG"/>'
                in output.data.decode('utf-8'))

            self.assertTrue(
                '<input id="csrf_token" name="csrf_token"'
                in output.data.decode('utf-8'))

            csrf_token = output.data.decode('utf-8').split(
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
            with open(FILE_NOTOK, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribution/6/update', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">The submitted candidate has a '
                    'width of 1280 pixels which is lower than the minimum '
                    '1600 pixels required</li>'
                    in output.data.decode('utf-8')
                )
                self.assertTrue('<h1>Update your candidate</h1>'
                            in output.data.decode('utf-8'))

            self.assertFalse(os.path.exists(upload_path))

            # Wrong hight
            with open(FILE_NOTOK2, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribution/6/update', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">The submitted candidate has a '
                    'height of 1166 pixels which is lower than the minimum '
                    '1200 pixels required</li>'
                    in output.data.decode('utf-8')
                )
                self.assertTrue('<h1>Update your candidate</h1>'
                                in output.data.decode('utf-8'))

            self.assertFalse(os.path.exists(upload_path))

            # Is not an image
            with open(FILE_NOTOK3, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribution/6/update', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">The submitted candidate could not '
                    'be opened as an Image</li>'
                    in output.data.decode('utf-8')
                )
                self.assertTrue('<h1>Update your candidate</h1>'
                                in output.data.decode('utf-8'))

            self.assertFalse(os.path.exists(upload_path))

            # Wrong file extension
            with open(FILE_NOTOK4, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribution/6/update', data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    '<li class="error">The submitted candidate has the '
                    'file extension "txt" which is not an allowed format'
                    in output.data.decode('utf-8')
                )
                self.assertTrue('<h1>Update your candidate</h1>'
                                in output.data.decode('utf-8'))

            self.assertFalse(os.path.exists(upload_path))

            # Right file, works as it should
            with open(FILE_OK, 'rb') as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribution/6/update', data=data,
                                       follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    'class="message">Thanks for updating your submission</li>'
                    in output.data.decode('utf-8')
                )
                self.assertTrue(
                    '<h1>Nuancier</h1>' in output.data.decode('utf-8'))
                self.assertTrue(
                    'Nuancier is a simple voting application'
                    in output.data.decode('utf-8'))

            self.assertTrue(os.path.exists(upload_path))
            shutil.rmtree(upload_path)

            self.assertFalse(os.path.exists(upload_path))

    def test_update_candidate_not_allowed(self):
        """ Test the update_candidate function. """

        create_elections(self.session)
        create_candidates(self.session)
        approve_candidate(self.session)
        deny_candidate(self.session)

        upload_path = os.path.join(PICTURE_FOLDER, 'F21')

        user = FakeFasUser()
        user.cla_done = True
        with user_set(nuancier.APP, user):
            # Election does not allow updating submissions
            election = nuancierlib.get_election(self.session, 3)
            election.allows_updating = False
            self.session.add(election)
            self.session.commit()

            output = self.app.get('/contribution/6/update',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertIn(
                '<li class="error">This election does not allow rejected '
                'candidate to be updated</li>', output.data)

            output = self.app.get('/election/2/vote/')
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            with open(FILE_OK) as stream:
                data = {
                    'candidate_name': 'name',
                    'candidate_author': 'pingou',
                    'candidate_file': stream,
                    'candidate_license': 'CC-BY-SA',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/contribution/6/update', data=data,
                                       follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertIn(
                    '<li class="error">This election does not allow rejected '
                    'candidate to be updated</li>', output.data)
                self.assertTrue('<h1>Elections</h1>' in output.data)

        self.assertFalse(os.path.exists(upload_path))


    def test_contribute_max_upload(self):
        """ Test the contribute function when the user has already submitted
        a number of candidates.
        """

        create_elections(self.session)
        create_candidates(self.session)
        upload_path = os.path.join(PICTURE_FOLDER, 'F21')

        user = FakeFasUser()
        user.cla_done = True
        with user_set(nuancier.APP, user):
            output = self.app.get('/contribute/3', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h1>Elections</h1>' in output.data.decode('utf-8'))
            self.assertTrue(
                'Listed here are all current and past elections.'
                in output.data.decode('utf-8'))
            self.assertTrue(
                '<li class="error">You have uploaded the maximum number of '
                'candidates (3) you can upload for this election</li>'
                in output.data.decode('utf-8'))


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Nuanciertests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
