"""Add the Vote.value column

Revision ID: 3d8c307f8f2b
Revises: c634e3c9312
Create Date: 2014-09-25 12:42:32.121983

"""

# revision identifiers, used by Alembic.
revision = '3d8c307f8f2b'
down_revision = 'c634e3c9312'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the column value from the Votes table '''
    op.add_column(
        'Votes',
        sa.Column('value', sa.Integer(), nullable=True, default=1)
    )

    # This is required for prod as there is already an election in the DB
    try:
        ins = "UPDATE \"Votes\" SET value=1;"
        op.execute(ins)
    except Exception, err:
        print 'ERROR', err

    ## Enforce the nullable=False
    op.alter_column('Votes', 'value', nullable=False)


def downgrade():
    ''' Drop the column value from the Votes table '''
    op.drop_column('Candidates', 'candidate_original_url')
