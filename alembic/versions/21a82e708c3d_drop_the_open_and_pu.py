"""Drop the open and public columns

Revision ID: 21a82e708c3d
Revises: 22da948cbe48
Create Date: 2013-12-01 18:54:49.156762

"""

# revision identifiers, used by Alembic.
revision = '21a82e708c3d'
down_revision = '22da948cbe48'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Drop the open and public column from the Elections table. '''
    op.drop_column('Elections', 'election_open')
    op.drop_column('Elections', 'election_public')


def downgrade():
    ''' Add the open and public column from the Elections table. '''
    op.add_column(
        'Elections',
        sa.Column(
            'election_open',
            sa.Boolean,
            nullable=False,
            default=False
        )
    )
    op.add_column(
        'Elections',
        sa.Column(
            'election_public',
            sa.Boolean,
            nullable=False,
            default=False
        )
    )
