"""add assign_type to ICE_CUBE_RECON_STRS

Revision ID: 00246fc934bf
Revises: 13486c0dae22
Create Date: 2026-04-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00246fc934bf'
down_revision: Union[str, None] = '13486c0dae22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ASSIGN_TYPE column to ICE_CUBE_RECON_STRS."""
    op.add_column(
        'ICE_CUBE_RECON_STRS',
        sa.Column('ASSIGN_TYPE', sa.String(10), nullable=True),
    )


def downgrade() -> None:
    """Remove ASSIGN_TYPE column from ICE_CUBE_RECON_STRS."""
    op.drop_column('ICE_CUBE_RECON_STRS', 'ASSIGN_TYPE')
