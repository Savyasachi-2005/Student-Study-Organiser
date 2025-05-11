"""Add multiple URLs support

Revision ID: multiple_urls_support
Revises: 82da03f1fb62
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'multiple_urls_support'
down_revision = '82da03f1fb62'
branch_labels = None
depends_on = None


def upgrade():
    # op.create_table('resource_url',
    #     sa.Column('id', sa.Integer(), nullable=False),
    #     sa.Column('url', sa.String(length=255), nullable=False),
    #     sa.Column('is_primary', sa.Boolean(), default=False),
    #     sa.Column('resource_id', sa.Integer(), nullable=False),
    #     sa.Column('date_added', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    #     sa.ForeignKeyConstraint(['resource_id'], ['resource.id'], ),
    #     sa.PrimaryKeyConstraint('id')
    # )
    pass

    # Migrate existing URLs to the new table
    connection = op.get_bind()
    resources = connection.execute(sa.text('SELECT id, url FROM resource')).fetchall()
    for resource in resources:
        connection.execute(
            sa.text('INSERT INTO resource_url (url, is_primary, resource_id) VALUES (?, ?, ?)'),
            (resource[1], True, resource[0])
        )

    # Remove url column from resource table
    with op.batch_alter_table('resource') as batch_op:
        batch_op.drop_column('url')


def downgrade():
    # Add back url column to resource table
    with op.batch_alter_table('resource') as batch_op:
        batch_op.add_column(sa.Column('url', sa.String(length=255), nullable=True))

    # Migrate primary URLs back to resource table
    connection = op.get_bind()
    urls = connection.execute('SELECT resource_id, url FROM resource_url WHERE is_primary = 1').fetchall()
    for url in urls:
        connection.execute(
            'UPDATE resource SET url = ? WHERE id = ?',
            (url[1], url[0])
        )

    # Drop ResourceURL table
    op.drop_table('resource_url') 