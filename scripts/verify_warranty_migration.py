"""Empty/legacy upgrade in NEW MySQL schemas. Never drop/reset a database."""
import secrets
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COMPOSE=['docker','compose','-f','docker-compose.db-test.yml']
SOURCE=r'''
import hashlib,json,secrets
from flask_migrate import upgrade
from sqlalchemy import text,inspect
from werkzeug.security import generate_password_hash
from wsgi import app
from app.extensions import db
assert app.config['APP_ENV']=='testing'
with app.app_context():
    assert db.engine.url.host=='db-test' and db.engine.url.database.startswith('techflow_migration_warranty_')
    if LEGACY:
        upgrade(revision='c051_customers')
        with db.engine.begin() as conn:
            conn.execute(text("INSERT INTO users(full_name,username,password_hash,role) VALUES('Legacy test','legacy',:hash,'admin')"),{'hash':generate_password_hash(secrets.token_urlsafe(24))})
            conn.execute(text("INSERT INTO categories(code,name) VALUES('OLD','Old category')"))
            conn.execute(text("INSERT INTO products(sku,name,category_id,purchase_price,selling_price,stock_quantity) VALUES('OLD','Old product',1,1234.56,2345.67,7)"))
            conn.execute(text("INSERT INTO customers(name,phone,created_by) VALUES('Legacy customer','+84901234567',1)"))
            for status in ['draft','completed','cancelled']:
                conn.execute(text("INSERT INTO sales_orders(order_code,customer_name,customer_phone,customer_id,created_by,order_date,status,total_amount,notes) VALUES(:code,'Old snapshot','0901234567',:customer,1,'2025-01-31',:status,2345.67,'Private old note')"),dict(code='OLD-'+status,customer=1 if status=='completed' else None,status=status))
                oid=conn.scalar(text('SELECT LAST_INSERT_ID()'))
                conn.execute(text('INSERT INTO sales_order_items(order_id,product_id,quantity,unit_price,line_total) VALUES(:oid,1,1,2345.67,2345.67)'),dict(oid=oid))
            conn.execute(text("INSERT INTO stock_movements(product_id,quantity_delta,movement_type,reference_type,reference_id,created_by) VALUES(1,-1,'sale_out','sales_order',2,1)"))
            conn.execute(text('CREATE TABLE stage1_probe(id INT PRIMARY KEY, value VARCHAR(30))'))
            conn.execute(text("INSERT INTO stage1_probe VALUES(1,'preserve')"))
            tables=[t for t in inspect(conn).get_table_names() if t!='alembic_version']
            columns={t:[c['name'] for c in inspect(conn).get_columns(t)] for t in tables}
            def fingerprint(conn,t):
                rows=[list(r) for r in conn.execute(text('SELECT '+','.join('`'+c+'`' for c in columns[t])+' FROM `'+t+'` ORDER BY 1'))]
                return hashlib.sha256(json.dumps(rows,default=str).encode()).hexdigest()
            before={t:fingerprint(conn,t) for t in tables}
    upgrade()
    with db.engine.connect() as conn:
        assert conn.scalar(text('SELECT version_num FROM alembic_version'))=='w052_guards'
        for table in ['warranty_coverages','warranty_devices','warranty_tickets','warranty_events']:
            assert conn.scalar(text('SELECT COUNT(*) FROM '+table))==0
        if LEGACY:
            assert before=={t:fingerprint(conn,t) for t in tables}
            assert conn.scalar(text('SELECT COUNT(*) FROM sales_orders WHERE completed_at IS NOT NULL'))==0
            assert conn.scalar(text('SELECT COUNT(*) FROM products WHERE warranty_enabled<>0 OR warranty_months IS NOT NULL'))==0
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from app.migration_policy import include_object
    with db.engine.connect() as conn:
        assert compare_metadata(MigrationContext.configure(conn,opts={'include_object':include_object}),db.metadata)==[]
print('Warranty migration passed; all original columns/rows preserved. Schema retained.')
'''


def main():
    for legacy in [False,True]:
        name='techflow_migration_warranty_'+('legacy_' if legacy else 'empty_')+secrets.token_hex(5)
        sql=f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL ON `{name}`.* TO 'techflow_test_user'@'%';"
        subprocess.run(COMPOSE+['exec','-T','db-test','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot'],cwd=ROOT,input=sql,text=True,check=True)
        subprocess.run(COMPOSE+['run','--rm','--no-deps','-T','-e','MYSQL_DATABASE='+name,'tests','python','-'],cwd=ROOT,
            input=SOURCE.replace('LEGACY',repr(legacy)),text=True,encoding='utf-8',check=True)
    print('Empty and populated legacy MySQL warranty migrations verified.')


if __name__=='__main__':main()
