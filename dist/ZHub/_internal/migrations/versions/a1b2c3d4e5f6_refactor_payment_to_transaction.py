"""Refactor Payment to Transaction module

Revision ID: a1b2c3d4e5f6
Revises: eb299ce35a61
Create Date: 2026-06-03 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'eb299ce35a61'
branch_labels = None
depends_on = None


def upgrade():
    # --- 0. Handle the case where db.create_all() already created a
    #         'transactions' table from the new model definition.
    #         We need to drop it so we can rename 'payments' -> 'transactions'
    #         and preserve existing payment data. ---
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'transactions' in existing_tables and 'payments' in existing_tables:
        # The empty transactions table was auto-created by db.create_all().
        # Drop it so we can rename the real payments table.
        op.drop_table('transactions')
    elif 'transactions' in existing_tables and 'payments' not in existing_tables:
        # payments was already renamed or doesn't exist; the transactions table
        # may already have the right schema. Just ensure enrollment columns exist.
        _ensure_enrollment_columns(conn)
        return

    if 'payments' not in existing_tables:
        # Nothing to migrate
        _ensure_enrollment_columns(conn)
        return

    # --- 1. Rename payments table to transactions and restructure columns ---
    op.rename_table('payments', 'transactions')

    with op.batch_alter_table('transactions', schema=None) as batch_op:
        # Add new columns
        batch_op.add_column(sa.Column('transaction_category', sa.String(20), nullable=False, server_default='Income'))
        batch_op.add_column(sa.Column('expense_type', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('other_expense_description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('enrollment_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('total_amount', sa.Float(), nullable=True))

        # Rename existing columns
        batch_op.alter_column('payment_type', new_column_name='income_type',
                              existing_type=sa.String(20), nullable=True)
        batch_op.alter_column('amount', new_column_name='paid_amount',
                              existing_type=sa.Float(), nullable=False)
        batch_op.alter_column('paid_at', new_column_name='transaction_date',
                              existing_type=sa.DateTime(), nullable=True)

        # Make student_id and course_id nullable (for expense transactions)
        batch_op.alter_column('student_id', existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column('course_id', existing_type=sa.Integer(), nullable=True)

        # Create foreign key for enrollment_id
        batch_op.create_foreign_key('fk_transaction_enrollment', 'enrollments', ['enrollment_id'], ['id'])

    # --- 2. Add financial tracking columns to enrollments ---
    _ensure_enrollment_columns(conn)


def _ensure_enrollment_columns(conn):
    """Add financial tracking columns to enrollments if they don't already exist."""
    inspector = sa.inspect(conn)
    existing_cols = [c['name'] for c in inspector.get_columns('enrollments')]

    with op.batch_alter_table('enrollments', schema=None) as batch_op:
        if 'total_fee' not in existing_cols:
            batch_op.add_column(sa.Column('total_fee', sa.Float(), server_default='0.0', nullable=True))
        if 'total_paid' not in existing_cols:
            batch_op.add_column(sa.Column('total_paid', sa.Float(), server_default='0.0', nullable=True))
        if 'payment_status' not in existing_cols:
            batch_op.add_column(sa.Column('payment_status', sa.String(20), server_default='Unpaid', nullable=True))


def downgrade():
    # --- Reverse enrollment changes ---
    with op.batch_alter_table('enrollments', schema=None) as batch_op:
        batch_op.drop_column('payment_status')
        batch_op.drop_column('total_paid')
        batch_op.drop_column('total_fee')

    # --- Reverse transaction changes ---
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_transaction_enrollment', type_='foreignkey')
        batch_op.drop_column('total_amount')
        batch_op.drop_column('enrollment_id')
        batch_op.drop_column('other_expense_description')
        batch_op.drop_column('expense_type')
        batch_op.drop_column('transaction_category')

        batch_op.alter_column('income_type', new_column_name='payment_type',
                              existing_type=sa.String(20), nullable=False)
        batch_op.alter_column('paid_amount', new_column_name='amount',
                              existing_type=sa.Float(), nullable=False)
        batch_op.alter_column('transaction_date', new_column_name='paid_at',
                              existing_type=sa.DateTime(), nullable=True)

        batch_op.alter_column('student_id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('course_id', existing_type=sa.Integer(), nullable=False)

    op.rename_table('transactions', 'payments')
