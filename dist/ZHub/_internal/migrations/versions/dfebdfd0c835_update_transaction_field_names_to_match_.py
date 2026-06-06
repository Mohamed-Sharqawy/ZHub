"""update transaction field names to match new model

Revision ID: dfebdfd0c835
Revises: a1b2c3d4e5f6
Create Date: 2026-06-04 02:58:29.450595

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dfebdfd0c835'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        # Rename columns to match new model field names
        batch_op.alter_column('transaction_category', new_column_name='transaction_kind',
                              existing_type=sa.String(20), nullable=False)
        batch_op.alter_column('income_type', new_column_name='payment_type',
                              existing_type=sa.String(20), nullable=True)
        batch_op.alter_column('expense_type', new_column_name='expense_category',
                              existing_type=sa.String(50), nullable=True)
        batch_op.alter_column('other_expense_description', new_column_name='expense_description',
                              existing_type=sa.Text(), nullable=True)
        batch_op.alter_column('transaction_date', new_column_name='date',
                              existing_type=sa.DateTime(), nullable=True)

        # Add the new 'amount' column (common field for both income and expenses)
        batch_op.add_column(sa.Column('amount', sa.Float(), nullable=True))

        # Drop the enrollment_id column (no longer in the new model)
        if 'enrollment_id' in [c['name'] for c in sa.inspect(op.get_bind()).get_columns('transactions')]:
            batch_op.drop_constraint('fk_transaction_enrollment', type_='foreignkey')
            batch_op.drop_column('enrollment_id')

    # Update the amount column with data from paid_amount for existing records
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE transactions SET amount = paid_amount WHERE amount IS NULL"))

    # Make amount column not nullable after updating data
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('amount', existing_type=sa.Float(), nullable=False)


def downgrade():
    # Reverse the changes
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        # Make amount nullable again
        batch_op.alter_column('amount', existing_type=sa.Float(), nullable=True)

        batch_op.alter_column('transaction_kind', new_column_name='transaction_category',
                              existing_type=sa.String(20), nullable=False)
        batch_op.alter_column('payment_type', new_column_name='income_type',
                              existing_type=sa.String(20), nullable=True)
        batch_op.alter_column('expense_category', new_column_name='expense_type',
                              existing_type=sa.String(50), nullable=True)
        batch_op.alter_column('expense_description', new_column_name='other_expense_description',
                              existing_type=sa.Text(), nullable=True)
        batch_op.alter_column('date', new_column_name='transaction_date',
                              existing_type=sa.DateTime(), nullable=True)

        # Add back enrollment_id column and foreign key
        batch_op.add_column(sa.Column('enrollment_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_transaction_enrollment', 'enrollments', ['enrollment_id'], ['id'])

        # Drop the amount column
        batch_op.drop_column('amount')
