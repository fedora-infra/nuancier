"""Add candidate license

Revision ID: 154f23ea945d
Revises: 1bd4db428323
Create Date: 2013-12-04 10:49:30.384208

"""

# revision identifiers, used by Alembic.
revision = '154f23ea945d'
down_revision = '1bd4db428323'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the candidate_license field to the Candidates table. '''
    op.add_column(
        'Candidates',
        sa.Column('candidate_license', sa.String(255),
                  default='CC-BY-SA', nullable=False)
    )


def downgrade():
    ''' Drop the candidate_license column from the Candidates table. '''
    op.drop_column('Candidates', 'candidate_license')
