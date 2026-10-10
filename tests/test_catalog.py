"""Real MySQL CRUD and security regression; test runner uses an isolated database."""
import secrets
from decimal import Decimal
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, func

from test_auth import account, auth_client, csrf, login
from app.extensions import db
from app.models import AuditLog, Business, Category, Product, User, StockMovement, SalesOrder, PurchaseReceipt, PurchaseReceiptItem


@pytest.fixture
def signed_in(auth_client, account):
    assert login(auth_client, account).status_code == 302
    return auth_client


def data_for(kind, catalog):
    suffix = secrets.token_hex(6).upper()
    if kind == "products":
        return dict(sku=f"CRUD-{suffix}", name=f"Laptop {suffix}", category_id=catalog["category_id"],
                    business_id=catalog["business_id"], purchase_price="1000.25", selling_price="2000.50",
                    reorder_level="5", is_active="y")
    return dict(code=f"CRUD-{suffix}", name=f"Danh muc {suffix}", is_active="y")


def post(client, path, data=None):
    token = csrf(client, "/staff/dashboard")
    return client.post(path, data=dict(data or {}, csrf_token=token))


@pytest.mark.parametrize("role", ["admin", "staff"])
@pytest.mark.parametrize("kind,model", [("categories", Category), ("suppliers", Business), ("products", Product)])
def test_crud_and_audit(signed_in, account, catalog, role, kind, model):
    user = db.session.get(User, account["id"])
    user.role = role
    db.session.commit()
    path = f"/business/{kind}"
    assert signed_in.get(path).status_code == 200
    assert signed_in.get(path + "/new").status_code == 200
    data = data_for(kind, catalog)
    result = post(signed_in, path + "/new", data)
    assert result.status_code == 303
    detail = result.location
    identifier = int(detail.rsplit("/", 1)[1])
    record = db.session.get(model, identifier)
    assert record.name == data["name"]
    assert signed_in.get(detail).status_code == 200
    assert signed_in.get(detail + "/edit").status_code == 200
    data["name"] += " updated"
    assert post(signed_in, detail + "/edit", data).status_code == 303
    db.session.expire_all()
    assert db.session.get(model, identifier).name == data["name"]
    assert post(signed_in, detail + "/delete").status_code == 303
    assert db.session.get(model, identifier) is None
    actions = db.session.scalars(select(AuditLog.action).where(AuditLog.entity_type == model.__tablename__, AuditLog.entity_id == identifier)).all()
    assert sorted(actions) == ["create", "delete", "update"]
    if role == "staff":
        assert signed_in.get("/admin/dashboard").status_code == 403


@pytest.mark.parametrize("kind", ["categories", "suppliers", "products"])
def test_duplicates_are_atomic(signed_in, catalog, kind):
    data = data_for(kind, catalog)
    path = f"/business/{kind}/new"
    assert post(signed_in, path, data).status_code == 303
    count = db.session.scalar(select(func.count()).select_from(AuditLog))
    duplicate = post(signed_in, path, data)
    assert duplicate.status_code == 409
    assert {"categories":"Mã danh mục đã tồn tại.", "suppliers":"Mã nhà cung cấp đã tồn tại.", "products":"Mã SKU đã tồn tại."}[kind] in duplicate.text
    assert db.session.scalar(select(func.count()).select_from(AuditLog)) == count


@pytest.mark.parametrize("value", ["0", "0.01", "18500000.50", "999999999999.99"])
def test_money_exact_mysql_round_trip(signed_in, catalog, value):
    data = data_for("products", catalog)
    data.update(purchase_price=value, selling_price=value)
    response = post(signed_in, "/business/products/new", data)
    assert response.status_code == 303
    db.session.expire_all()
    product = db.session.get(Product, int(response.location.rsplit("/", 1)[1]))
    assert product.purchase_price == Decimal(value)
    assert product.selling_price == Decimal(value)
    assert post(signed_in, response.location + "/delete").status_code == 303


@pytest.mark.parametrize("field,value", [("purchase_price", "-1"), ("selling_price", "NaN"),
    ("selling_price", "Infinity"), ("selling_price", "1000000000000"), ("selling_price", "1.234"),
    ("reorder_level", "-1"), ("reorder_level", "4294967296"), ("category_id", "999999999999"),
    ("business_id", "999999999999"), ("image_url", "javascript:alert(1)"),
    ("image_url", "https://user:secret@example.com/x"), ("name", "   "), ("sku", "bad code")])
def test_product_validation(signed_in, catalog, field, value):
    data = data_for("products", catalog)
    data[field] = value
    before = db.session.scalar(select(func.count()).select_from(Product))
    response = post(signed_in, "/business/products/new", data)
    assert response.status_code == 422
    assert db.session.scalar(select(func.count()).select_from(Product)) == before


@pytest.mark.parametrize("field,value", [("email", "bad@"), ("phone", "abc123"), ("name", "x" * 181), ("code", "x" * 31)])
def test_supplier_validation(signed_in, catalog, field, value):
    data = data_for("suppliers", catalog)
    data[field] = value
    assert post(signed_in, "/business/suppliers/new", data).status_code == 422


def test_nullable_tax_unique(signed_in, catalog):
    data = data_for("suppliers", catalog)
    data["tax_code"] = ""
    first = post(signed_in, "/business/suppliers/new", data)
    assert first.status_code == 303
    second_data = data_for("suppliers", catalog)
    second_data["tax_code"] = ""
    assert post(signed_in, "/business/suppliers/new", second_data).status_code == 303
    data["tax_code"] = "TAX-" + secrets.token_hex(5)
    assert post(signed_in, first.location + "/edit", data).status_code == 303
    second_data["tax_code"] = data["tax_code"]
    assert post(signed_in, "/business/suppliers/new", second_data).status_code == 409


def test_fk_protection_and_stock_unchanged(signed_in, catalog):
    for kind, key in [("categories", "category_id"), ("suppliers", "business_id")]:
        assert post(signed_in, f"/business/{kind}/{catalog[key]}/delete").status_code == 409
    product = db.session.get(Product, catalog["product_id"])
    product.stock_quantity = 9  # Fixture setup only, never an application operation.
    db.session.commit()
    before = {model: db.session.scalar(select(func.count()).select_from(model)) for model in (StockMovement, SalesOrder, PurchaseReceipt)}
    data = data_for("products", catalog)
    data.update(sku=product.sku, stock_quantity="999", name="Updated stock readonly")
    assert post(signed_in, f"/business/products/{product.id}/edit", data).status_code == 303
    db.session.expire_all()
    assert product.stock_quantity == 9
    assert post(signed_in, f"/business/products/{product.id}/delete").status_code == 409
    created = post(signed_in, "/business/products/new", dict(data_for("products", catalog), stock_quantity="999"))
    assert created.status_code == 303
    assert db.session.get(Product, int(created.location.rsplit("/", 1)[1])).stock_quantity == 0
    for model, count in before.items():
        assert db.session.scalar(select(func.count()).select_from(model)) == count


@pytest.mark.parametrize("kind", ["categories", "suppliers", "products"])
def test_auth_csrf_missing_and_methods(auth_client, account, catalog, kind):
    path = f"/business/{kind}"
    assert auth_client.get(path).status_code == 302
    assert login(auth_client, account).status_code == 302
    assert auth_client.post(path + "/new", data={}).status_code == 400
    assert auth_client.get(path + "/999999999999").status_code == 404
    assert auth_client.get(path + "/999999999999/edit").status_code == 404
    assert auth_client.get(path + "/1/delete").status_code == 405
    assert post(auth_client, path + "/999999999999/delete").status_code == 404


def test_search_filter_sort_pagination_and_xss(signed_in, catalog):
    suffix = secrets.token_hex(6)
    for index in range(12):
        db.session.add(Category(code=f"PAGE-{suffix}-{index}", name=f"Pagination {suffix} {index:02}"))
    db.session.commit()
    path = f"/business/categories?q={suffix}&sort=name&per_page=10"
    first = signed_in.get(path)
    assert first.status_code == 200 and f"Pagination {suffix} 00" in first.text
    assert f"Pagination {suffix} 11" not in first.text
    assert f"Pagination {suffix} 11" in signed_in.get(path + "&page=2").text
    assert signed_in.get("/business/products?category_id=" + str(catalog["category_id"]) + "&business_id=" + str(catalog["business_id"])).status_code == 200
    assert catalog["sku"] in signed_in.get("/business/products?q=" + catalog["sku"]).text
    assert catalog["sku"] not in signed_in.get("/business/products?status=inactive").text
    for query in ("sort=drop", "page=0", "page=x", "per_page=999", "status=x", "category_id=x"):
        assert signed_in.get("/business/products?" + query).status_code == 400
    assert signed_in.get("/business/products?q=%25").status_code == 200
    data = data_for("categories", catalog)
    data["name"] = '<script>alert("xss")</script>' + suffix
    saved = post(signed_in, "/business/categories/new", data)
    assert saved.status_code == 303
    assert "<script>alert" not in signed_in.get(saved.location).text


def test_audit_failure_rolls_back_entity(signed_in, catalog, monkeypatch):
    from app.services import catalog_service
    def invalid_audit(**kwargs):
        kwargs["user_id"] = 999999999999
        return AuditLog(**kwargs)
    monkeypatch.setattr(catalog_service, "AuditLog", invalid_audit)
    data = data_for("categories", catalog)
    assert post(signed_in, "/business/categories/new", data).status_code == 409
    assert db.session.scalar(select(Category.id).where(Category.code == data["code"])) is None


def test_purchase_references_prevent_deletion(signed_in, catalog):
    receipt = PurchaseReceipt(receipt_code="FK-" + secrets.token_hex(8), business_id=catalog["business_id"],
                              created_by=catalog["user_id"], receipt_date=datetime.now(timezone.utc).replace(tzinfo=None))
    db.session.add(receipt)
    db.session.flush()
    item = PurchaseReceiptItem(receipt_id=receipt.id, product_id=catalog["product_id"], quantity=1, unit_cost=100, line_total=100)
    db.session.add(item)
    db.session.commit()
    before = db.session.scalar(select(func.count()).select_from(AuditLog))
    assert post(signed_in, f'/business/products/{catalog["product_id"]}/delete').status_code == 409
    assert post(signed_in, f'/business/suppliers/{catalog["business_id"]}/delete').status_code == 409
    assert db.session.get(PurchaseReceiptItem, item.id) is not None
    assert receipt.receipt_code in signed_in.get(f'/business/suppliers/{catalog["business_id"]}').text
    assert db.session.scalar(select(func.count()).select_from(AuditLog)) == before


def test_supplier_search_and_category_duplicate_name(signed_in, catalog):
    suffix = secrets.token_hex(6)
    data = data_for("suppliers", catalog)
    data.update(email=f"contact-{suffix}@example.invalid", phone="090" + str(int(suffix, 16))[:7])
    saved = post(signed_in, "/business/suppliers/new", data)
    assert saved.status_code == 303
    for search in (data["code"], data["email"], data["phone"]):
        assert data["name"] in signed_in.get("/business/suppliers", query_string={"q":search}).text
    category = data_for("categories", catalog)
    assert post(signed_in, "/business/categories/new", category).status_code == 303
    category["code"] += "-OTHER"
    assert post(signed_in, "/business/categories/new", category).status_code == 409
    response = signed_in.get("/business/categories", query_string={"q":"' OR 1=1 --"})
    assert response.status_code == 200 and "Chưa có kết quả phù hợp" in response.text


@pytest.mark.parametrize("kind,key,model", [("categories","category_id",Category),
    ("suppliers","business_id",Business), ("products","product_id",Product)])
def test_edit_delete_csrf_and_inactive_session(signed_in, account, catalog, kind, key, model):
    path = f'/business/{kind}/{catalog[key]}'
    assert signed_in.post(path + "/edit", data={}).status_code == 400
    assert signed_in.post(path + "/delete", data={}).status_code == 400
    assert db.session.get(model, catalog[key]) is not None
    user = db.session.get(User, account["id"])
    user.is_active = False
    db.session.commit()
    assert signed_in.get(path).status_code == 302


def test_storage_failure_is_atomic_and_friendly(signed_in, catalog, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    data = data_for("categories", catalog)
    def unavailable():
        raise SQLAlchemyError("sensitive database error must not be returned")
    monkeypatch.setattr(db.session, "commit", unavailable)
    response = post(signed_in, "/business/categories/new", data)
    assert response.status_code == 503
    assert data["name"] in response.text and data["code"] in response.text
    assert "sensitive database" not in response.text
    assert db.session.scalar(select(Category.id).where(Category.code == data["code"])) is None


def test_category_placeholder_required_and_edit_preserved(signed_in, catalog):
    page = signed_in.get("/business/products/new")
    assert '<option value="0">Chọn danh mục</option>' in page.text
    data = data_for("products", catalog)
    data["category_id"] = "0"
    rejected = post(signed_in, "/business/products/new", data)
    assert rejected.status_code == 422
    assert "Vui lòng chọn danh mục" in rejected.text
    edit = signed_in.get(f'/business/products/{catalog["product_id"]}/edit')
    assert f'<option selected value="{catalog["category_id"]}">' in edit.text


def test_product_only_image_csp(signed_in):
    product_csp = signed_in.get("/business/products/new").headers["Content-Security-Policy"]
    category_csp = signed_in.get("/business/categories/new").headers["Content-Security-Policy"]
    assert "img-src 'self' data: https: http:" in product_csp
    assert "img-src 'self' data:;" in category_csp
    assert "script-src 'self';" in product_csp and "unsafe-inline" not in product_csp
