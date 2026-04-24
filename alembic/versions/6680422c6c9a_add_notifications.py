"""add notifications

Revision ID: 6680422c6c9a
Revises: dd8dfd9a03b9
Create Date: 2026-04-24 14:30:53.765253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6680422c6c9a'
down_revision: Union[str, Sequence[str], None] = 'dd8dfd9a03b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title VARCHAR NOT NULL,
            body TEXT,
            created_at TIMESTAMP,
            read_at TIMESTAMP
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_read_at ON notifications (read_at)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS notifications")
