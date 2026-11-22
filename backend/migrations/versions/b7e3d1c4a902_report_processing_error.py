"""reports.processing_error: plain-language reason a report failed

Also gives reports that already failed a reason, since they were all
placeholder files the old OCR could not open.

Revision ID: b7e3d1c4a902
Revises: a1f4c2e9b7d1
Create Date: 2026-11-22 23:40:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e3d1c4a902'
down_revision: Union[str, None] = 'a1f4c2e9b7d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('processing_error', sa.String(), nullable=True))
    op.execute(
        "UPDATE reports SET processing_error = "
        "'This file could not be read. Upload a clear scan or a real PDF of the report.' "
        "WHERE status = 'error'"
    )


def downgrade() -> None:
    with op.batch_alter_table('reports') as batch:
        batch.drop_column('processing_error')
