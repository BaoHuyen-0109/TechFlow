"""Read-only comparison of original demo rows after the additive migration."""
import json
import subprocess
from pathlib import Path
from verify_demo_integrity import ROOT,SOURCE


def main():
    baseline=json.loads((ROOT/'.docker-local/stage51-before.json').read_text(encoding='utf-8'))
    source=SOURCE.replace("tables = sorted(conn.execute(text('SHOW TABLES')).scalars())",
        "tables = sorted(conn.execute(text('SHOW TABLES')).scalars())\n    assert conn.scalar(text('SELECT version_num FROM alembic_version')) == 'c051_customers'\n    assert conn.scalar(text('SELECT COUNT(*) FROM customers')) == 0\n    tables = [t for t in tables if t not in ('customers','alembic_version')]")
    source=source.replace("'SELECT * FROM `'+table+'` ORDER BY 1'",
        "'SELECT '+(','.join('`'+r[0]+'`' for r in conn.execute(text('SHOW COLUMNS FROM sales_orders')) if r[0]!='customer_id') if table=='sales_orders' else '*')+' FROM `'+table+'` ORDER BY 1'")
    current=json.loads(subprocess.check_output(['docker','compose','exec','-T','web','python','-'],
        cwd=ROOT,input=source,text=True,encoding='utf-8'))
    expected={key:value for key,value in baseline.items() if key!='alembic_version'}
    assert current==expected,'Original demo rows changed; investigate before proceeding.'
    print('All original demo business/probe rows unchanged; only new schema and Alembic revision added. Customers empty.')


if __name__=='__main__':main()
