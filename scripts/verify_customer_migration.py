"""Create two NEW isolated MySQL test schemas; never reset/drop any schema."""
import secrets
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COMPOSE=['docker','compose','-f','docker-compose.db-test.yml']


def main():
    suffix=secrets.token_hex(5)
    for scenario in ['empty','legacy']:
        name='techflow_migration_'+scenario+'_'+suffix
        sql=f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL ON `{name}`.* TO 'techflow_test_user'@'%';"
        subprocess.run(COMPOSE+['exec','-T','db-test','sh','-c',
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot'],cwd=ROOT,input=sql,text=True,check=True)
        source='''
import os,secrets
from flask_migrate import upgrade
from sqlalchemy import text,inspect
from werkzeug.security import generate_password_hash
from wsgi import app
from app.extensions import db
assert app.config['APP_ENV']=='testing'
with app.app_context():
    assert db.engine.url.host=='db-test' and db.engine.url.database.startswith('techflow_migration_')
    legacy=SCENARIO=='legacy'
    if legacy:
        upgrade(revision='db55d828848e')
        with db.engine.begin() as conn:
            conn.execute(text("INSERT INTO users(full_name,username,password_hash,role) VALUES('Legacy test','legacy',:hash,'admin')"),{'hash':generate_password_hash(secrets.token_urlsafe(24))})
            uid=conn.scalar(text('SELECT id FROM users LIMIT 1'))
            for status in ['draft','completed','cancelled']:
                conn.execute(text("INSERT INTO sales_orders(order_code,customer_name,customer_phone,customer_email,customer_address,created_by,order_date,status,total_amount,notes) VALUES(:code,'Khach cu','0901234567','old@example.invalid','Old address',:uid,'2025-01-01',:status,1234.56,'Legacy notes')"),dict(code='LEGACY-'+status,uid=uid,status=status))
            conn.execute(text('CREATE TABLE stage1_probe(id INT PRIMARY KEY, value VARCHAR(30))'))
            conn.execute(text("INSERT INTO stage1_probe VALUES(1,'preserve')"))
            before=[tuple(row) for row in conn.execute(text('SELECT * FROM sales_orders ORDER BY id'))]
    upgrade(revision='c051_customers')
    with db.engine.connect() as conn:
        assert conn.scalar(text('SELECT version_num FROM alembic_version'))=='c051_customers'
        assert conn.scalar(text('SELECT COUNT(*) FROM customers'))==0
        if legacy:
            columns=[column['name'] for column in inspect(conn).get_columns('sales_orders') if column['name']!='customer_id']
            after=[tuple(row) for row in conn.execute(text('SELECT '+','.join('`'+c+'`' for c in columns)+' FROM sales_orders ORDER BY id'))]
            assert before==after
            assert conn.scalar(text('SELECT COUNT(*) FROM sales_orders WHERE customer_id IS NOT NULL'))==0
            assert conn.scalar(text('SELECT value FROM stage1_probe WHERE id=1'))=='preserve'
print('Migration SCENARIO passed; new isolated schema retained.')
'''.replace('SCENARIO',repr(scenario),1).replace('Migration SCENARIO','Migration '+scenario)
        subprocess.run(COMPOSE+['run','--rm','--no-deps','-T','-e','MYSQL_DATABASE='+name,'tests','python','-'],
                       cwd=ROOT,input=source,text=True,encoding='utf-8',check=True)
    print('Empty and populated legacy migration checks passed; no schema/volume deleted.')


if __name__=='__main__':main()
