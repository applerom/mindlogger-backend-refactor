"""add folder

Revision ID: a676d8c9b174
Revises: 89a5b28c52ea
Create Date: 2023-02-09 15:37:51.692675

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a676d8c9b174"
down_revision = "89a5b28c52ea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "folders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=True),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["creator_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "applets", sa.Column("folder_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'applets_folder', "applets", "folders", ["folder_id"], ["id"], ondelete="RESTRICT"
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('applets_folder', "applets", type_="foreignkey")
    op.drop_column("applets", "folder_id")
    op.drop_table("folders")
    # ### end Alembic commands ###