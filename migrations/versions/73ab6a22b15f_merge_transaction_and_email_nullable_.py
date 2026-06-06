"""merge transaction and email nullable migrations

Revision ID: 73ab6a22b15f
Revises: 79cf9de5d107, d4e91b2c3f05
Create Date: 2026-06-06 02:54:22.913250

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73ab6a22b15f'
down_revision = ('79cf9de5d107', 'd4e91b2c3f05')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
