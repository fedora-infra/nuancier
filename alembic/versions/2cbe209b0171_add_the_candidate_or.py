"""Add the candidate_original_url field

Revision ID: 2cbe209b0171
Revises: 55f1d066ad4f
Create Date: 2014-01-08 18:27:58.864497

"""

# revision identifiers, used by Alembic.
revision = '2cbe209b0171'
down_revision = '55f1d066ad4f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the column candidate_original_url from the Candidates table '''
    op.add_column(
        'Candidates',
        sa.Column('candidate_original_url', sa.String(255), nullable=True)
    )


def downgrade():
    ''' Drop the column candidate_original_url from the Candidates table '''
    op.drop_column('Candidates', 'candidate_original_url')
