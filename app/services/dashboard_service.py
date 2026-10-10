"""Bounded, read-only dashboard queries. No inventory or sales mutations."""
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.engine import Connection

from app.extensions import db
from app.models import Business, Category, Product

LOW_STOCK_LIMIT = 8
RECENT_LIMIT = 6
CATEGORY_LIMIT = 8


def query_dashboard(connection: Connection, role: str) -> dict:
    """Execute against one MySQL read snapshot; expose only role-allowed fields."""
    if role not in {"admin", "staff"}:
        raise PermissionError("Dashboard role is not permitted")
    active = Product.is_active.is_(True)
    low = and_(active, Product.stock_quantity <= Product.reorder_level)
    aggregates = [func.count(case((active, 1))).label("products"),
                  func.count(case((low, 1))).label("low_stock")]
    if role == "admin":
        invalid = or_(Product.stock_quantity.is_(None), Product.stock_quantity < 0,
                      Product.purchase_price.is_(None), Product.purchase_price < 0)
        aggregates.extend([
            func.coalesce(func.sum(Product.stock_quantity * Product.purchase_price), Decimal("0.00")).label("inventory_value"),
            func.count(case((invalid, 1))).label("invalid_inventory"),
        ])
    totals = dict(connection.execute(select(*aggregates)).mappings().one())
    if role == "admin":
        if totals.pop("invalid_inventory"):
            totals["inventory_value"] = None
    totals["categories"] = connection.scalar(select(func.count()).select_from(Category).where(Category.is_active.is_(True)))
    totals["suppliers"] = connection.scalar(select(func.count()).select_from(Business).where(Business.is_active.is_(True)))

    count = func.count(Product.id)
    groups = [dict(row) for row in connection.execute(
        select(Category.id, Category.name, Category.is_active, count.label("count"))
        .join(Product, Product.category_id == Category.id).where(active)
        .group_by(Category.id, Category.name, Category.is_active)
        .order_by(count.desc(), Category.id).limit(CATEGORY_LIMIT)
    ).mappings()]
    remainder = totals["products"] - sum(row["count"] for row in groups)
    if remainder:
        groups.append(dict(id=None, name="Danh mục khác", is_active=True, count=remainder))
    columns = [Product.id, Product.sku, Product.name, Product.stock_quantity,
               Product.reorder_level, Product.is_active, Category.name.label("category")]
    low_stock = [dict(row) for row in connection.execute(
        select(*columns).join(Category, Product.category_id == Category.id)
        .where(low).order_by(Product.stock_quantity, Product.name, Product.id).limit(LOW_STOCK_LIMIT)
    ).mappings()]
    # Catalog permissions currently allow both roles to view inactive records.
    recent = [dict(row) for row in connection.execute(
        select(Product.id, Product.sku, Product.name, Product.is_active,
               Product.created_at, Product.updated_at,
               func.greatest(Product.created_at, Product.updated_at).label("activity_at"))
        .order_by(func.greatest(Product.created_at, Product.updated_at).desc(), Product.id.desc())
        .limit(RECENT_LIMIT)
    ).mappings()]
    return dict(totals=totals, categories=groups, low_stock=low_stock, recent=recent,
                low_stock_limit=LOW_STOCK_LIMIT, recent_limit=RECENT_LIMIT,
                as_of=datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")))


def load_dashboard(role: str) -> dict:
    # Separate from the authentication session: a fresh, consistent read transaction.
    with db.engine.connect() as connection, connection.begin():
        return query_dashboard(connection, role)
