"""Add submitter email

Revision ID: c634e3c9312
Revises: 2cbe209b0171
Create Date: 2014-05-12 20:08:13.226721

"""

# revision identifiers, used by Alembic.
revision = 'c634e3c9312'
down_revision = '2cbe209b0171'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the candidate_email field to the Candidates table. '''
    op.add_column(
        'Candidates',
        sa.Column(
            'submitter_email',
            sa.String(255))
    )


def downgrade():
    ''' Remove the columns candidate_email from the Candidates table. '''
    op.drop_column('Candidates', 'submitter_email')
