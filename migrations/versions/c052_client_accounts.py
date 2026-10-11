"""Add self-service client accounts while preserving existing staff/admin data."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "c052_clients"
down_revision = "w052_guards"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(op.f("ck_users_valid_role"), "users", type_="check")
    op.create_check_constraint("valid_role", "users", "role IN ('admin', 'staff', 'client')")
    op.add_column("customers", sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=True))
    op.create_unique_constraint("user_id", "customers", ["user_id"])
    op.create_foreign_key("user_id", "customers", "users", ["user_id"], ["id"], ondelete="RESTRICT")


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM users WHERE role = 'client' LIMIT 1")).first():
        raise RuntimeError("Client accounts exist; retain the client role and use a reviewed data migration.")
    op.drop_constraint(op.f("fk_customers_user_id_users"), "customers", type_="foreignkey")
    op.drop_constraint(op.f("uq_customers_user_id"), "customers", type_="unique")
    op.drop_column("customers", "user_id")
    op.drop_constraint(op.f("ck_users_valid_role"), "users", type_="check")
    op.create_check_constraint("valid_role", "users", "role IN ('admin', 'staff')")
