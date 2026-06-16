"""update_type_template_column_for_export_books_table

Revision ID: 2e006f69a525
Revises: cb5789296b60
Create Date: 2026-06-16 18:30:51.170310

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2e006f69a525"
down_revision: str | Sequence[str] | None = "cb5789296b60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("check_template_type", "export_books", type_="check")
    op.alter_column(
        "export_books",
        "template",
        existing_type=sa.VARCHAR(length=40),
        type_=sa.String(length=40),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "export_books",
        "template",
        existing_type=sa.String(length=40),
        type_=sa.VARCHAR(length=40),
        existing_nullable=True,
    )

    op.create_check_constraint(
        "check_template_type", "export_books", 'template IN ("DEFAULT")'
    )
