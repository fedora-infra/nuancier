"""Add the approve column to Candidates

Revision ID: 1bd4db428323
Revises: 21a82e708c3d
Create Date: 2013-12-03 16:06:36.038441

"""

# revision identifiers, used by Alembic.
revision = '1bd4db428323'
down_revision = '21a82e708c3d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the approved column to the Candidates table. '''
    op.add_column(
        'Candidates',
        sa.Column('approved', sa.Boolean, default=False, nullable=False)
    )
    op.add_column(
        'Candidates',
        sa.Column('approved_motif', sa.Text)
    )


def downgrade():
    ''' Drop the approved column from the Candidates table. '''
    op.drop_column('Candidates', 'approved')
    op.drop_column('Candidates', 'approved_motif')
