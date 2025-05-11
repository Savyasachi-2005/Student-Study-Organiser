"""add notes column to resource table

Revision ID: add_notes_column
Revises: ec939abe2ed1
Create Date: 2025-05-11 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'add_notes_column'
down_revision = 'ec939abe2ed1'
branch_labels = None
depends_on = None


def upgrade():
    # Get database connection
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Check if notes column exists
    columns = [col['name'] for col in inspector.get_columns('resource')]
    
    if 'notes' not in columns:
        # Add notes column to resource table
        op.add_column('resource', sa.Column('notes', sa.Text(), nullable=True))


def downgrade():
    # Get database connection
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Check if notes column exists
    columns = [col['name'] for col in inspector.get_columns('resource')]
    
    if 'notes' in columns:
        # Remove notes column from resource table
        op.drop_column('resource', 'notes') 