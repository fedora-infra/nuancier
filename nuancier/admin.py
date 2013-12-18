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
Admin interface for the nuancier flask application.
'''

import os

import flask

from sqlalchemy.exc import SQLAlchemyError

import nuancier
import nuancier.lib as nuancierlib

from nuancier import APP, SESSION, LOG, nuancier_admin_required


@APP.route('/admin/')
@nuancier_admin_required
def admin_index():
    ''' Display the index page of the admin interface. '''
    elections = nuancierlib.get_elections(SESSION)
    return flask.render_template('admin_index.html', elections=elections)


@APP.route('/admin/<election_id>/edit/', methods=['GET', 'POST'])
@nuancier_admin_required
def admin_edit(election_id):
    ''' Edit an election. '''
    election = nuancierlib.get_election(SESSION, election_id)

    if not election:
        flask.flash('No election found', 'error')
        return flask.render_template('msg.html')

    form = nuancier.forms.AddElectionForm()
    if flask.request.method == 'GET':
        form = nuancier.forms.AddElectionForm(election=election)

    if form.validate_on_submit():
        election = nuancierlib.edit_election(
            SESSION,
            election=election,
            election_name=form.election_name.data,
            election_folder=form.election_folder.data,
            election_year=form.election_year.data,
            election_date_start=form.election_date_start.data,
            election_date_end=form.election_date_end.data,
            election_n_choice=form.election_n_choice.data,
            election_badge_link=form.election_badge_link.data,
        )
        try:
            SESSION.commit()
            flask.flash('Election updated')
        except SQLAlchemyError as err:
            SESSION.rollback()
            LOG.debug("User: %s could not edit election: %s ",
                      flask.g.fas_user.username, election_id)
            LOG.exception(err)
            flask.flash('Could not edit this election, is this name or '
                        'folder already used?', 'error')
            return flask.render_template(
                'admin_edit.html',
                election=election,
                form=form)

        return flask.redirect(flask.url_for('admin_index'))
    return flask.render_template(
        'admin_edit.html',
        election=election,
        form=form)


@APP.route('/admin/new/', methods=['GET', 'POST'])
@nuancier_admin_required
def admin_new():
    ''' Create a new election. '''
    form = nuancier.forms.AddElectionForm()
    if form.validate_on_submit():

        election = nuancierlib.add_election(
            SESSION,
            election_name=form.election_name.data,
            election_folder=form.election_folder.data,
            election_year=form.election_year.data,
            election_date_start=form.election_date_start.data,
            election_date_end=form.election_date_end.data,
            election_n_choice=form.election_n_choice.data,
            election_badge_link=form.election_badge_link.data,
        )

        try:
            SESSION.commit()
        except SQLAlchemyError as err:
            SESSION.rollback()
            LOG.debug("User: %s could not add an election",
                      flask.g.fas_user.username)
            LOG.exception(err)
            flask.flash('Could not add this election, is this name or '
                        'folder already used?', 'error')
            return flask.render_template('admin_new.html', form=form)

        flask.flash('Election created')
        if form.generate_cache.data:
            return admin_cache(election.id)
        return flask.redirect(flask.url_for('admin_index'))
    return flask.render_template('admin_new.html', form=form)


@APP.route('/admin/review/<election_id>/', methods=['GET'])
@nuancier_admin_required
def admin_review(election_id):
    ''' Review a new election. '''
    election = nuancierlib.get_election(SESSION, election_id)

    if not election:
        flask.flash('No election found', 'error')
        return flask.render_template('msg.html')

    if election.election_open:
        flask.flash(
            'This election is already open to public votes and can no '
            'longer be changed', 'error')
        return flask.redirect(flask.url_for('admin_index'))

    if election.election_public:
        flask.flash(
            'The results of this election are already public, this election'
            ' can no longer be changed', 'error')
        return flask.redirect(flask.url_for('admin_index'))

    candidates = nuancierlib.get_candidates(SESSION, election_id)

    return flask.render_template(
        'admin_review.html',
        election=election,
        form=nuancier.forms.ConfirmationForm(),
        candidates=candidates,
        picture_folder=os.path.join(
            APP.config['PICTURE_FOLDER'], election.election_folder),
        cache_folder=os.path.join(
            APP.config['CACHE_FOLDER'], election.election_folder))


@APP.route('/admin/review/<election_id>/process', methods=['POST'])
@nuancier_admin_required
def admin_process_review(election_id):
    ''' Process the reviewing of a new election. '''
    election = nuancierlib.get_election(SESSION, election_id)

    form = nuancier.forms.ConfirmationForm()
    if not form.validate_on_submit():
        flask.flash('Wrong input submitted', 'error')
        return flask.render_template('msg.html')

    if not election:
        flask.flash('No election found', 'error')
        return flask.render_template('msg.html')

    if election.election_open:
        flask.flash(
            'This election is already open to public votes and can no '
            'longer be changed', 'error')
        return flask.redirect(flask.url_for('results_list'))

    if election.election_public:
        flask.flash(
            'The results of this election are already public, this election'
            ' can no longer be changed', 'error')
        return flask.redirect(flask.url_for('results_list'))

    candidates = nuancierlib.get_candidates(SESSION, election_id)
    candidates_id = [str(candidate.id) for candidate in candidates]

    candidates_selected = flask.request.form.getlist('candidates_id')
    motifs = flask.request.form.getlist('motifs')
    action = flask.request.form.get('action')

    if action:
        action = action.strip()

    if action not in ['Approved', 'Denied']:
        flask.flash(
            'Only the actions "Approved" or "Denied" are accepted',
            'error')
        return flask.redirect(
            flask.url_for('admin_review', election_id=election_id))

    selections = []
    for cand in candidates_id:
        if cand not in candidates_selected:
            selections.append(None)
        else:
            selections.append(cand)

    if action == 'Denied':
        req_motif = False
        if not motifs:
            req_motif = True
        for cnt in range(len(motifs)):
            motif = motifs[cnt]
            if selections[cnt] and not motif.strip():
                req_motif = True
                break
        if req_motif:
            flask.flash(
                'You must provide a motif to deny a candidate',
                'error')
            return flask.redirect(
                flask.url_for('admin_review', election_id=election_id))

    cnt = 0
    for candidate in candidates_selected:
        if candidate not in candidates_id:
            flask.flash(
                'One of the candidate submitted was not candidate in this '
                'election', 'error')
            return flask.redirect(
                flask.url_for('admin_review', election_id=election_id))

    for candidate in selections:
        if candidate:
            candidate = nuancierlib.get_candidate(SESSION, candidate)
            motif = None
            if len(motifs) > cnt:
                motif = motifs[cnt].strip()
            if action == 'Approved':
                candidate.approved = True
                candidate.approved_motif = motif
            else:
                candidate.approved = False
                candidate.approved_motif = motif
            SESSION.add(candidate)
        cnt += 1

    try:
        SESSION.commit()
    except SQLAlchemyError as err:  # pragma: no cover
        SESSION.rollback()
        LOG.debug('User: "%s" could not approve/deny candidate(s) for '
                  'election "%s"', flask.g.fas_user.username,
                  election_id)
        LOG.exception(err)
        flask.flash('Could not approve/deny candidate', 'error')

    flask.flash('Candidate(s) updated')

    return flask.redirect(
        flask.url_for('admin_review', election_id=election_id))


@APP.route('/admin/cache/<int:election_id>')
@nuancier_admin_required
def admin_cache(election_id):
    ''' Regenerate the cache for this election. '''
    election = nuancierlib.get_election(SESSION, election_id)

    next_url = None
    if 'next' in flask.request.args:
        next_url = flask.request.args['next']

    if not next_url or next_url == flask.url_for(
            '.admin_cache', election_id=election_id):
        next_url = flask.url_for('.admin_index')

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
        SESSION.rollback()
        LOG.debug('User: "%s" could not generate cache for "%s"',
                  flask.g.fas_user.username, election_id)
        LOG.exception(err)
        flask.flash(err.message, 'error')

    return flask.redirect(next_url)
