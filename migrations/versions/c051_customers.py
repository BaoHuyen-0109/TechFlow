"""Add customers and optional sales linkage; preserve all existing snapshots."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = 'c051_customers'
down_revision = 'db55d828848e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('customers',
        sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('phone', sa.String(16), nullable=False),
        sa.Column('email', sa.String(190)),
        sa.Column('address', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_by', mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_customers'),
        sa.UniqueConstraint('phone', name='uq_customers_phone'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_customers_created_by_users', ondelete='RESTRICT'),
        mysql_engine='InnoDB', mysql_charset='utf8mb4', mysql_collate='utf8mb4_unicode_ci')
    for field in ('name', 'is_active', 'created_by'):
        op.create_index('ix_customers_'+field, 'customers', [field])
    op.add_column('sales_orders', sa.Column('customer_id', mysql.BIGINT(unsigned=True), nullable=True))
    op.create_index('ix_sales_orders_customer_id', 'sales_orders', ['customer_id'])
    op.create_foreign_key('fk_sales_orders_customer_id_customers', 'sales_orders', 'customers',
                          ['customer_id'], ['id'], ondelete='RESTRICT')
    op.create_index('ix_sales_orders_customer_status_date', 'sales_orders', ['customer_id','status','order_date'])


def downgrade():
    # Do not discard customer records/links on an accidental app rollback.
    raise RuntimeError('Customer downgrade is destructive and disabled; use a reviewed recovery plan.')
