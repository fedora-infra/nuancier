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
Mapping of python classes to Database Tables.
'''

## Ignore warning about pkg_resources, it does help us
# pylint: disable=W0611
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import datetime
import logging

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import relation

BASE = declarative_base()


## Some of our methods have too many arguments
# pylint: disable=R0913
## We use id for the identifier in our db but that's too short
# pylint: disable=C0103
## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101


def create_tables(db_url, alembic_ini=None, debug=False):
    """ Create the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
        information with regards to the database engine, the host to
        connect to, the user and password and the database name.
          ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg alembic_ini, path to the alembic ini file. This is necessary
        to be able to use alembic correctly, but not for the unit-tests.
    :kwarg debug, a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a session that can be used to query the database.

    """
    engine = create_engine(db_url, echo=debug)
    BASE.metadata.create_all(engine)

    if alembic_ini is not None:  # pragma: no cover
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:

        ## Ignore the warning missing alembic
        # pylint: disable=F0401
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


class Elections(BASE):
    '''This table lists all the elections available.

    Table -- Elections
    '''

    __tablename__ = 'Elections'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    election_name = sa.Column(sa.String(255), nullable=False, unique=True)
    election_folder = sa.Column(sa.String(50), nullable=False, unique=True)
    election_year = sa.Column(sa.Integer, nullable=False)
    election_n_choice = sa.Column(sa.Integer, nullable=False)
    election_badge_link = sa.Column(sa.String(255), default=None)
    election_date_start = sa.Column(sa.Date, nullable=False)
    election_date_end = sa.Column(sa.Date, nullable=False)
    submission_date_start = sa.Column(sa.Date, nullable=False)
    submission_date_end = sa.Column(sa.Date, nullable=False)
    user_n_candidates = sa.Column(sa.Integer, nullable=True)

    date_created = sa.Column(sa.DateTime, nullable=False,
                             default=sa.func.current_timestamp())
    date_updated = sa.Column(sa.DateTime, nullable=False,
                             default=sa.func.current_timestamp(),
                             onupdate=sa.func.current_timestamp())

    @property
    def submission_open(self):
        ''' Returns if this election is opened for contribution or not. '''
        today = datetime.datetime.utcnow().date()
        return (self.submission_date_start <= today
                and self.submission_date_end > today
                and self.election_date_start > today
                and self.election_date_end >= today)

    @property
    def election_open(self):
        ''' Return if this election is opened or not. '''
        today = datetime.datetime.utcnow().date()
        return (self.submission_date_start <= today
                and self.submission_date_end <= today
                and self.election_date_start <= today
                and self.election_date_end > today)

    @property
    def election_public(self):
        ''' Return if this election is public or not.
        Public here means that the results are accessible to anyone.
        '''
        today = datetime.datetime.utcnow().date()
        return (self.submission_date_start <= today
                and self.submission_date_end <= today
                and self.election_date_start <= today
                and self.election_date_end <= today)

    @property
    def candidates_approved(self):
        ''' Return the approved candidates for this elections. '''
        return [cand for cand in self.candidates if cand.approved]

    def __repr__(self):
        return 'Elections(id:%r, name:%r, year:%r)' % (
            self.id, self.election_name, self.election_year)

    def api_repr(self, version):
        """ Used by fedmsg to serialize Elections in messages. """
        if version == 1:
            return dict(
                id=self.id,
                name=self.election_name,
                year=self.election_year,
                date_start=self.election_date_start,
                date_end=self.election_date_end,
                submission_date_start=self.submission_date_start,
                submission_date_end=self.submission_date_end,
            )
        else:  # pragma: no cover
            raise NotImplementedError("Unsupported version %r" % version)

    @classmethod
    def all(cls, session):
        """ Return all the entries in the elections table.
        """
        return session.query(
            cls
        ).order_by(
            Elections.election_date_end.desc()
        ).all()

    @classmethod
    def by_id(cls, session, election_id):
        """ Return the election corresponding to the provided identifier.
        """
        return session.query(cls).get(election_id)

    @classmethod
    def get_open(cls, session):
        """ Return all the election open to votes.
        """
        today = datetime.datetime.utcnow().date()
        return session.query(
            cls
        ).filter(
            Elections.submission_date_start < today
        ).filter(
            Elections.submission_date_end <= today
        ).filter(
            Elections.election_date_start <= today
        ).filter(
            Elections.election_date_end >= today
        ).order_by(
            Elections.election_year.desc()
        ).all()

    @classmethod
    def get_public(cls, session):
        """ Return all the election public.
        """
        today = datetime.datetime.utcnow().date()
        return session.query(
            cls
        ).filter(
            Elections.election_date_end <= today
        ).order_by(
            Elections.election_year.desc()
        ).all()

    @classmethod
    def get_to_contribute(cls, session):
        """ Return all the election public.
        """
        today = datetime.datetime.utcnow().date()
        return session.query(
            cls
        ).filter(
            Elections.submission_date_start <= today
        ).filter(
            Elections.submission_date_end > today
        ).filter(
            Elections.election_date_start > today
        ).order_by(
            Elections.election_year.desc()
        ).all()


class Candidates(BASE):
    ''' This table lists the candidates for the elections.

    Table -- Candidates
    '''

    __tablename__ = 'Candidates'
    id = sa.Column(sa.Integer, nullable=False, primary_key=True)
    candidate_file = sa.Column(sa.String(255), nullable=False)
    candidate_name = sa.Column(sa.String(255), nullable=False)
    candidate_author = sa.Column(sa.String(255), nullable=False)
    candidate_original_url = sa.Column(sa.String(255), nullable=True)
    candidate_license = sa.Column(sa.String(255), nullable=False)
    candidate_submitter = sa.Column(sa.String(255), nullable=False)
    submitter_email = sa.Column(sa.String(255), nullable=False)
    election_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('Elections.id',
                      ondelete='CASCADE',
                      onupdate='CASCADE'
                      ),
        nullable=False,
    )
    approved = sa.Column(sa.Boolean, default=False, nullable=False)
    approved_motif = sa.Column(sa.Text, nullable=True)

    date_created = sa.Column(sa.DateTime, nullable=False,
                             default=sa.func.current_timestamp())
    date_updated = sa.Column(sa.DateTime, nullable=False,
                             default=sa.func.current_timestamp(),
                             onupdate=sa.func.current_timestamp())

    election = relation('Elections', backref='candidates')
    __table_args__ = (
        sa.UniqueConstraint('election_id', 'candidate_file'),
    )

    @property
    def denied(self):
        """ Return a boolean specifying if the candidate has been denied or
        is either Approved or Pending Review.
        """
        return bool(not self.approved and self.approved_motif)

    def __repr__(self):
        return 'Candidates(file:%r, name:%r, election_id:%r, created:%r' % (
            self.candidate_file, self.candidate_name, self.election_id,
            self.date_created)

    def api_repr(self, version):
        """ Used by fedmsg to serialize Packages in messages. """
        if version == 1:
            return dict(
                name=self.candidate_name,
                author=self.candidate_author,
                original_url=self.candidate_original_url,
                license=self.candidate_license,
                submitter=self.candidate_submitter,
            )
        else:  # pragma: no cover
            raise NotImplementedError("Unsupported version %r" % version)

    @classmethod
    def by_id(cls, session, candidate_id):
        """ Return the election corresponding to the provided identifier.
        """
        return session.query(cls).get(candidate_id)

    @classmethod
    def by_election(cls, session, election_id, approved=None):
        """ Return the candidate associated to the given election
        identifier. Filter them if they are approved or not for the
        election.

        """
        query = session.query(
            cls
        ).filter(
            Candidates.election_id == election_id
        )

        if approved is not None:
            query = query.filter(
                Candidates.approved == approved
            )

        query = query.order_by(Candidates.date_created)

        return query.all()

    @classmethod
    def by_election_file(
            cls, session, election_id, filename,):
        """ Return the candidate associated to the given election
        identifier and having the specified filename.

        """
        query = session.query(
            cls
        ).filter(
            Candidates.election_id == election_id
        ).filter(
            Candidates.candidate_file == filename
        )

        return query.first()

    @classmethod
    def get_results(cls, session, election_id):
        """ Return the candidate of a given election ranked by the number
        of vote each received.

        """
        query = session.query(
            Candidates,
            sa.func.sum(Votes.value).label('votes')
        ).filter(
            Candidates.election_id == election_id
        ).filter(
            Candidates.id == Votes.candidate_id
        ).group_by(
            Candidates.id,
            Candidates.candidate_file,
            Candidates.candidate_name,
            Candidates.candidate_author,
            Candidates.candidate_original_url,
            Candidates.candidate_license,
            Candidates.candidate_submitter,
            Candidates.submitter_email,
            Candidates.election_id,
            Candidates.approved,
            Candidates.approved_motif,
            Candidates.date_created,
            Candidates.date_updated
        ).order_by(
            'votes DESC'
        )
        return query.all()

    @classmethod
    def get_by_submitter(cls, session, submitter, election_id=None):
        """ Return the list of denied submission of the specified submitter

        """

        query = session.query(
            Candidates
        ).filter(
            Candidates.candidate_submitter == submitter
        ).order_by(
            Candidates.date_updated.desc()
        )

        if election_id:
            query = query.filter(
                Candidates.election_id == election_id
            )

        return query.all()


class Votes(BASE):
    ''' This table lists the results of the elections

    Table -- Votes
    '''

    __tablename__ = 'Votes'
    user_name = sa.Column(sa.String(50), nullable=False, primary_key=True)
    candidate_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('Candidates.id',
                      onupdate='CASCADE'
                      ),
        nullable=False,
        primary_key=True
    )
    value = sa.Column(sa.Integer, nullable=False, default=True)

    date_created = sa.Column(sa.DateTime, nullable=False,
                             default=sa.func.current_timestamp())
    date_updated = sa.Column(sa.DateTime, nullable=False,
                             default=sa.func.current_timestamp(),
                             onupdate=sa.func.current_timestamp())

    def __init__(self, user_name, candidate_id, value=1):
        """ Constructor

        :arg name: the name of the user who voted
        :arg candidate_id: the identifier of the candidate that the user
            voted for.
        """
        self.user_name = user_name
        self.candidate_id = candidate_id
        self.value = value

    def __repr__(self):
        return 'Votes(name:%r, candidate_id:%r, created:%r' % (
            self.user_name, self.candidate_id, self.date_created)

    @classmethod
    def cnt_votes(cls, session, election_id,):
        """ Return the votes on the specified election.

        :arg session:
        :arg election_id:
        """
        return session.query(
            sa.func.sum(cls.value)
        ).filter(
            Votes.candidate_id == Candidates.id
        ).filter(
            Candidates.election_id == election_id
        ).first()[0]

    @classmethod
    def cnt_voters(cls, session, election_id,):
        """ Return the votes on the specified election.

        :arg session:
        :arg election_id:
        """
        return session.query(
            sa.func.distinct(cls.user_name)
        ).filter(
            Votes.candidate_id == Candidates.id
        ).filter(
            Candidates.election_id == election_id
        ).count()

    @classmethod
    def by_election(cls, session, election_id):
        """ Return the votes on the specified election.

        :arg session:
        :arg election_id:
        """
        return session.query(
            cls
        ).filter(
            Votes.candidate_id == Candidates.id
        ).filter(
            Candidates.election_id == election_id
        ).all()

    @classmethod
    def by_election_user(cls, session, election_id, username):
        """ Return the votes the specified user casted on the specified
        election.

        :arg session:
        :arg election_id:
        :arg username:
        """
        return session.query(
            cls
        ).filter(
            Votes.candidate_id == Candidates.id
        ).filter(
            Candidates.election_id == election_id
        ).filter(
            Votes.user_name == username
        ).order_by(
            Votes.candidate_id
        ).all()
