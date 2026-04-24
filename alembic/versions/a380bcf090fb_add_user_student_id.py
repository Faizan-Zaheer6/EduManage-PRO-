"""add user student_id

Revision ID: a380bcf090fb
Revises: 
Create Date: 2026-04-24 14:09:25.254633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a380bcf090fb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # NOTE: this project previously used lightweight auto-migrations at runtime.
    # We use IF NOT EXISTS to make this revision safe on existing databases.
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS student_id INTEGER")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                  AND table_name = 'users'
                  AND constraint_name = 'fk_users_student_id_students'
            ) THEN
                ALTER TABLE users
                    ADD CONSTRAINT fk_users_student_id_students
                    FOREIGN KEY (student_id) REFERENCES students(id);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_student_id_students")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS student_id")
