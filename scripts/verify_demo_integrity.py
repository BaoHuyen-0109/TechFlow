"""Read-only table fingerprints; snapshots stay in ignored .docker-local."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / '.docker-local' / 'workspace-refactor-before.json'
SOURCE = """
import hashlib, json
from sqlalchemy import text
from wsgi import app
from app.extensions import db
with app.app_context(), db.engine.connect() as conn:
    tables = sorted(conn.execute(text('SHOW TABLES')).scalars())
    result = {}
    for table in tables:
        digest = hashlib.sha256()
        count = 0
        for row in conn.execute(text('SELECT * FROM `'+table+'` ORDER BY 1')):
            digest.update(json.dumps(list(row), default=str, ensure_ascii=True).encode())
            digest.update(b'\\n')
            count += 1
        result[table] = {'rows': count, 'sha256': digest.hexdigest()}
print(json.dumps(result, sort_keys=True))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['snapshot', 'compare'])
    parser.add_argument('--snapshot-file', type=Path, default=SNAPSHOT)
    args = parser.parse_args()
    snapshot = args.snapshot_file
    raw = subprocess.check_output(['docker', 'compose', 'exec', '-T', 'web', 'python', '-'],
                                  cwd=ROOT, input=SOURCE, text=True, encoding='utf-8')
    current = json.loads(raw)
    if args.mode == 'snapshot':
        if snapshot.exists():
            raise SystemExit('Baseline exists; refusing to overwrite it.')
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(json.dumps(current, indent=2), encoding='utf-8')
        print('Read-only baseline saved; rows:', {key: value['rows'] for key, value in current.items()})
    else:
        before = json.loads(snapshot.read_text(encoding='utf-8'))
        changed = [key for key in sorted(set(before) | set(current)) if before.get(key) != current.get(key)]
        assert not changed, 'Tables changed since baseline: ' + ', '.join(changed)
        print(f'Integrity passed: all {len(current)} tables have identical row counts and SHA-256 fingerprints.')


if __name__ == '__main__':
    main()
