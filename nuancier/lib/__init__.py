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

import os

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    try:
        import Image
    except ImportError:
        print 'Could not import PIL nor Pillow, one of them should '\
              'be installed'

import model

class NuancierException(Exception):
    """ Generic Exception object used to throw nuancier specific error.
    """
    pass


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


def get_candidates(session, election_id):
    """ Return the candidates for a specified election.

    :arg election_id: the identifier of the election of interest.
    """
    return model.Candidates.by_election(session, election_id)


def get_candidate(session, candidate_id):
    """ Return the candidate with the specified identifier.

    :arg candidate_id: the identifier of the candidate of interest.
    """
    return model.Candidates.by_id(session, candidate_id)


def get_elections(session):
    """ Return all the elections in the database. """
    return model.Elections.all(session)


def get_election(session, election_id):
    """ Return the election corresponding to the provided identifier. """
    return model.Elections.by_id(session, election_id)


def get_elections_open(session):
    """ Return all the election that are open. """
    return model.Elections.get_open(session)


def get_elections_public(session):
    """ Return all the election that are public. """
    return model.Elections.get_public(session)


def get_votes_user(session, election_id, username):
    """ Return the votes the specified user casted on the specified election.

    :arg session:
    :arg election_id:
    :arg username:
    """
    return model.Votes.by_election_user(session, election_id, username)


def get_results(session, election_id):
    """ Return the results for the specified election. """
    return model.Candidates.get_results(session, election_id)


def add_election(session, election_name, election_folder, election_year,
                 election_open, election_n_choice):
    """ Add a new election to the database.

    :arg session:
    :arg election_name:
    :arg election_folder:
    :arg election_year:
    :arg election_open:
    :arg election_n_choice:
    """
    election = model.Elections(
        election_name=election_name,
        election_folder=election_folder,
        election_year=election_year,
        election_open=election_open,
        election_n_choice=election_n_choice
    )
    session.add(election)


def add_candidate(session, candidate_file, candidate_name, election_id):
    """ Add a new candidate to the database.

    :arg session:
    :arg candidate_file:
    :arg candidate_name:
    :arg election_id:
    """
    candidate = model.Candidates(
        candidate_file=candidate_file,
        candidate_name=candidate_name,
        election_id=election_id,
    )
    session.add(candidate)


def add_vote(session, candidate_id, username):
    """ Register the vote of username on candidate.

    :arg session:
    :arg candidate_id:
    :arg username:
    """
    votes = model.Votes(
        user_name=username,
        candidate_id=candidate_id,
    )
    session.add(votes)
    

def toggle_open(session, election_id):
    """ Toggle the boolean of the open status for the specified election.
    """
    election = model.Elections.by_id(session, election_id)
    if election.election_open:
        election.election_open = False
        msg = 'Election ended'
    else:
        election.election_open = True
        msg = 'Election opened'
    session.add(election)
    return msg


def toggle_public(session, election_id):
    """ Toggle the boolean of the public status for the specified election.
    """
    election = model.Elections.by_id(session, election_id)
    if election.election_public:
        election.election_public = False
        msg = 'Election closed'
    else:
        election.election_public = True
        msg = 'Election published'
    session.add(election)
    return msg


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
        im = Image.open(infile)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(outfile)
    except IOError:  # pragma: no cover
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

        filename1    image name 1
        filename3    image name 2
        filename2    image name 3
        ...

    The character delimiting the values is a tabulation (tab, \t).

    :arg session:
    :arg election_id:
    :arg picture_folder:
    :arg cache_folder:
    :kwarg size: 
    """
    picture_folder = os.path.join(picture_folder, election.election_folder)
    infos_file = os.path.join(picture_folder, 'infos.txt')

    if not os.path.exists(picture_folder) or not os.path.isdir(picture_folder):
        raise NuancierException(
            'The folder said to contain the pictures of this election (%s) '
            'does not exist or is not a folder' % picture_folder)

    # Check if the cache folder itself is a file
    if os.path.exists(cache_folder) and not os.path.isdir(cache_folder):
        raise NuancierException(
            'Something happened in the creation of the cache folder (%s) '
            'of this election, the path does not lead to a folder'
            % cache_folder)

    cache_folder = os.path.join(cache_folder, election.election_folder)

    # Check if the cache folder of this election is a file
    if os.path.exists(cache_folder) and not os.path.isdir(cache_folder):
        raise NuancierException(
            'Something happened in the creation of the cache folder (%s) '
            'of this election, the path does not lead to a folder'
            % cache_folder)

    # Check is the information file is present
    if not os.path.exists(infos_file) or not os.path.isfile(infos_file):
        raise NuancierException(
            'Something is wrong with the information file ``infos.txt`` for '
            'this election, either it is missing or it is not a file.')

    # Once we checked everything is in place, let's start to do something.
    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)

    stream = open(infos_file)
    infos = stream.readlines()
    stream.close()

    existing_candidates = model.Candidates.by_election(session, election.id)
    existing_candidates = [candidate.candidate_file
                           for candidate in existing_candidates]

    for info in infos:
        info = info.replace('"', '').strip()
        if not '\t' in info:
            raise NuancierException(
            'The information file ``infos.txt`` does not contain a tabulation '
            'on the row: %s.' % info)
        filename, imgname = info.split('\t')
        filename = filename.strip()
        imgname = imgname.strip()
        if filename not in existing_candidates:
            add_candidate(session, filename, imgname, election.id)
        generate_thumbnail(filename, picture_folder, cache_folder, size)

    try:
        session.commit()
    except SQLAlchemyError as err:  # pragma: no cover
        raise NuancierException(err.message)
