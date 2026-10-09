"""Check local MySQL persistence without deleting any existing data.

Run from the host with Python 3.12. Docker Compose services must be running.
Creates one probe row, restarts the local db service, and verifies the row.
The stage1_probe table is intentionally retained, separate from business models.
"""
from pathlib import Path
import secrets
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def compose(*args: str, source: str | None = None) -> None:
    subprocess.run(
        ["docker", "compose", *args],
        cwd=PROJECT_ROOT,
        input=source,
        text=True,
        check=True,
    )


def main() -> None:
    probe_id = secrets.randbelow(2_000_000_000) + 1
    marker = secrets.token_hex(16)
    setup = """
from wsgi import app
from app.extensions import db
from sqlalchemy import text
with app.app_context(), db.engine.begin() as connection:
    connection.execute(text('CREATE TABLE IF NOT EXISTS stage1_probe (id INT PRIMARY KEY, marker VARCHAR(50)) ENGINE=InnoDB'))
    connection.execute(text('INSERT INTO stage1_probe (id, marker) VALUES (:id, :marker)'), PARAMETERS)
print('Probe row committed to MySQL.')
""".replace("PARAMETERS", repr({"id": probe_id, "marker": marker}))
    compose("exec", "-T", "web", "python", "-", source=setup)
    compose("restart", "db")
    compose("up", "-d", "--wait", "--wait-timeout", "120")
    verify = """
from wsgi import app
from app.extensions import db
from sqlalchemy import text
with app.app_context(), db.engine.connect() as connection:
    marker = connection.execute(text('SELECT marker FROM stage1_probe WHERE id = :id'), PARAMETERS).scalar_one()
    assert marker == EXPECTED, 'Persistence check failed'
print('Persistence passed: committed row retained after MySQL restart.')
""".replace("PARAMETERS", repr({"id": probe_id})).replace("EXPECTED", repr(marker))
    compose("exec", "-T", "web", "python", "-", source=verify)
    print(f"Retained local stage1_probe row id={probe_id}; no data deleted.")


if __name__ == "__main__":
    main()
