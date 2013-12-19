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
from flask.ext.openid import OpenID
from flask.ext.fas_openid import FAS

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
OID = OpenID(APP, store_factory=lambda: None)
# Set up FAS extension
FAS = FAS(APP)

# Initialize the cache.
CACHE = dogpile.cache.make_region().configure(
    APP.config.get('NUANCIER_CACHE_BACKEND', 'dogpile.cache.memory'),
    **APP.config.get('NUANCIER_CACHE_KWARGS', {})
)

SESSION = nuancierlib.create_session(APP.config['DB_URL'])


def is_nuancier_admin(user):
    ''' Is the user a nuancier admin.
    '''
    if not user:
        return False
    if not user.cla_done or len(user.groups) < 1:
        return False

    admins = APP.config['ADMIN_GROUP']
    if isinstance(admins, basestring):  # pragma: no cover
        admins = set([admins])
    else:
        admins = set(admins)

    return len(set(user.groups).intersection(admins)) > 0


def login_required(function):
    ''' Flask decorator to ensure that the user is logged. '''
    @wraps(function)
    def decorated_function(*args, **kwargs):
        ''' Wrapped function actually checking if the user is logged in.
        '''
        if (not hasattr(flask.g, 'fas_user') or flask.g.fas_user is None) \
                and (
                    not hasattr(flask.g, 'auth')
                    or not flask.g.auth.logged_in):
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
        if (not hasattr(flask.g, 'fas_user') or flask.g.fas_user is None) \
                and (
                    not hasattr(flask.g, 'auth')
                    or not flask.g.auth.logged_in):
            return flask.redirect(
                flask.url_for('.login', next=flask.request.url))
        elif flask.g.auth.logged_in:
            flask.flash(
                'You have not authentified with a Fedora account', 'error')
            return flask.redirect(flask.url_for('index'))
        elif not flask.g.fas_user.cla_done:
            flask.flash('You must sign the CLA (Contributor License '
                        'Agreement to use nuancier', 'error')
            return flask.redirect(flask.url_for('index'))
        elif len(flask.g.fas_user.groups) == 0:
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
        if (not hasattr(flask.g, 'fas_user') or flask.g.fas_user is None) \
                and (
                    not hasattr(flask.g, 'auth')
                    or not flask.g.auth.logged_in):
            return flask.redirect(
                flask.url_for('.login', next=flask.request.url))
        elif flask.g.auth.logged_in:
            flask.flash(
                'You have not authentified with a Fedora account', 'error')
            return flask.redirect(flask.url_for('index'))
        elif not flask.g.fas_user.cla_done:
            flask.flash('You must sign the CLA (Contributor License '
                        'Agreement to use nuancier', 'error')
            return flask.redirect(flask.url_for('index'))
        elif len(flask.g.fas_user.groups) == 0:
            flask.flash(
                'You must be in one more group than the CLA', 'error')
            return flask.redirect(flask.url_for('index'))
        elif not is_nuancier_admin(flask.g.fas_user):
            flask.flash('You are not an administrator of nuancier',
                        'error')
            return flask.redirect(flask.url_for('msg'))
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
    default = flask.url_for('index')
    if resp.identity_url:
        openid_url = resp.identity_url
        flask.session['openid'] = openid_url
        flask.session['fullname'] = resp.fullname
        flask.session['nickname'] = resp.nickname or resp.fullname
        flask.session['email'] = resp.email
        next_url = flask.request.args.get('next', default)
        return flask.redirect(next_url)
    else:
        return flask.redirect(default)


## Generic APP functions


@APP.before_request
def check_auth():
    flask.g.auth = Bunch(
        logged_in=False,
        method=None,
        id=None,
    )
    if 'openid' in flask.session:  # pragma: no cover
        flask.g.auth.logged_in = True
        flask.g.auth.method = u'openid'
        flask.g.auth.openid_url = flask.session.get('openid')
        flask.g.auth.nickname = flask.session.get('nickname', None)
        flask.g.auth.fullname = flask.session.get('fullname', None)
        flask.g.auth.email = flask.session.get('email', None)


@APP.context_processor
def inject_is_admin():
    ''' Inject whether the user is a nuancier admin or not in every page
    (every template).
    '''
    user = None
    if hasattr(flask.g, 'fas_user'):
        user = flask.g.fas_user
    return dict(is_admin=is_nuancier_admin(user),
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
    default = flask.url_for('index')
    next_url = flask.request.args.get('next', default)
    if (hasattr(flask.g, 'fas_user') and flask.g.fas_user) or (
            hasattr(flask.g, 'auth') and flask.g.auth.logged_in):
        return flask.redirect(next_url)

    openid_server = flask.request.form.get('openid', None)
    pat = re.compile('http(s)?:\/\/(.*\.)?id\.fedoraproject\.org(/)?')
    if openid_server:  # pragma: no cover
        if pat.match(openid_server):
            return FAS.login(return_url=next_url)
        else:
            return OID.try_login(
                openid_server, ask_for=['email', 'fullname', 'nickname'])

    return flask.render_template(
        'login.html', next=OID.get_next_url(), error=OID.fetch_error())


@APP.route('/login/fedora/')
@APP.route('/login/fedora')
@OID.loginhandler
def fedora_login():
    default = flask.url_for('index')
    next_url = flask.request.args.get('next', default)
    return FAS.login(return_url=next_url)

@APP.route('/login/google/')
@APP.route('/login/google')
@OID.loginhandler
def google_login():
    default = flask.url_for('index')
    next_url = flask.request.args.get('next', default)
    return OID.try_login(
        "https://www.google.com/accounts/o8/id",
        ask_for=['email', 'fullname'])

@APP.route('/login/yahoo/')
@APP.route('/login/yahoo')
@OID.loginhandler
def yahoo_login():
    default = flask.url_for('index')
    next_url = flask.request.args.get('next', default)
    return OID.try_login(
        "https://me.yahoo.com/",
        ask_for=['email', 'fullname'])


@APP.route('/logout/')
@APP.route('/logout')
def logout():
    FAS.logout()
    if 'openid' in flask.session:
        flask.session.pop('openid')
    flask.flash('You are no longer logged-in')
    return flask.redirect(flask.url_for('index'))

# Finalize the import of other controllers
import nuancier.admin
import nuancier.ui
