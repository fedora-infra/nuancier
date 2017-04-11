"""Add allow_updating field

Revision ID: 9262dc2af69d
Revises: 7db0e24a2a85
Create Date: 2017-04-11 13:50:35.179230

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9262dc2af69d'
down_revision = '7db0e24a2a85'


def upgrade():
    """ Add the allows_updating field to the Elections table. """
    op.add_column(
        'Elections',
        sa.Column(
            'allows_updating',
            sa.Boolean, default=True, nullable=True)
    )

    try:
        ins = "UPDATE \"Elections\" SET "\
            "allows_updating=True;"
        op.execute(ins)
    except Exception, err:
        print 'ERROR', err

    ## Enforce the nullable=False
    op.alter_column(
        'Elections',
        column_name='allows_updating',
        nullable=False,
        existing_nullable=True,)


def downgrade():
    ''' Drop the columns allows_updating from the Elections table. '''
    op.drop_column('Elections', 'allows_updating')
