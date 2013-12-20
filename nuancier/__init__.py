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
Top level of the nuancier Flask application.
'''

import logging
import os
import re
import sys

import flask
import dogpile.cache
from bunch import Bunch
from functools import wraps
## pylint cannot import flask extension correctly
# pylint: disable=E0611,F0401
from openid_cla import cla
from openid_teams import teams
from flask.ext.openid import OpenID

from sqlalchemy.exc import SQLAlchemyError
from werkzeug import secure_filename

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    # This is for the old versions not using pillow
    import Image

import nuancier.forms
import nuancier.lib as nuancierlib
import nuancier.notifications


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101, E1103

__version__ = '0.2.0'

APP = flask.Flask(__name__)
LOG = logging.getLogger(__name__)

APP.config.from_object('nuancier.default_config')
if 'NUANCIER_CONFIG' in os.environ:  # pragma: no cover
    APP.config.from_envvar('NUANCIER_CONFIG')

# Set up OpenID in stateless mode
OID = OpenID(APP, store_factory=lambda: None,
             extension_responses=[cla.CLAResponse, teams.TeamsResponse])

# Initialize the cache.
CACHE = dogpile.cache.make_region().configure(
    APP.config.get('NUANCIER_CACHE_BACKEND', 'dogpile.cache.memory'),
    **APP.config.get('NUANCIER_CACHE_KWARGS', {})
)

SESSION = nuancierlib.create_session(APP.config['DB_URL'])

PATTERN = re.compile(r'http(s)?:\/\/(.*\.)?id\.fedoraproject\.org(/)?')


def is_nuancier_admin(groups):
    ''' Is the user a nuancier admin.
    '''
    if not groups:
        return False

    admins = APP.config['ADMIN_GROUP']
    if isinstance(admins, basestring):  # pragma: no cover
        admins = set([admins])
    else:
        admins = set(admins)

    return len(set(groups).intersection(admins)) > 0


def login_required(function):
    ''' Flask decorator to ensure that the user is logged. '''
    @wraps(function)
    def decorated_function(*args, **kwargs):
        ''' Wrapped function actually checking if the user is logged in.
        '''
        if not hasattr(flask.g, 'auth') or not flask.g.auth.logged_in:
            return flask.redirect(flask.url_for('.login',
                                                next=flask.request.url))
        return function(*args, **kwargs)
    return decorated_function


def fas_login_required(function):
    ''' Flask decorator to ensure that the user is logged in against FAS.
    To use this decorator you need to have a function named 'auth_login'.
    Without that function the redirect if the user is not logged in will not
    work.

    We'll always make sure the user is CLA+1 as it's what's needed to be
    allowed to vote.
    '''
    @wraps(function)
    def decorated_function(*args, **kwargs):
        ''' Wrapped function actually checking if the user is logged in.
        '''
        if not hasattr(flask.g, 'auth') or not flask.g.auth.logged_in:
            return flask.redirect(
                flask.url_for('.login', next=flask.request.url))
        elif not PATTERN.match(flask.g.auth.openid):
            flask.flash(
                'You have not authentified with a Fedora account', 'error')
            return flask.redirect(flask.url_for('index'))
        elif not flask.g.auth.cla_done:
            flask.flash('You must sign the CLA (Contributor License '
                        'Agreement) to use nuancier', 'error')
            return flask.redirect(flask.url_for('index'))
        elif not flask.g.auth.groups:
                flask.flash('You must be in one more group than the CLA',
                            'error')
                return flask.redirect(flask.url_for('index'))
        return function(*args, **kwargs)
    return decorated_function


def nuancier_admin_required(function):
    ''' Decorator used to check if the loged in user is a nuancier admin
    or not.
    '''
    @wraps(function)
    def decorated_function(*args, **kwargs):
        ''' Wrapped function actually checking if the user is an admin for
        nuancier.
        '''
        if not hasattr(flask.g, 'auth') or not flask.g.auth.logged_in:
            return flask.redirect(
                flask.url_for('.login', next=flask.request.url))
        elif not PATTERN.match(flask.g.auth.openid):
            flask.flash(
                'You have not authentified with a Fedora account', 'error')
            return flask.redirect(flask.url_for('index'))
        elif not flask.g.auth.cla_done:
            flask.flash('You must sign the CLA (Contributor License '
                        'Agreement to use nuancier', 'error')
            return flask.redirect(flask.url_for('index'))
        elif len(flask.g.auth.groups) == 0:
            flask.flash(
                'You must be in one more group than the CLA', 'error')
            return flask.redirect(flask.url_for('index'))
        elif not is_nuancier_admin(flask.g.auth.groups):
            flask.flash('You are not an administrator of nuancier',
                        'error')
            return flask.redirect(flask.url_for('index'))
        else:
            return function(*args, **kwargs)
    return decorated_function


def validate_input_file(input_file):
    ''' Validate the submitted input file.

    This validation has four layers:
      - extension of the file provided
      - MIMETYPE of the file provided
      - size of the image (1600x1200 minimal)
      - ratio of the image (16:9)

    :arg input_file: a File object of the candidate submitted/uploaded and
        for which we want to check that it compliants with our expectations.
    '''

    extension = os.path.splitext(
        secure_filename(input_file.filename))[1][1:].lower()
    if extension not in APP.config.get('ALLOWED_EXTENSIONS', []):
        raise nuancierlib.NuancierException(
            'The submitted candidate has the file extension "%s" which is '
            'not an allowed format' % extension)

    mimetype = input_file.mimetype.lower()
    if mimetype not in APP.config.get(
            'ALLOWED_MIMETYPES', []):  # pragma: no cover
        raise nuancierlib.NuancierException(
            'The submitted candidate has the MIME type "%s" which is '
            'not an allowed MIME type' % mimetype)

    try:
        image = Image.open(input_file.stream)
    except:
        raise nuancierlib.NuancierException(
            'The submitted candidate could not be opened as an Image')
    width, height = image.size
    min_width = APP.config.get('PICTURE_MIN_WIDTH', 1600)
    min_height = APP.config.get('PICTURE_MIN_HEIGHT', 1200)
    if width < min_width:
        raise nuancierlib.NuancierException(
            'The submitted candidate has a width of %s pixels which is lower'
            ' than the minimum %s pixels required' % (width, min_width))
    if height < min_height:
        raise nuancierlib.NuancierException(
            'The submitted candidate has a height of %s pixels which is lower'
            ' than the minimum %s pixels required' % (height, min_height))


@OID.after_login
def after_openid_login(resp):  # pragma: no cover
    ''' Handles the response sent by the OpenID server and store at the
    session level the information we can make use of later on.
    '''
    default = flask.url_for('index')
    if resp.identity_url:
        flask.session['openid'] = resp.identity_url
        flask.session['fullname'] = resp.fullname
        flask.session['nickname'] = resp.nickname or resp.fullname
        flask.session['email'] = resp.email

        # Handle OpenID extensions
        flask.session['cla'] = False
        if 'CLAResponse' in resp.extensions and resp.extensions['CLAResponse']:
            flask.session['cla'] = \
                cla.CLA_URI_FEDORA_DONE in resp.extensions['CLAResponse'].clas
        flask.session['groups'] = []
        if 'TeamsResponse' in resp.extensions and resp.extensions['TeamsResponse']:
            flask.session['groups'] = resp.extensions['TeamsResponse'].teams

        next_url = flask.request.args.get('next', default)
        return flask.redirect(next_url)
    else:
        return flask.redirect(default)


## Generic APP functions


@APP.before_request
def check_auth():
    ''' Retrieve the information from the session to set information at the
    request level.
    '''
    flask.g.auth = Bunch(
        logged_in=False,
        method=None,
        id=None,
        groups=[],
        cla_done=False,
        openid=None,
    )
    if 'openid' in flask.session:  # pragma: no cover
        flask.g.auth.logged_in = True
        flask.g.auth.method = u'openid'
        flask.g.auth.openid = flask.session.get('openid')
        flask.g.auth.nickname = flask.session.get('nickname', None)
        flask.g.auth.fullname = flask.session.get('fullname', None)
        flask.g.auth.email = flask.session.get('email', None)
        flask.g.auth.cla_done = flask.session.get('cla', False)
        flask.g.auth.groups = flask.session.get('groups', [])


@APP.context_processor
def inject_is_admin():
    ''' Inject whether the user is a nuancier admin or not in every page
    (every template).
    '''
    groups = None
    if hasattr(flask.g, 'auth'):
        groups = flask.g.auth.groups
    return dict(is_admin=is_nuancier_admin(groups),
                version=__version__)


# pylint: disable=W0613
@APP.teardown_request
def shutdown_session(exception=None):
    ''' Remove the DB session at the end of each request. '''
    SESSION.remove()


@CACHE.cache_on_arguments(expiration_time=3600)
@APP.route('/pictures/<path:filename>')
def base_picture(filename):
    ''' Returns a picture having the provided path relative to the
    PICTURE_FOLDER set in the configuration.
    '''
    return flask.send_from_directory(APP.config['PICTURE_FOLDER'], filename)


@CACHE.cache_on_arguments(expiration_time=3600)
@APP.route('/cache/<path:filename>')
def base_cache(filename):
    ''' Returns a picture having the provided path relative to the
    CACHE_FOLDER set in the configuration.
    '''
    return flask.send_from_directory(APP.config['CACHE_FOLDER'], filename)


@APP.route('/msg/')
def msg():
    ''' Page used to display error messages
    '''
    return flask.render_template('msg.html')


@APP.route('/login/', methods=('GET', 'POST'))
@APP.route('/login', methods=('GET', 'POST'))
@OID.loginhandler
def login():
    ''' Displays a form where the user can enter his/her openid server. '''
    if not APP.config['NUANCIER_ALLOW_GENERIC_OPENID']:
        flask.abort(403)

    default = flask.url_for('index')
    next_url = flask.request.args.get('next', default)
    if (hasattr(flask.g, 'fas_user') and flask.g.fas_user) or (
            hasattr(flask.g, 'auth') and flask.g.auth.logged_in):
        return flask.redirect(next_url)

    openid_server = flask.request.form.get('openid', None)
    if openid_server:  # pragma: no cover
        if PATTERN.match(openid_server):
            return OID.try_login(
                "https://id.fedoraproject.org",
                ask_for=['email', 'fullname', 'nickname'],
                extension_args=[
                    ('http://ns.launchpad.net/2007/openid-teams',
                     'query_membership', '_FAS_ALL_GROUPS_'),
                    ('http://fedoraproject.org/specs/open_id/cla',
                     'query_cla', 'http://admin.fedoraproject.org/accounts/cla/done')
                ])
        else:
            return OID.try_login(
                openid_server,
                ask_for=['email', 'fullname', 'nickname'])

    return flask.render_template(
        'login.html', next=OID.get_next_url(), error=OID.fetch_error())


@APP.route('/login/fedora/', methods=('GET', 'POST'))
@APP.route('/login/fedora', methods=('GET', 'POST'))
@OID.loginhandler
def fedora_login():  # pragma: no cover
    ''' Log the user in using the FAS-OpenID server. '''
    if not APP.config['NUANCIER_ALLOW_FAS_OPENID']:
        flask.abort(403)

    return OID.try_login(
        "https://id.fedoraproject.org",
        ask_for=['email', 'fullname', 'nickname'],
        extension_args=[
            ('http://ns.launchpad.net/2007/openid-teams',
             'query_membership', '_FAS_ALL_GROUPS_'),
            ('http://fedoraproject.org/specs/open_id/cla',
             'query_cla', 'http://admin.fedoraproject.org/accounts/cla/done')
        ])


@APP.route('/login/google/', methods=('GET', 'POST'))
@APP.route('/login/google', methods=('GET', 'POST'))
@OID.loginhandler
def google_login():  # pragma: no cover
    ''' Log the user in using google. '''
    if not APP.config['NUANCIER_ALLOW_GOOGLE_OPENID']:
        flask.abort(403)

    return OID.try_login(
        "https://www.google.com/accounts/o8/id",
        ask_for=['email', 'fullname'])


@APP.route('/login/yahoo/', methods=('GET', 'POST'))
@APP.route('/login/yahoo', methods=('GET', 'POST'))
@OID.loginhandler
def yahoo_login():  # pragma: no cover
    ''' Log the user in using yahoo. '''
    if not APP.config['NUANCIER_ALLOW_YAHOO_OPENID']:
        flask.abort(403)

    return OID.try_login(
        "https://me.yahoo.com/",
        ask_for=['email', 'fullname'])


@APP.route('/logout/')
@APP.route('/logout')
def logout():
    ''' Log out the user. '''
    if 'openid' in flask.session:  # pragma: no cover
        flask.session.pop('openid')
        flask.flash('You are no longer logged-in')
    if 'groups' in flask.session:
        flask.session.pop('groups')
    if 'cla' in flask.session:
        flask.session.pop('cla')
    return flask.redirect(flask.url_for('index'))

# Finalize the import of other controllers
import nuancier.admin
import nuancier.ui
