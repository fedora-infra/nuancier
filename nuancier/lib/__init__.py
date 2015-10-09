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
Backend library for nuancier.
'''

## Apparently some of our methods have too many arguments
# pylint: disable=R0913
## import Image is not
# pylint: disable=R0912

import os
import sys

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    try:
        ## Ignore warning about pylint not being able to import Image
        # pylint: disable=F0401
        import Image
    except ImportError:
        print >> sys.stderr, 'Could not import PIL nor Pillow, one of ' \
            'them should be installed'

import nuancier.lib.model
import nuancier.notifications as notifications


class NuancierException(Exception):
    """ Generic Exception object used to throw nuancier specific error.
    """
    pass


class NuancierMultiExceptions(NuancierException):
    """ Generic Exception object used to throw nuancier specific error.
    """

    def __init__(self, messages):  # pragma: no cover
        ''' Instanciate a new NuancierMultiExceptions object. '''
        self.messages = messages


def create_session(db_url, debug=False, pool_recycle=3600):
    """ Create the Session object to use to query the database.

    :arg db_url: URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg debug: a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a Session that can be used to query the database.
    """
    engine = sqlalchemy.create_engine(db_url,
                                      echo=debug,
                                      pool_recycle=pool_recycle)
    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


def get_candidates(session, election_id, approved=None):
    """ Return the candidates for a specified election.

    :arg election_id: the identifier of the election of interest.
    :kwarg approved: a boolean specifying wether to filter the candidates
        for approved or not-approved candidates. If left to default (None),
        no filtering of the approval is performed.
    """
    return nuancier.lib.model.Candidates.by_election(
        session, election_id, approved)


def get_candidate(session, candidate_id):
    """ Return the candidate with the specified identifier.

    :arg candidate_id: the identifier of the candidate of interest.
    """
    return nuancier.lib.model.Candidates.by_id(session, candidate_id)


def get_elections(session):
    """ Return all the elections in the database. """
    return nuancier.lib.model.Elections.all(session)


def get_election(session, election_id):
    """ Return the election corresponding to the provided identifier. """
    return nuancier.lib.model.Elections.by_id(session, election_id)


def get_elections_to_contribute(session):
    """ Return all the election that are open. """
    return nuancier.lib.model.Elections.get_to_contribute(session)


def get_elections_open(session):
    """ Return all the election that are open. """
    return nuancier.lib.model.Elections.get_open(session)


def get_elections_public(session):
    """ Return all the election that are public. """
    return nuancier.lib.model.Elections.get_public(session)


def get_votes_user(session, election_id, username):
    """ Return the votes the specified user casted on the specified election.

    :arg session:
    :arg election_id:
    :arg username:
    """
    return nuancier.lib.model.Votes.by_election_user(
        session, election_id, username)


def get_results(session, election_id):
    """ Return the results for the specified election. """
    return nuancier.lib.model.Candidates.get_results(session, election_id)


def add_election(session, election_name, election_folder, election_year,
                 election_date_start, election_date_end,
                 submission_date_start, election_n_choice,
                 user_n_candidates, election_badge_link=None, user=None):
    """ Add a new election to the database.

    :arg session:
    :arg election_name:
    :arg election_folder:
    :arg election_year:
    :arg election_date_start:
    :arg election_date_end:
    :arg submission_date_start:
    :arg election_n_choice:
    :arg user_n_candidates:
    :kwarg election_badge_link:
    :kwarg user: The user/admin creating the election.
    """
    if not user:
        raise NuancierException('User required to create an election')

    election = nuancier.lib.model.Elections(
        election_name=election_name,
        election_folder=election_folder,
        election_year=election_year,
        election_date_start=election_date_start,
        election_date_end=election_date_end,
        submission_date_start=submission_date_start,
        election_n_choice=election_n_choice,
        user_n_candidates=user_n_candidates,
        election_badge_link=election_badge_link,
    )
    session.add(election)
    session.flush()

    notifications.publish(
        topic='election.new',
        msg=dict(
            agent=user,
            election=election.api_repr(version=1),
        )
    )

    return election


def edit_election(session, election, election_name, election_folder,
                  election_year, election_date_start, election_date_end,
                  submission_date_start, election_n_choice,
                  user_n_candidates, election_badge_link=None, user=None):
    """ Edit an election of the database.

    :arg session:
    :arg election:
    :arg election_name:
    :arg election_folder:
    :arg election_year:
    :arg election_date_start:
    :arg election_date_end:
    :arg submission_date_start:
    :arg election_n_choice:
    :arg user_n_candidates:
    :kwarg election_badge_link:
    :kwarg user:
    """
    if not user:
        raise NuancierException('User required to edit an election')

    edited = []
    if election.election_name != election_name:
        election.election_name = election_name
        edited.append('election name')

    if election.election_folder != election_folder:
        election.election_folder = election_folder
        edited.append('election folder')

    if election.election_year != election_year:
        election.election_year = election_year
        edited.append('election year')

    if election.election_date_start != election_date_start:
        election.election_date_start = election_date_start
        edited.append('election start date')

    if election.election_date_end != election_date_end:
        election.election_date_end = election_date_end
        edited.append('election end date')

    if election.submission_date_start != submission_date_start:
        election.submission_date_start = submission_date_start
        edited.append('submission start date')

    if election.election_n_choice != election_n_choice:
        election.election_n_choice = election_n_choice
        edited.append('election name')

    if election.election_badge_link != election_badge_link:
        election.election_badge_link = election_badge_link
        edited.append('election badge link')

    if election.user_n_candidates != user_n_candidates:
        election.user_n_candidates = user_n_candidates
        edited.append('Number of candidates per user')

    if edited:
        session.add(election)
        session.flush()

    notifications.publish(
        topic='election.update',
        msg=dict(
            agent=user,
            election=election.api_repr(version=1),
            updated=edited,
        )
    )

    return election


def add_candidate(session, candidate_file, candidate_name, candidate_author,
                  candidate_original_url, candidate_license,
                  candidate_submitter, submitter_email,
                  election_id, user=None):
    """ Add a new candidate to the database.

    :arg session: session with which to interact with the database
    :arg candidate_file: the file name of candidate
    :arg candidate_name: the name of candidate
    :arg candidate_author: the name of the author of this candidate
    :arg candidate_original_url: if the artwork originates from
            someone else, this should be a link to the original artwork.
    :arg candidate_license: the license name of candidate
    :arg candidate_submitter: the name of the submitter of this candidate
    :arg submitter_email: the email address of submitter
    :arg election_id: the identifier of the election this candidate is
            candidate for.
    """
    if not user:
        raise NuancierException('User required to add a new candidate')

    candidate = nuancier.lib.model.Candidates.by_election_file(
        session, election_id, candidate_file)
    if candidate:
        raise NuancierException(
            'A candidate with the filename "%s" has already been submitted'
            % (candidate_file)
        )

    candidate = nuancier.lib.model.Candidates(
        candidate_file=candidate_file,
        candidate_name=candidate_name,
        candidate_author=candidate_author,
        candidate_original_url=candidate_original_url,
        candidate_license=candidate_license,
        candidate_submitter=candidate_submitter,
        submitter_email=submitter_email,
        election_id=election_id,
    )
    session.add(candidate)
    session.flush()

    election = nuancier.lib.model.Elections.by_id(session, election_id)

    notifications.publish(
        topic='candidate.new',
        msg=dict(
            agent=user,
            election=election.api_repr(version=1),
            candidate=candidate.api_repr(version=1),
        )
    )


def add_vote(session, candidate_id, username, value=1):
    """ Register the vote of username on candidate.

    :arg session:
    :arg candidate_id:
    :arg username:
    """
    votes = nuancier.lib.model.Votes(
        user_name=username,
        candidate_id=candidate_id,
        value=value,
    )
    session.add(votes)
    session.flush()


def generate_thumbnail(filename, picture_folder, cache_folder,
                       size=(128, 128)):
    """ Generate the thumbnail of the given picture of the picture_folder
    in the cache_folder and at the specified size.

    :arg filename:
    :arg picture_folder:
    :arg cache_folder
    :kwarg size:
    """
    infile = os.path.join(picture_folder, filename)
    outfile = os.path.join(cache_folder, filename)
    try:
        image = Image.open(infile)
        image.thumbnail(size, Image.ANTIALIAS)
        image.save(outfile)
    except (IOError, IndexError) as err:  # pragma: no cover
        print >> sys.stderr, "Cannot create thumbnail", err
        raise NuancierException('Cannot create thumbnail for "%s"' % infile)


def generate_cache(session, election, picture_folder, cache_folder,
                   size=(128, 128)):
    """ Generate the cache of the picture for a given election.
    This function reads all the file in the picture_folder, finds in it the
    file ``infos.txt`` containing for each picture in the folder their name
    and loads this information in the database.
    At the same time, it generate a small thumbnail of the picture into the
    cache folder for faster loading of the overview page.

    The file ``infos.txt`` should have the following layout:

    ::

        filename1    author name1    image name 1
        filename2    author name2    image name 2
        filename3    author name3    image name 3
        ...

    The character delimiting the values is a tabulation (tab, \t).

    :arg session:
    :arg election_id:
    :arg picture_folder:
    :arg cache_folder:
    :kwarg size:
    """
    picture_folder = os.path.join(picture_folder, election.election_folder)

    if not os.path.exists(picture_folder) or not os.path.isdir(picture_folder):
        raise NuancierException(
            'The folder said to contain the pictures of this election (%s) '
            'does not exist or is not a folder' % picture_folder)

    # Check if the cache folder itself exists or is a file
    if os.path.exists(cache_folder) and not os.path.isdir(cache_folder):
        raise NuancierException(
            'Something happened in the creation of the cache folder (%s) '
            'of this election, the path does not lead to a folder'
            % cache_folder)

    cache_folder = os.path.join(cache_folder, election.election_folder)

    # Check if the cache folder *of this election* exists or is a file
    if os.path.exists(cache_folder) and not os.path.isdir(cache_folder):
        raise NuancierException(
            'Something happened in the creation of the cache folder (%s) '
            'of this election, the path does not lead to a folder'
            % cache_folder)

    # Once we checked everything is in place, let's start to do something.
    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)

    candidates = nuancier.lib.model.Candidates.by_election(
        session, election.id)

    exceptions = []
    for candidate in candidates:
        try:
            generate_thumbnail(
                candidate.candidate_file,
                picture_folder,
                cache_folder,
                size)
        except NuancierException, err:  # pragma: no cover
            exceptions.append(err.message)

    if exceptions:  # pragma: no cover
        raise NuancierMultiExceptions(exceptions)


def get_stats(session, election_id):
    """ Return a dictionnary containing a number of statistics for the
    specified election.

    :arg session:
    :arg election_id:
    """
    election = get_election(session, election_id)
    votes = nuancier.lib.model.Votes.cnt_votes(session, election_id)
    voters = nuancier.lib.model.Votes.cnt_voters(session, election_id)
    results = nuancier.lib.model.Votes.by_election(session, election_id)

    # Count the number of votes for each participant
    user_votes = {}
    for vote in results:
        if vote.user_name in user_votes:
            user_votes[vote.user_name] += 1
        else:
            user_votes[vote.user_name] = 1

    # Invert the dictionnary
    votes_user = {}
    for user in user_votes:
        if user_votes[user] in votes_user:
            votes_user[user_votes[user]] += 1
        else:
            votes_user[user_votes[user]] = 1

    data = [[key, votes_user[key]] for key in votes_user]

    # Retrieve the list of authors
    authors = set(
        [cand.candidate_author for cand in election.candidates_approved])

    # Get the distribution of votes per candidate
    election_results = get_results(session, election_id)
    data2 = []
    cnt = 0
    for result in election_results:
        cnt += 1
        data2.append([cnt, int(result[1])])

    return dict(
        votes=votes,
        voters=voters,
        data=data,
        authors=authors,
        data2=data2,
    )


def get_contributions(session, submitter):
    """ Return the list of contributions that have been denied and that
    were made by the specified submitter.

    :arg session:
    :arg submitter:
    """

    return nuancier.lib.model.Candidates.get_by_submitter(
        session, submitter)
