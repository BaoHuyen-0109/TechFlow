"""Dashboard acceptance on real MySQL, with connection-local empty tables.

Temporary tables shadow catalog tables only for this connection. Existing test
and demo rows are never deleted, truncated, reset or changed by these fixtures.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import insert, select, func, text
from sqlalchemy.exc import SQLAlchemyError

from test_auth import account, auth_client, login
from app.extensions import db
from app.models import Product, Category, Business, User
from app.services.dashboard_service import query_dashboard
from app.dashboard.routes import vietnam_time


@pytest.fixture
def isolated_catalog(mysql_app):
    with db.engine.connect() as connection:
        assert connection.engine.url.database == "techflow_test"
        for name in ("categories", "businesses", "products"):
            connection.execute(text(f"CREATE TEMPORARY TABLE `dashboard_test_{name}` LIKE `{name}`"))
            connection.execute(text(f"ALTER TABLE `dashboard_test_{name}` RENAME TO `{name}`"))
        try:
            yield connection
        finally:
            connection.rollback()
            for name in ("products", "businesses", "categories"):
                connection.execute(text(f"DROP TEMPORARY TABLE IF EXISTS `{name}`"))
            connection.commit()


def category(connection, identifier, active=True, name=None):
    connection.execute(insert(Category.__table__).values(id=identifier, code=f"CAT-{identifier}",
        name=name or f"Danh mục {identifier}", is_active=active))


def product(connection, identifier, *, category_id=1, stock=0, threshold=5,
            price="0.00", active=True, updated=None):
    created = datetime(2026, 1, 1, 0, 0)
    connection.execute(insert(Product.__table__).values(id=identifier, sku=f"SKU-{identifier}",
        name=f"Thiết bị {identifier:03}", category_id=category_id, purchase_price=Decimal(price),
        selling_price=Decimal("1.00"), stock_quantity=stock, reorder_level=threshold,
        is_active=active, created_at=created, updated_at=updated or created))


@pytest.mark.parametrize("role", ["admin", "staff"])
def test_empty_dashboard_real_mysql(isolated_catalog, role):
    stats = query_dashboard(isolated_catalog, role)
    assert stats["totals"]["products"] == stats["totals"]["categories"] == 0
    assert stats["totals"]["suppliers"] == stats["totals"]["low_stock"] == 0
    assert stats["categories"] == stats["low_stock"] == stats["recent"] == []
    if role == "admin":
        assert stats["totals"]["inventory_value"] == Decimal("0.00")
    else:
        assert "inventory_value" not in stats["totals"]


def test_active_counts_and_exact_inventory_value(isolated_catalog):
    connection = isolated_catalog
    category(connection, 1)
    category(connection, 2, active=False)
    connection.execute(insert(Business.__table__), [dict(id=1,code="SUP-1",name="Đối tác",is_active=True),
                                                   dict(id=2,code="SUP-2",name="Ngừng",is_active=False)])
    product(connection, 1, stock=3, price="0.01")
    product(connection, 2, stock=2, price="1234.56", category_id=2)
    product(connection, 3, stock=7, price="10.01", active=False)
    stats = query_dashboard(connection, "admin")
    assert stats["totals"] == dict(products=2, categories=1, suppliers=1, low_stock=2,
                                   inventory_value=Decimal("2539.22"))
    assert sum(row["count"] for row in stats["categories"]) == 2
    assert any(row["id"] == 2 and not row["is_active"] for row in stats["categories"])
    assert [row["id"] for row in stats["recent"]] == [3, 2, 1]


@pytest.mark.parametrize("stock,threshold,active,expected", [
    (0, 0, True, True), (0, 5, True, True), (4, 5, True, True),
    (5, 5, True, True), (6, 5, True, False), (0, 5, False, False),
])
def test_low_stock_boundaries(isolated_catalog, stock, threshold, active, expected):
    category(isolated_catalog, 1)
    product(isolated_catalog, 1, stock=stock, threshold=threshold, active=active)
    stats = query_dashboard(isolated_catalog, "staff")
    assert stats["totals"]["low_stock"] == int(expected)
    assert bool(stats["low_stock"]) is expected


def test_limits_category_remainder_and_recent_order(isolated_catalog):
    connection = isolated_catalog
    for identifier in range(1, 13):
        category(connection, identifier)
        product(connection, identifier, category_id=identifier, stock=0,
                updated=datetime(2026, 1, 1) + timedelta(hours=identifier))
    stats = query_dashboard(connection, "admin")
    assert stats["totals"]["products"] == stats["totals"]["low_stock"] == 12
    assert len(stats["low_stock"]) == 8
    assert [row["id"] for row in stats["recent"]] == [12, 11, 10, 9, 8, 7]
    assert len(stats["categories"]) == 9
    assert stats["categories"][-1]["id"] is None
    assert stats["categories"][-1]["count"] == 4
    assert sum(row["count"] for row in stats["categories"]) == 12


def test_large_decimal_and_zero_price_are_not_rounded(isolated_catalog):
    category(isolated_catalog, 1)
    product(isolated_catalog, 1, stock=4294967295, price="999999999999.99")
    product(isolated_catalog, 2, stock=9, price="0")
    stats = query_dashboard(isolated_catalog, "admin")
    assert stats["totals"]["inventory_value"] == Decimal("4294967295") * Decimal("999999999999.99")


@pytest.mark.parametrize("field", ["purchase_price", "stock_quantity"])
def test_missing_inventory_value_is_not_a_misleading_zero(isolated_catalog, field):
    # Alter only a connection-local temporary table to simulate invalid imports.
    definition = "DECIMAL(14,2)" if field == "purchase_price" else "INT UNSIGNED"
    isolated_catalog.execute(text(f"ALTER TABLE products MODIFY `{field}` {definition} NULL"))
    category(isolated_catalog, 1)
    product(isolated_catalog, 1, stock=3, price="1.01")
    isolated_catalog.execute(Product.__table__.update().values({field: None}))
    stats = query_dashboard(isolated_catalog, "admin")
    assert stats["totals"]["inventory_value"] is None


def test_staff_never_queries_purchase_prices(isolated_catalog):
    from sqlalchemy import event
    queries = []
    def record(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)
    event.listen(isolated_catalog, "before_cursor_execute", record)
    try:
        result = query_dashboard(isolated_catalog, "staff")
    finally:
        event.remove(isolated_catalog, "before_cursor_execute", record)
    assert "inventory_value" not in result["totals"]
    assert len(queries) == 6
    assert all("purchase_price" not in sql and "selling_price" not in sql for sql in queries)
    assert all(sql.lstrip().upper().startswith("SELECT") for sql in queries)


def test_unknown_role_cannot_query(isolated_catalog):
    with pytest.raises(PermissionError):
        query_dashboard(isolated_catalog, "owner")


@pytest.mark.parametrize("role", ["admin", "staff"])
def test_dashboard_render_and_permission(auth_client, account, role):
    db.session.get(User, account["id"]).role = role
    db.session.commit()
    assert login(auth_client, account).status_code == 302
    response = auth_client.get("/staff/dashboard?role=admin&include_value=true")
    assert response.status_code == 200
    assert 'data-kpi="products"' in response.text
    assert ('data-kpi="inventory_value"' in response.text) is (role == "admin")
    assert ("Giá trị tồn kho ước tính" in response.text) is (role == "admin")
    assert "Báo cáo doanh thu nâng cao chưa triển khai" in response.text
    assert auth_client.get("/admin/dashboard").status_code == (200 if role == "admin" else 403)


def test_dashboard_unavailable_is_not_zero(auth_client, account):
    login(auth_client, account)
    with patch("app.dashboard.routes.load_dashboard", side_effect=SQLAlchemyError("sensitive SQL details")):
        response = auth_client.get("/staff/dashboard")
    assert response.status_code == 503
    assert "Chưa thể tải thống kê" in response.text
    assert "sensitive SQL" not in response.text
    assert "data-kpi=" not in response.text
    assert 'id="session"' in response.text


def test_dashboard_empty_template(auth_client, account, isolated_catalog):
    login(auth_client, account)
    stats = query_dashboard(isolated_catalog, "admin")
    with patch("app.dashboard.routes.load_dashboard", return_value=stats):
        response = auth_client.get("/staff/dashboard")
    assert response.status_code == 200
    assert "Chưa có dữ liệu biểu đồ" in response.text
    assert "Chưa có sản phẩm" in response.text
    assert 'id="category-chart"' not in response.text
    assert "0,00 ₫" in response.text


def test_dashboard_chart_escapes_category_labels(auth_client, account, isolated_catalog):
    login(auth_client, account)
    category(isolated_catalog, 1, name="</script><img src=x onerror=alert(1)>")
    product(isolated_catalog, 1)
    with patch("app.dashboard.routes.load_dashboard", return_value=query_dashboard(isolated_catalog,"admin")):
        response = auth_client.get("/staff/dashboard")
    assert "</script><img" not in response.text
    assert "&lt;/script&gt;" in response.text
    assert "\\u003c/script\\u003e" in response.text


def test_dashboard_anonymous_is_protected(auth_client):
    assert auth_client.get("/staff/dashboard").location.startswith("/login?")


def test_vietnam_timestamp_is_not_server_local_time():
    assert vietnam_time(datetime(2026, 1, 1, 20, 30)) == "03:30 · 02/01/2026"
