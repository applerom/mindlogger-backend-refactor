"""activity item fields fix

Revision ID: 343916a84a24
Revises: 9f910258cf25
Create Date: 2023-03-30 22:31:19.491780

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "343916a84a24"
down_revision = "9f910258cf25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "activity_item_histories",
        sa.Column("name", sa.Text(), nullable=True),
    )
    op.execute("UPDATE activity_item_histories SET name = 'item';")
    op.alter_column("activity_item_histories", "name", nullable=False)

    op.add_column(
        "activity_item_histories",
        sa.Column(
            "response_values",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.drop_column("activity_item_histories", "header_image")
    op.drop_column("activity_item_histories", "skippable_item")
    op.drop_column("activity_item_histories", "remove_availability_to_go_back")
    op.drop_column("activity_item_histories", "answers")
    op.add_column(
        "activity_items",
        sa.Column("name", sa.Text(), nullable=True, default="item"),
    )
    op.execute("UPDATE activity_items SET name = 'item';")
    op.alter_column("activity_items", "name", nullable=False)

    op.add_column(
        "activity_items",
        sa.Column(
            "response_values",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.drop_column("activity_items", "header_image")
    op.drop_column("activity_items", "skippable_item")
    op.drop_column("activity_items", "remove_availability_to_go_back")
    op.drop_column("activity_items", "answers")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "activity_items",
        sa.Column(
            "answers",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "remove_availability_to_go_back",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "skippable_item", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )

    op.add_column(
        "activity_items",
        sa.Column(
            "header_image", sa.TEXT(), autoincrement=False, nullable=True
        ),
    )
    op.drop_column("activity_items", "response_values")
    op.drop_column("activity_items", "name")
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "answers",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "remove_availability_to_go_back",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "skippable_item", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )

    op.add_column(
        "activity_item_histories",
        sa.Column(
            "header_image", sa.TEXT(), autoincrement=False, nullable=True
        ),
    )
    op.drop_column("activity_item_histories", "response_values")
    op.drop_column("activity_item_histories", "name")
    # ### end Alembic commands ###
