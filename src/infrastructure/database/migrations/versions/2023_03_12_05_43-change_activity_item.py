"""change activity item

Revision ID: 8d675fdfaa1d
Revises: 3a5ae83208e3
Create Date: 2023-03-12 05:43:51.722936

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8d675fdfaa1d"
down_revision = "3a5ae83208e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "activity_item_histories",
        sa.Column("header_image", sa.Text(), nullable=True),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "config", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column("skippable_item", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "remove_availability_to_go_back", sa.Boolean(), nullable=True
        ),
    )
    op.drop_column("activity_item_histories", "color_palette")
    op.drop_column("activity_item_histories", "timer")
    op.drop_column("activity_item_histories", "is_able_to_move_to_previous")
    op.drop_column("activity_item_histories", "is_random")
    op.drop_column("activity_item_histories", "has_score")
    op.drop_column("activity_item_histories", "has_token_value")
    op.drop_column("activity_item_histories", "has_text_response")
    op.drop_column("activity_item_histories", "has_alert")
    op.drop_column("activity_item_histories", "is_skippable")
    op.add_column(
        "activity_items", sa.Column("header_image", sa.Text(), nullable=True)
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "config", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "activity_items",
        sa.Column("skippable_item", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "remove_availability_to_go_back", sa.Boolean(), nullable=True
        ),
    )
    op.drop_column("activity_items", "color_palette")
    op.drop_column("activity_items", "timer")
    op.drop_column("activity_items", "is_able_to_move_to_previous")
    op.drop_column("activity_items", "is_random")
    op.drop_column("activity_items", "has_score")
    op.drop_column("activity_items", "has_token_value")
    op.drop_column("activity_items", "has_text_response")
    op.drop_column("activity_items", "has_alert")
    op.drop_column("activity_items", "is_skippable")
    op.add_column(
        "applet_histories",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.drop_constraint(
        "fk_applet_histories_creator_id_users",
        "applet_histories",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_applet_histories_user_id_users"),
        "applet_histories",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_column("applet_histories", "creator_id")
    op.drop_column("applet_histories", "account_id")
    op.drop_constraint("uq_applets_display_name", "applets", type_="unique")
    op.drop_constraint(
        "fk_applets_creator_id_users", "applets", type_="foreignkey"
    )
    op.drop_column("applets", "creator_id")
    op.drop_column("applets", "account_id")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "applets",
        sa.Column(
            "account_id", postgresql.UUID(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "applets",
        sa.Column(
            "creator_id",
            postgresql.UUID(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_applets_creator_id_users",
        "applets",
        "users",
        ["creator_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_applets_display_name", "applets", ["display_name"]
    )
    op.add_column(
        "applet_histories",
        sa.Column(
            "account_id", postgresql.UUID(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "applet_histories",
        sa.Column(
            "creator_id",
            postgresql.UUID(),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.drop_constraint(
        op.f("fk_applet_histories_user_id_users"),
        "applet_histories",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_applet_histories_creator_id_users",
        "applet_histories",
        "users",
        ["creator_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_column("applet_histories", "user_id")
    op.add_column(
        "activity_items",
        sa.Column(
            "is_skippable", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "has_alert", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "has_text_response",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "has_token_value", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "has_score", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "is_random", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "is_able_to_move_to_previous",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "activity_items",
        sa.Column("timer", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "activity_items",
        sa.Column(
            "color_palette", sa.TEXT(), autoincrement=False, nullable=True
        ),
    )
    op.drop_column("activity_items", "remove_availability_to_go_back")
    op.drop_column("activity_items", "skippable_item")
    op.drop_column("activity_items", "config")
    op.drop_column("activity_items", "header_image")
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "is_skippable", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "has_alert", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "has_text_response",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "has_token_value", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "has_score", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "is_random", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "is_able_to_move_to_previous",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column("timer", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "activity_item_histories",
        sa.Column(
            "color_palette", sa.TEXT(), autoincrement=False, nullable=True
        ),
    )
    op.drop_column("activity_item_histories", "remove_availability_to_go_back")
    op.drop_column("activity_item_histories", "skippable_item")
    op.drop_column("activity_item_histories", "config")
    op.drop_column("activity_item_histories", "header_image")
    # ### end Alembic commands ###
