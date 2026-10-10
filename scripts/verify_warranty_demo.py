"""Backup/restore proof before additive migration; compare original columns after.

Stop UI writes before backup and until compare completes. Dumps remain ignored.
"""
import argparse
import hashlib
import json
import secrets
import subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEST=['docker','compose','-f','docker-compose.db-test.yml']
SNAPSHOT=ROOT/'.docker-local/stage52-before.json'
SOURCE=r'''
import hashlib,json
from sqlalchemy import text,inspect
from wsgi import app
from app.extensions import db
with app.app_context(),db.engine.connect() as conn:
    selected=SELECTED
    result={}
    for table in sorted(inspect(conn).get_table_names()):
        if selected is not None and table not in selected: continue
        columns=selected[table]['columns'] if selected is not None else [c['name'] for c in inspect(conn).get_columns(table)]
        digest=hashlib.sha256();count=0
        for row in conn.execute(text('SELECT '+','.join('`'+c+'`' for c in columns)+' FROM `'+table+'` ORDER BY 1')):
            digest.update(json.dumps(list(row),default=str,ensure_ascii=True).encode());digest.update(bytes([10]));count+=1
        result[table]=dict(columns=columns,rows=count,sha256=digest.hexdigest())
print(json.dumps(result,sort_keys=True))
'''


def read(command,selected=None):
    source=SOURCE.replace('SELECTED',repr(selected))
    if '-e' in command:
        source="import os\nassert os.environ['DB_HOST']=='db-test' and os.environ['MYSQL_DATABASE'].startswith('techflow_migration_restore_')\n"+source
    return json.loads(subprocess.check_output(command+['python','-'],cwd=ROOT,input=source,text=True,encoding='utf-8'))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['backup','compare']);args=parser.parse_args()
    demo=['docker','compose','exec','-T','web']
    if args.mode=='compare':
        before=json.loads(SNAPSHOT.read_text(encoding='utf-8'));before.pop('alembic_version',None)
        after=read(demo,before)
        assert before==after,'Original data changed; investigate before opening UI.'
        print('Demo integrity verified:',len(before),'original tables unchanged (original columns).')
        return
    if SNAPSHOT.exists(): raise SystemExit('Baseline exists; refusing to overwrite backup proof.')
    baseline=read(demo)
    assert 'warranty_coverages' not in baseline,'Demo is already upgraded; do not overwrite the pre-migration proof.'
    SNAPSHOT.parent.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(3)
    target=ROOT/'.docker-local/backups'/('stage52-'+stamp+'.sql');target.parent.mkdir(parents=True,exist_ok=True)
    command='MYSQL_PWD="$MYSQL_PASSWORD" mysqldump --single-transaction --no-tablespaces --set-gtid-purged=OFF --skip-add-drop-table -u"$MYSQL_USER" "$MYSQL_DATABASE"'
    with target.open('xb') as out:
        subprocess.run(['docker','compose','exec','-T','db','sh','-c',command],cwd=ROOT,stdout=out,check=True)
    assert target.stat().st_size>1000
    name='techflow_migration_restore_'+secrets.token_hex(5)
    root='MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot'
    sql=f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL ON `{name}`.* TO 'techflow_test_user'@'%';"
    subprocess.run(TEST+['exec','-T','db-test','sh','-c',root],cwd=ROOT,input=sql,text=True,check=True)
    with target.open('rb') as source:subprocess.run(TEST+['exec','-T','db-test','sh','-c',root+' '+name],cwd=ROOT,stdin=source,check=True)
    restored=read(TEST+['run','--rm','--no-deps','-T','-e','MYSQL_DATABASE='+name,'tests'])
    assert baseline==restored,'Restore differs; do not migrate demo.'
    SNAPSHOT.write_text(json.dumps(baseline,indent=2),encoding='utf-8')
    manifest=dict(file=target.name,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),restored_schema=name,tables_verified=len(baseline))
    target.with_suffix('.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Backup saved locally:',target.relative_to(ROOT),'; restore verified:',len(baseline),'tables. No schema/volume deleted.')


if __name__=='__main__':main()
