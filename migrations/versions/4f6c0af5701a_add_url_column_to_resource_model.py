"""Add url column to Resource model

Revision ID: 4f6c0af5701a
Revises: add_notes_column
Create Date: 2025-05-12 20:10:13.979189

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f6c0af5701a'
down_revision = 'add_notes_column'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('resource', schema=None) as batch_op:
        batch_op.add_column(sa.Column('url', sa.String(length=255), nullable=False, server_default=sa.text("''")))
        batch_op.alter_column('url', server_default=None)
        batch_op.drop_column('notes')


def downgrade():
    with op.batch_alter_table('resource', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notes', sa.TEXT(), nullable=True))
        batch_op.drop_column('url')
