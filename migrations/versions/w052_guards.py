"""Enforce non-NULL terms in MySQL CHECK expressions (UNKNOWN otherwise passes)."""
from alembic import op

revision='w052_guards'
down_revision='w052_warranty'
branch_labels=None
depends_on=None


def upgrade():
    for table,name,expression in [
        ('products','warranty_policy','(warranty_enabled = 0 AND warranty_months IS NULL) OR (warranty_enabled = 1 AND warranty_months IS NOT NULL AND warranty_months BETWEEN 1 AND 120)'),
        ('warranty_coverages','policy','(enabled = 0 AND months IS NULL) OR (enabled = 1 AND months IS NOT NULL AND months BETWEEN 1 AND 120)'),
        ('warranty_coverages','dates','(starts_on IS NULL AND expires_on IS NULL) OR (starts_on IS NOT NULL AND expires_on IS NOT NULL AND expires_on >= starts_on)')]:
        op.drop_constraint(op.f('ck_'+table+'_'+name),table,type_='check')
        op.create_check_constraint(name,table,expression)


def downgrade():
    raise RuntimeError('Warranty constraints must not be weakened by an accidental downgrade.')
