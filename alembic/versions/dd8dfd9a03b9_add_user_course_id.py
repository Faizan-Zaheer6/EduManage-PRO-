"""add user course_id

Revision ID: dd8dfd9a03b9
Revises: a380bcf090fb
Create Date: 2026-04-24 14:25:31.426444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd8dfd9a03b9'
down_revision: Union[str, Sequence[str], None] = 'a380bcf090fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS course_id INTEGER")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                  AND table_name = 'users'
                  AND constraint_name = 'fk_users_course_id_courses'
            ) THEN
                ALTER TABLE users
                    ADD CONSTRAINT fk_users_course_id_courses
                    FOREIGN KEY (course_id) REFERENCES courses(id);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_course_id_courses")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS course_id")
