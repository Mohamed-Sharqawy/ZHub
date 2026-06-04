"""rename received_by to recorded_by in transactions

Revision ID: 79cf9de5d107
Revises: dfebdfd0c835
Create Date: 2026-06-04 03:16:03.414721

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79cf9de5d107'
down_revision = 'dfebdfd0c835'
branch_labels = None
depends_on = None


def upgrade():
    # Rename received_by to recorded_by to match the Transaction model
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('received_by', new_column_name='recorded_by',
                              existing_type=sa.Integer(), nullable=True)


def downgrade():
    # Reverse the rename
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('recorded_by', new_column_name='received_by',
                              existing_type=sa.Integer(), nullable=True)
