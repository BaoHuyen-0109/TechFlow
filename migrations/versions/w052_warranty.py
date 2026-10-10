"""Add warranty policies and handling; never infer coverage for legacy sales."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = 'w052_warranty'
down_revision = 'c051_customers'
branch_labels = None
depends_on = None
OPTIONS = dict(mysql_engine='InnoDB', mysql_charset='utf8mb4', mysql_collate='utf8mb4_unicode_ci')


def base():
    return [sa.Column('id', mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))]


def fk(name, table, nullable=False):
    return sa.Column(name, mysql.BIGINT(unsigned=True), sa.ForeignKey(table+'.id', ondelete='RESTRICT'), nullable=nullable)


def upgrade():
    op.add_column('products', sa.Column('warranty_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('products', sa.Column('warranty_months', mysql.INTEGER(unsigned=True)))
    op.add_column('products', sa.Column('warranty_notes', sa.String(2000)))
    op.create_check_constraint('warranty_policy', 'products', '(warranty_enabled = 0 AND warranty_months IS NULL) OR (warranty_enabled = 1 AND warranty_months BETWEEN 1 AND 120)')
    op.add_column('sales_orders', sa.Column('completed_at', sa.DateTime()))
    op.create_table('warranty_coverages', *base(), fk('sale_item_id','sales_order_items'),
        sa.Column('enabled',sa.Boolean(),nullable=False), sa.Column('months',mysql.INTEGER(unsigned=True)),
        sa.Column('notes',sa.String(2000)), sa.Column('starts_on',sa.Date()), sa.Column('expires_on',sa.Date()),
        sa.Column('source',sa.String(20),nullable=False), fk('verified_by','users',True),
        sa.Column('verification_reason',sa.String(1000)), sa.UniqueConstraint('sale_item_id'),
        sa.CheckConstraint("source IN ('sale', 'legacy_verified')",name='valid_source'),
        sa.CheckConstraint('(enabled = 0 AND months IS NULL) OR (enabled = 1 AND months BETWEEN 1 AND 120)',name='policy'),
        sa.CheckConstraint('(starts_on IS NULL AND expires_on IS NULL) OR (starts_on IS NOT NULL AND expires_on >= starts_on)',name='dates'), **OPTIONS)
    op.create_table('warranty_devices', *base(), fk('coverage_id','warranty_coverages'),
        sa.Column('unit_index',mysql.INTEGER(unsigned=True),nullable=False), sa.Column('serial',sa.String(100)),
        sa.UniqueConstraint('serial'),sa.UniqueConstraint('coverage_id','unit_index'),sa.CheckConstraint('unit_index > 0',name='unit_positive'), **OPTIONS)
    op.create_table('warranty_tickets', *base(),
        sa.Column('updated_at',sa.DateTime(),nullable=False,server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ticket_code',sa.String(40),nullable=False), fk('device_id','warranty_devices'),
        sa.Column('open_device_key',mysql.BIGINT(unsigned=True),sa.Computed("CASE WHEN status <> 'returned' THEN device_id ELSE NULL END",persisted=True)),
        fk('customer_id','customers',True),sa.Column('customer_name',sa.String(150),nullable=False),sa.Column('customer_phone',sa.String(30)),
        sa.Column('product_name',sa.String(180),nullable=False),sa.Column('product_sku',sa.String(50),nullable=False),
        fk('created_by','users'),fk('assigned_to','users',True),
        sa.Column('status',sa.String(20),nullable=False,server_default='received'),
        sa.Column('assessment',sa.String(20),nullable=False,server_default='pending'),
        sa.Column('issue',sa.String(2000),nullable=False),sa.Column('inspection_result',sa.String(2000)),sa.Column('rejection_reason',sa.String(1000)),
        sa.Column('received_on',sa.Date(),nullable=False),sa.Column('promised_on',sa.Date()),
        sa.Column('completed_at',sa.DateTime()),sa.Column('returned_at',sa.DateTime()),
        sa.UniqueConstraint('ticket_code'),sa.UniqueConstraint('open_device_key'),
        sa.CheckConstraint("status IN ('received','processing','completed','rejected','returned')",name='valid_status'),
        sa.CheckConstraint("assessment IN ('pending','accepted','rejected')",name='valid_assessment'),
        sa.CheckConstraint("status NOT IN ('completed','returned') OR assessment <> 'pending'",name='assessment_required'),
        sa.CheckConstraint("assessment <> 'rejected' OR rejection_reason IS NOT NULL",name='rejection_reason_required'),
        sa.CheckConstraint('promised_on IS NULL OR promised_on >= received_on',name='promise_date'), **OPTIONS)
    op.create_table('warranty_events', *base(),fk('ticket_id','warranty_tickets'),fk('actor_id','users'),
        sa.Column('action',sa.String(30),nullable=False),sa.Column('from_status',sa.String(20)),
        sa.Column('to_status',sa.String(20),nullable=False),sa.Column('note',sa.String(2000)), **OPTIONS)
    indexes = {'warranty_coverages':['sale_item_id','verified_by','expires_on'],
        'warranty_devices':['coverage_id'],
        'warranty_tickets':['device_id','customer_id','created_by','assigned_to','status','received_on'],
        'warranty_events':['ticket_id','actor_id']}
    for table, fields in indexes.items():
        for field in fields: op.create_index('ix_'+table+'_'+field,table,[field])
    op.create_index('ix_warranty_tickets_scope','warranty_tickets',['created_by','assigned_to','status'])


def downgrade():
    raise RuntimeError('Warranty downgrade discards device/history data and is disabled; use reviewed recovery.')
