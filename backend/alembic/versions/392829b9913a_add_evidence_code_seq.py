"""Add evidence_code_seq

Revision ID: 392829b9913a
Revises: 0001_initial
Create Date: 2026-09-29 05:58:48.946320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '392829b9913a'
down_revision: Union[str, Sequence[str], None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SEQUENCE evidence_code_seq START 1;")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP SEQUENCE evidence_code_seq;")
