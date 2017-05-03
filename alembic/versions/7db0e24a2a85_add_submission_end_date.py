"""Add Submission end date

Revision ID: 7db0e24a2a85
Revises: 1f1fac3fa4f5
Create Date: 2017-04-09 21:35:06.232452

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '7db0e24a2a85'
down_revision = '1f1fac3fa4f5'


def upgrade():
    """ Add the submission_date_start field to the Elections table. """
    op.add_column(
        'Elections',
        sa.Column(
            'submission_date_end',
            sa.Date)
    )

    try:
        ins = "UPDATE \"Elections\" SET "\
            "submission_date_end=election_date_start;"
        op.execute(ins)
    except Exception, err:
        print 'ERROR', err

    ## Enforce the nullable=False
    op.alter_column(
        'Elections',
        column_name='submission_date_end',
        nullable=False,
        existing_nullable=True,)


def downgrade():
    ''' Drop the columns submission_date_start from the Elections table. '''
    op.drop_column('Elections', 'submission_date_end')
