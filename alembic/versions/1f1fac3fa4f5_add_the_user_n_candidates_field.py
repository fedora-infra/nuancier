"""Add the user_n_candidates field

Revision ID: 1f1fac3fa4f5
Revises: 3d8c307f8f2b
Create Date: 2015-10-09 13:15:31.807680

"""

# revision identifiers, used by Alembic.
revision = '1f1fac3fa4f5'
down_revision = '3d8c307f8f2b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the user_n_candidates column to the Elections table '''
    op.add_column(
        'Elections', sa.Column('user_n_candidates', sa.Integer)
    )


def downgrade():
    ''' Remove the user_n_candidates column from the Elections table. '''
    op.drop_column('Elections', 'user_n_candidates')
