"""Add a submission_start_date field

Revision ID: 55f1d066ad4f
Revises: 154f23ea945d
Create Date: 2014-01-08 14:44:10.186368

"""

# revision identifiers, used by Alembic.
revision = '55f1d066ad4f'
down_revision = '154f23ea945d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'Elections',
        sa.Column('submission_date_start',
        sa.Date)
    )

    try:
        ins = "UPDATE \"Elections\" SET submission_date_start=election_date_start;"
        op.execute(ins)
    except Exception, err:
        print 'ERROR', err

    ## Enforce the nullable=False
    op.alter_column(
        'Elections',
        column_name='submission_date_start',
        nullable=False,
        existing_nullable=True,)

def downgrade():
    ''' Remove the columns submission_date_start from the Elections table. '''
    op.drop_column('Elections', 'submission_date_start')
