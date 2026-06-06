"""make users.email nullable to allow student accounts without email

Revision ID: d4e91b2c3f05
Revises: c3f8a1d92e04
Create Date: 2026-06-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4e91b2c3f05'
down_revision = 'eb299ce35a61'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'email',
            existing_type=sa.String(length=150),
            nullable=True,
        )


def downgrade():
    # Before reverting, ensure no NULL emails exist or this will fail
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'email',
            existing_type=sa.String(length=150),
            nullable=False,
        )
