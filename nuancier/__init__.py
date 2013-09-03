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
Top level of the nuancier-lite Flask application.
'''

import os
import random

import flask
from functools import wraps
from flask.ext.fas_openid import FAS

from sqlalchemy.exc import SQLAlchemyError

import forms
import lib as nuancierlib


__version__ = '0.1.0'

APP = flask.Flask(__name__)
APP.config.from_object('nuancier.default_config')
if 'NUANCIER_CONFIG' in os.environ:  # pragma: no cover
    APP.config.from_envvar('NUANCIER_CONFIG')

# Set up FAS extension
FAS = FAS(APP)

SESSION = nuancierlib.create_session(APP.config['DB_URL'])


def is_nuancier_admin():
    """ Is the user a nuancier admin.
    """
    if not hasattr(flask.g, 'fas_user') or not flask.g.fas_user:
        return False
    if not flask.g.fas_user.cla_done or \
            len(flask.g.fas_user.groups) < 1:
        return False

    return APP.config['ADMIN_GROUP'] in flask.g.fas_user.groups


def fas_login_required(function):
    """ Flask decorator to ensure that the user is logged in against FAS.
    To use this decorator you need to have a function named 'auth_login'.
    Without that function the redirect if the user is not logged in will not
    work.
    """
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if flask.g.fas_user is None:
            return flask.redirect(flask.url_for(
                '.login', next=flask.request.url))
        return function(*args, **kwargs)
    return decorated_function


def nuancier_admin_required(function):
    """ Decorator used to check if the loged in user is a nuancier admin
    or not.
    """
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if flask.g.fas_user is None or \
                not flask.g.fas_user.cla_done or \
                len(flask.g.fas_user.groups) < 1:
            return flask.redirect(flask.url_for('.login',
                                                next=flask.request.url))
        elif not is_nuancier_admin():
            flask.flash('You are not an administrator of nuancier-lite',
                        'errors')
            return flask.redirect(flask.url_for('msg'))
        else:
            return function(*args, **kwargs)
    return decorated_function


## APP

@APP.context_processor
def inject_is_admin():
    """ Inject whether the user is a nuancier admin or not in every page
    (every template).
    """
    return dict(is_admin=is_nuancier_admin())


# pylint: disable=W0613
@APP.teardown_request
def shutdown_session(exception=None):
    """ Remove the DB session at the end of each request. """
    SESSION.remove()


@APP.route('/msg/')
def msg():
    """ Page used to display error messages
    """
    return flask.render_template('msg.html')


@APP.route('/login/', methods=['GET', 'POST'])
def login():
    """ Login mechanism for this application.
    """
    next_url = None
    if 'next' in flask.request.args:
        next_url = flask.request.args['next']

    if not next_url or next_url == flask.url_for('.login'):
        next_url = flask.url_for('.index')

    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        return flask.redirect(next_url)
    else:
        return FAS.login(return_url=next_url)


@APP.route('/logout/')
def logout():
    """ Log out if the user is logged in other do nothing.
    Return to the index page at the end.
    """
    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        FAS.logout()
    return flask.redirect(flask.url_for('.index'))


@APP.route('/')
def index():
    ''' Display the index page. '''
    elections = nuancierlib.get_elections_open(SESSION)
    return flask.render_template('index.html', elections=elections)


@APP.route('/elections/')
def elections_list():
    ''' Displays the results of all published election. '''
    elections = nuancierlib.get_elections(SESSION)

    return flask.render_template(
        'elections_list.html',
        elections=elections)


@APP.route('/election/<int:election_id>/')
def election(election_id):
    ''' Display the index page of the election will all the candidates
    submitted. '''
    election = nuancierlib.get_election(SESSION, election_id)
    if not election:
        flask.flash('No election found', 'error')
        return flask.render_template('msg.html')

    if not election.election_open:
        flask.flash('This election is not open yet', 'error')
        return flask.redirect(flask.url_for('index'))

    candidates = nuancierlib.get_candidates(SESSION, election_id)

    if flask.g.fas_user:
        random.seed(flask.g.fas_user.username)
    random.shuffle(candidates)

    return flask.render_template(
        'election.html',
        candidates=candidates,
        election=election,
        picture_folder=os.path.join(
            APP.config['PICTURE_FOLDER'], election.election_folder),
        cache_folder=os.path.join(
            APP.config['CACHE_FOLDER'], election.election_folder)
    )


@APP.route('/election/<int:election_id>/vote/')
@fas_login_required
def vote(election_id):
    ''' Give the possibility to the user to vote for an election. '''
    election = nuancierlib.get_election(SESSION, election_id)
    if not election:
        flask.flash('No election found', 'error')
        return flask.render_template('msg.html')
    candidates = nuancierlib.get_candidates(SESSION, election_id)

    if flask.g.fas_user:
        random.seed(flask.g.fas_user.username)
    random.shuffle(candidates)

    # How many votes the user made:
    votes = nuancierlib.get_votes_user(SESSION, election_id,
                                       flask.g.fas_user.username)

    if len(votes) >= election.election_n_choice:
        flask.flash('You have already cast the maximal number of votes '
                    'allowed for this election.', 'error')
        return flask.redirect(
            flask.url_for('election', election_id=election_id))

    return flask.render_template(
        'vote.html',
        election=election,
        candidates=candidates,
        picture_folder=os.path.join(
            APP.config['PICTURE_FOLDER'], election.election_folder),
        cache_folder=os.path.join(
            APP.config['CACHE_FOLDER'], election.election_folder)
    )


@APP.route('/election/<int:election_id>/voted/', methods=['GET', 'POST'])
@fas_login_required
def process_vote(election_id):
    election = nuancierlib.get_election(SESSION, election_id)
    if not election:
        flask.flash('No election found', 'error')
        return flask.render_template('msg.html')

    candidates = nuancierlib.get_candidates(SESSION, election_id)
    candidate_ids = set([candidate.id for candidate in candidates])

    entries = set([int(entry)
                   for entry in flask.request.form.getlist('selection')])
    if not set(entries).issubset(candidate_ids):
        flask.flash('The selection you have made contains element which are '
                    'part of this election, please be careful.', 'error')
        return flask.redirect(flask.url_for('vote', election_id=election_id))

    # How many votes the user made:
    votes = nuancierlib.get_votes_user(SESSION, election_id,
                                       flask.g.fas_user.username)

    if len(votes) >= election.election_n_choice:
        flask.flash('You have already cast the maximal number of votes '
                    'allowed for this election.', 'error')
        return flask.redirect(
            flask.url_for('election', election_id=election_id))

    if len(votes) + len(entries) > election.election_n_choice:
        flask.flash('You selected %s wallpapers while you are only allowed '
                    'to select %s' % (
                        len(entries),
                        (election.election_n_choice - len(votes))),
                    'error')
        return flask.render_template(
            'vote.html',
            election=election,
            candidates=[nuancierlib.get_candidate(SESSION, candidate_id)
                        for candidate_id in entries],
            picture_folder=os.path.join(
                APP.config['PICTURE_FOLDER'], election.election_folder),
            cache_folder=os.path.join(
                APP.config['CACHE_FOLDER'], election.election_folder)
        )

    try:
        for selection in entries:
            nuancierlib.add_vote(SESSION, selection,
                                 flask.g.fas_user.username)
    except nuancierlib.NuancierException, err:
        flask.flash(err.message, 'error')

    try:
        SESSION.commit()
    except SQLAlchemyError as err:
        flask.flash(err.message, 'error')

    return flask.redirect(flask.url_for('vote', election_id=election_id))


@APP.route('/results/')
def results_list():
    ''' Displays the results of all published election. '''
    elections = nuancierlib.get_elections_public(SESSION)

    return flask.render_template(
        'result_list.html',
        elections=elections)


@APP.route('/results/<int:election_id>/')
def results(election_id):
    ''' Displays the results of an election. '''
    election = nuancierlib.get_election(SESSION, election_id)

    if not election:
        flask.flash('No election found', 'error')
        return flask.render_template('msg.html')

    if not election.election_public:
        flask.flash('The results this election are not public yet', 'error')
        return flask.redirect(flask.url_for('results_list'))

    results = nuancierlib.get_results(SESSION, election_id)

    return flask.render_template(
        'results.html',
        election=election,
        results=results,
        picture_folder=os.path.join(
            APP.config['PICTURE_FOLDER'], election.election_folder),
        cache_folder=os.path.join(
            APP.config['CACHE_FOLDER'], election.election_folder))


## ADMIN


@APP.route('/admin/')
def admin_index():
    ''' Display the index page of the admin interface. '''
    elections = nuancierlib.get_elections(SESSION)
    return flask.render_template('admin_index.html', elections=elections)


@APP.route('/admin/new/', methods=['GET', 'POST'])
@nuancier_admin_required
def admin_new():
    ''' Create a new election. '''
    form = forms.AddElectionForm()
    if form.validate_on_submit():
        try:
            nuancierlib.add_election(
                SESSION,
                election_name=form.election_name.data,
                election_folder=form.election_folder.data,
                election_year=form.election_year.data,
                election_open=form.election_open.data,
                election_n_choice=form.election_n_choice.data,
            )
        except nuancierlib.NuancierException as err:
            flask.flash(err.message, 'error')
        try:
            SESSION.commit()
        except SQLAlchemyError as err:
            flask.flash(err.message, 'error')
        return flask.redirect(flask.url_for('admin_index'))
    return flask.render_template('admin_new.html', form=form)


@APP.route('/admin/open/<int:election_id>')
def admin_open(election_id):
    ''' Flip the open state '''
    msg = nuancierlib.toggle_open(SESSION, election_id)
    try:
        SESSION.commit()
        flask.flash(msg)
    except SQLAlchemyError as err:
        flask.flash(err.message, 'error')
    return flask.redirect(flask.url_for('.admin_index'))


@APP.route('/admin/publish/<int:election_id>')
def admin_publish(election_id):
    ''' Flip the public state '''
    msg = nuancierlib.toggle_public(SESSION, election_id)
    try:
        SESSION.commit()
        flask.flash(msg)
    except SQLAlchemyError as err:
        flask.flash(err.message, 'error')
    return flask.redirect(flask.url_for('.admin_index'))


@APP.route('/admin/cache/<int:election_id>')
def admin_cache(election_id):
    ''' Regenerate the cache for this election. '''
    election = nuancierlib.get_election(SESSION, election_id)

    if not election:
        flask.flash('No election found', 'error')
        return flask.render_template('msg.html')

    try:
        nuancierlib.generate_cache(
            session=SESSION,
            election=election,
            picture_folder=APP.config['PICTURE_FOLDER'],
            cache_folder=APP.config['CACHE_FOLDER'],
            size=APP.config['THUMB_SIZE'])
        flask.flash('Cache regenerated for election %s' %
                    election.election_name)
    except nuancierlib.NuancierException as err:
        flask.flash(err.message, 'error')

    return flask.redirect(flask.url_for('.admin_index'))
