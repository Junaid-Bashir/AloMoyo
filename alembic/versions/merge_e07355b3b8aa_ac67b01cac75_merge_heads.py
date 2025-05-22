"""merge heads

Revision ID: merge_e07355b3b8aa_ac67b01cac75
Revises: e07355b3b8aa, ac67b01cac75
Create Date: 2025-05-21 20:30:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "merge_e07355b3b8aa_ac67b01cac75"
down_revision = ("e07355b3b8aa", "ac67b01cac75")
branch_labels = None
depends_on = None

def upgrade():
    """Unify the two heads into one linear history – no schema changes."""
    pass

def downgrade():
    """This merge only affects history; no schema rollback."""
    pass
