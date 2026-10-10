"""Validation unit tests without a database connection."""
from werkzeug.datastructures import MultiDict
import pytest

from app.catalog.forms import CategoryForm, ProductForm


@pytest.mark.parametrize("code,valid", [("  ssd-pcie  ", True), ("SKU/2026.1", True), ("bad code", False), ("", False)])
def test_category_code_normalization(app, code, valid):
    with app.test_request_context():
        form = CategoryForm(MultiDict(dict(code=code, name="Thiết bị")), meta={"csrf":False})
        assert form.validate() is valid
        if valid:
            assert form.code.data == code.strip().upper()


@pytest.mark.parametrize("value,valid", [("0", True), ("999999999999.99", True), ("1.001", False),
    ("NaN", False), ("-Infinity", False), ("abc", False), ("-0.01", False),
    ("15.000.000", False), ("15000000,50", False)])
def test_money_validation(app, value, valid):
    with app.test_request_context():
        form = ProductForm(MultiDict(dict(sku="SSD-01", name="SSD", category_id="1", business_id="0",
                           purchase_price="0", selling_price=value, reorder_level="0")), meta={"csrf":False})
        form.category_id.choices = [(1,"SSD")]
        form.business_id.choices = [(0,"Không chọn")]
        assert form.validate() is valid
