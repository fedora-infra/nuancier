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
Top level of the nuancier Flask application.
'''

import logging
import logging.handlers
import os
import sys

from functools import wraps

import flask
import dogpile.cache
import six

from flask_fas_openid import FAS
from six.moves.urllib.parse import urlparse, urljoin
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    # This is for the old versions not using pillow
    import Image

# There's currently a circular dependency between forms.py
# and this module and a refacter is required to fix it.
# until then, this needs to be set up before forms is imported.
APP = flask.Flask(__name__)  # NOQA

import nuancier.forms
import nuancier.lib as nuancierlib
import nuancier.proxy


## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101, E1103


__version__ = '0.11.0'


APP.config.from_object('nuancier.default_config')
if 'NUANCIER_CONFIG' in os.environ:  # pragma: no cover
    APP.config.from_envvar('NUANCIER_CONFIG')

# Set up FAS extension
FAS = FAS(APP)
APP.wsgi_app = nuancier.proxy.ReverseProxied(APP.wsgi_app)

# Initialize the cache.
CACHE = dogpile.cache.make_region().configure(
    APP.config.get('NUANCIER_CACHE_BACKEND', 'dogpile.cache.memory'),
    **APP.config.get('NUANCIER_CACHE_KWARGS', {})
)

# Set up the logger
## Send emails for big exception
mail_handler = logging.handlers.SMTPHandler(
    APP.config.get('NUANCIER_EMAIL_SMTP_SERVER', '127.0.0.1'),
    APP.config.get('NUANCIER_EMAIL_FROM', 'nobody@fedoraproject.org'),
    APP.config.get('NUANCIER_EMAIL_ERROR_TO', 'admin@fedoraproject.org'),
    '[Nuancier] error')
mail_handler.setFormatter(logging.Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
'''))
mail_handler.setLevel(logging.ERROR)
if not APP.debug:
    APP.logger.addHandler(mail_handler)

# Log to stderr as well
stderr_log = logging.StreamHandler(sys.stderr)
stderr_log.setLevel(logging.INFO)
APP.logger.addHandler(stderr_log)

LOG = APP.logger


SESSION = nuancierlib.create_session(APP.config['DB_URL'])


def is_safe_url(target):
    """ Checks that the target url is safe and sending to the current
    website not some other malicious one.
    """
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(
        urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def is_nuancier_admin(user):
    ''' Is the user a nuancier admin.
    '''
    if not user:
        return False
    if not user.cla_done or len(user.groups) < 1:
        return False

    admins = APP.config['ADMIN_GROUP']
    if isinstance(admins, six.string_types):  # pragma: no cover
        admins = set([admins])
    else:
        admins = set(admins)

    return len(set(user.groups).intersection(admins)) > 0


def is_nuancier_reviewer(user):
    ''' Is the user a nuancier reviewer.
    '''
    if not user:
        return False
    if not user.cla_done or len(user.groups) < 1:
        return False

    reviewers = APP.config['REVIEW_GROUP']
    if isinstance(reviewers, six.string_types):  # pragma: no cover
        reviewers = set([reviewers])
    else:  # pragma: no cover
        reviewers = set(reviewers)

    return len(set(user.groups).intersection(reviewers)) > 0


def has_weigthed_vote(user):
    ''' Has the user a weigthed vote or not.
    '''
    if not user:  # pragma: no cover
        return False
    if not user.cla_done or len(user.groups) < 1:  # pragma: no cover
        return False

    voters = APP.config['WEIGHTED_GROUP']
    if isinstance(voters, six.string_types):  # pragma: no cover
        voters = set([voters])
    else:  # pragma: no cover
        voters = set(voters)

    return len(set(user.groups).intersection(voters)) > 0


def fas_login_required(function):
    ''' Flask decorator to ensure that the user is logged in against FAS.
    To use this decorator you need to have a function named 'auth_login'.
    Without that function the redirect if the user is not logged in will not
    work.

    '''
    @wraps(function)
    def decorated_function(*args, **kwargs):
        ''' Wrapped function actually checking if the user is logged in.
        '''
        if not hasattr(flask.g, 'fas_user') or flask.g.fas_user is None:
            return flask.redirect(flask.url_for('.login',
                                                next=flask.request.url))
        elif not flask.g.fas_user.cla_done:
            flask.flash('You must sign the CLA (Contributor License '
                        'Agreement to use nuancier', 'error')
            return flask.redirect(flask.url_for('index'))
        return function(*args, **kwargs)
    return decorated_function


def contributor_required(function):
    ''' Flask decorator to ensure that the user is logged in against FAS.

    We'll always make sure the user is CLA+1 as it's what's needed to be
    allowed to vote.
    '''
    @wraps(function)
    def decorated_function(*args, **kwargs):
        ''' Wrapped function actually checking if the user is logged in.
        '''
        if not hasattr(flask.g, 'fas_user') or flask.g.fas_user is None:
            return flask.redirect(flask.url_for('.login',
                                                next=flask.request.url))
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
        if not hasattr(flask.g, 'fas_user') or flask.g.fas_user is None:
            return flask.redirect(flask.url_for('.login',
                                                next=flask.request.url))
        elif not flask.g.fas_user.cla_done:
            flask.flash('You must sign the CLA (Contributor License '
                        'Agreement to use nuancier', 'error')
            return flask.redirect(flask.url_for('index'))
        elif len(flask.g.fas_user.groups) == 0:
            flask.flash(
                'You must be in one more group than the CLA', 'error')
            return flask.redirect(flask.url_for('index'))
        elif not is_nuancier_admin(flask.g.fas_user) \
                and not is_nuancier_reviewer(flask.g.fas_user):
            flask.flash(
                'You are neither an administrator or a reviewer of nuancier',
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
      - portrait or landscape orientation
      - size of the image (1600x1200 minimal)
      - ratio of the image (16:9) - not checked by this function,
            it is only recommended

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
    if width < height:
       if APP.config.get('ALLOW_PORTRAIT', False):
           # portrait allowed, turn condition by 90 deg.; width is heigh and
           # vice versa
           swap = min_width
           min_width = min_height
           min_height = swap
       else:
           raise nuancierlib.NuancierException(
               'This instance does not support portrait oriented pictures.')
    if width < min_width:
        raise nuancierlib.NuancierException(
            'The submitted candidate has a width of %s pixels which is lower'
            ' than the minimum %s pixels required' % (width, min_width))
    if height < min_height:
        raise nuancierlib.NuancierException(
            'The submitted candidate has a height of %s pixels which is lower'
            ' than the minimum %s pixels required' % (height, min_height))


## Generic APP functions

@APP.template_filter('format_grp')
def format_grp(groups):
    """ Template filter to present correctly the groups given.
    In this case groups can be a string or a list
    """
    if isinstance(groups, six.string_types):  # pragma: no cover
        groups = set([groups])
    else:  # pragma: no cover
        groups = set(groups)

    return ', '.join(groups)

@APP.context_processor
def inject_is_admin():
    ''' Inject whether the user is a nuancier admin or not in every page
    (every template).
    '''
    user = None
    if hasattr(flask.g, 'fas_user'):
        user = flask.g.fas_user
    return dict(is_admin=is_nuancier_admin(user),
                is_reviewer=is_nuancier_reviewer(user),
                version=__version__)


# pylint: disable=W0613
@APP.teardown_request
def shutdown_session(exception=None):
    ''' Remove the DB session at the end of each request. '''
    SESSION.remove()


# pylint: disable=W0613
@APP.before_request
def set_session():
    """ Set the flask session as permanent. """
    flask.session.permanent = True


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


@APP.route('/login/', methods=['GET', 'POST'])
def login():  # pragma: no cover
    ''' Login mechanism for this application.
    '''
    next_url = None
    if 'next' in flask.request.args:
        if is_safe_url(flask.request.args['next']):
            next_url = flask.request.args['next']

    if not next_url or next_url == flask.url_for('.login'):
        next_url = flask.url_for('.index')

    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        return flask.redirect(next_url)
    else:
        admins = APP.config['ADMIN_GROUP']
        if isinstance(admins, six.string_types):  # pragma: no cover
            admins = set([admins])
        else:
            admins = set(admins)

        groups = list(admins)[:]

        reviewers = APP.config['REVIEW_GROUP']
        if isinstance(reviewers, six.string_types):  # pragma: no cover
            reviewers = set([reviewers])
        else:
            reviewers = set(reviewers)

        groups.extend(reviewers)

        voters = APP.config['WEIGHTED_GROUP']
        if isinstance(voters, six.string_types):  # pragma: no cover
            voters = set([voters])
        else:
            voters = set(voters)

        groups.extend(voters)

        return FAS.login(return_url=next_url, groups=groups)


@APP.route('/logout/')
def logout():  # pragma: no cover
    ''' Log out if the user is logged in other do nothing.
    Return to the index page at the end.
    '''
    next_url = None
    if 'next' in flask.request.args:
        if is_safe_url(flask.request.args['next']):
            next_url = flask.request.args['next']

    if not next_url or next_url == flask.url_for('.login'):
        next_url = flask.url_for('.index')

    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        FAS.logout()
        flask.flash('You are no longer logged-in')

    return flask.redirect(next_url)


# Finalize the import of other controllers
import nuancier.admin
import nuancier.ui
