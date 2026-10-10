"""Export documentation from ORM metadata without connecting to a database."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy.dialects import mysql
from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db
from app import models  # noqa: F401 -- register all models


def main() -> None:
    lines = ["# Chi tiết schema MySQL", "",
             "Xuất từ models bằng `python scripts/export_database_schema.py`.",
             f"Mô tả {len(db.metadata.tables)} bảng nghiệp vụ; không kết nối DB hoặc đọc secrets.",
             "Giai đoạn 5.1 bổ sung customers và liên kết tùy chọn vào đơn bán; xem [CUSTOMERS.md](CUSTOMERS.md).", ""]
    for table in db.metadata.sorted_tables:
        lines.extend([f"## {table.name}", "", "| Cột | Kiểu MySQL | Nullable | Quy tắc |",
                      "| --- | --- | --- | --- |"])
        for column in table.columns:
            rules = []
            if column.primary_key:
                rules.append("PK, AUTO_INCREMENT")
            if column.unique:
                rules.append("UNIQUE")
            for foreign_key in column.foreign_keys:
                rules.append(f"FK {foreign_key.target_fullname}, DELETE {foreign_key.ondelete}")
            if column.computed is not None:
                rules.append(f"GENERATED ALWAYS ({column.computed.sqltext}) STORED")
            elif column.server_default is not None:
                rules.append(f"DEFAULT {column.server_default.arg}")
            if column.onupdate is not None:
                rules.append("ORM cập nhật UTC")
            kind = column.type.compile(dialect=mysql.dialect())
            lines.append(f"| {column.name} | {kind} | {'Có' if column.nullable else 'Không'} | {', '.join(rules)} |")
        lines.extend(["", "Indexes:", ""])
        for index in sorted(table.indexes, key=lambda item: item.name):
            lines.append(f"- `{index.name}`: {', '.join(column.name for column in index.columns)}")
        lines.extend(["", "Constraints bổ sung:", ""])
        for constraint in sorted(table.constraints, key=lambda item: str(item.name)):
            if isinstance(constraint, CheckConstraint):
                lines.append(f"- `{constraint.name}`: CHECK ({constraint.sqltext})")
            elif isinstance(constraint, UniqueConstraint):
                lines.append(f"- `{constraint.name}`: UNIQUE ({', '.join(column.name for column in constraint.columns)})")
        lines.append("")
    (ROOT / "docs" / "DATABASE_SCHEMA.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Exported docs/DATABASE_SCHEMA.md from {len(db.metadata.tables)} model tables.")


if __name__ == "__main__":
    main()
