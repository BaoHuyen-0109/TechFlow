"""Read-only demo dump + restore verification in a NEW db-test schema.

Never restores to demo, never drops schemas/volumes, never prints dump contents.
"""
import hashlib
import json
import secrets
import subprocess
from datetime import datetime,timezone
from pathlib import Path
from verify_demo_integrity import SOURCE

ROOT=Path(__file__).resolve().parents[1]
TEST=['docker','compose','-f','docker-compose.db-test.yml']


def main():
    target=ROOT/'.docker-local/backups'/('stage51-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(3)+'.sql')
    target.parent.mkdir(parents=True,exist_ok=True)
    baseline=json.loads(subprocess.check_output(['docker','compose','exec','-T','web','python','-'],cwd=ROOT,input=SOURCE,text=True,encoding='utf-8'))
    assert 'customers' not in baseline,'This helper expects the pre-customer schema.'
    command='MYSQL_PWD="$MYSQL_PASSWORD" mysqldump --single-transaction --no-tablespaces --set-gtid-purged=OFF --skip-add-drop-table -u"$MYSQL_USER" "$MYSQL_DATABASE"'
    with target.open('xb') as output:
        subprocess.run(['docker','compose','exec','-T','db','sh','-c',command],cwd=ROOT,stdout=output,check=True)
    assert target.stat().st_size>1000
    name='techflow_migration_restore_'+secrets.token_hex(5)
    root_command='MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot'
    sql=f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL ON `{name}`.* TO 'techflow_test_user'@'%';"
    subprocess.run(TEST+['exec','-T','db-test','sh','-c',root_command],cwd=ROOT,input=sql,text=True,check=True)
    with target.open('rb') as source:
        subprocess.run(TEST+['exec','-T','db-test','sh','-c',root_command+' '+name],cwd=ROOT,stdin=source,check=True)
    guarded="import os\nassert os.environ['DB_HOST']=='db-test' and os.environ['MYSQL_DATABASE'].startswith('techflow_migration_restore_')\n"+SOURCE
    restored=json.loads(subprocess.check_output(TEST+['run','--rm','--no-deps','-T','-e','MYSQL_DATABASE='+name,'tests','python','-'],
        cwd=ROOT,input=guarded,text=True,encoding='utf-8'))
    assert baseline==restored,'Restored fingerprints differ; do not migrate demo.'
    manifest=dict(file=target.name,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  restored_schema=name,tables_verified=len(baseline))
    target.with_suffix('.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Local backup saved:',str(target.relative_to(ROOT)))
    print('Restore verified: all',len(baseline),'table fingerprints match; test schema retained. Demo was read only.')


if __name__=='__main__':main()
