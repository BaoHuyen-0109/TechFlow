from dataclasses import dataclass

from app.catalog.forms import BusinessForm, CategoryForm, ProductForm
from app.models import Business, Category, Product


@dataclass(frozen=True)
class Resource:
    key: str
    label: str
    icon: str
    model: type
    form: type
    code: str

    @property
    def singular(self):
        return {"categories": "danh mục", "businesses": "nhà cung cấp", "products": "sản phẩm"}[self.key]

    @property
    def description(self):
        return {"categories": "Tổ chức và phân loại sản phẩm để quản lý dễ dàng hơn.",
                "businesses": "Quản lý thông tin và đối tác cung cấp hàng hóa.",
                "products": "Quản lý thông tin sản phẩm, giá bán và danh mục thiết bị."}[self.key]

    @property
    def create_description(self):
        return {"categories": "Tạo danh mục mới để phân loại sản phẩm.",
                "businesses": "Thêm đối tác cung cấp hàng hóa vào hệ thống.",
                "products": "Nhập thông tin để tạo sản phẩm mới trong hệ thống."}[self.key]

    @property
    def groups(self):
        # Presentation metadata; all fields already exist in the models/forms.
        return {
            "products": [
                ("Thông tin cơ bản", "box-seam", ("sku", "name", "brand", "model")),
                ("Phân loại", "tags", ("category_id", "business_id")),
                ("Giá và tồn kho", "wallet2", ("purchase_price", "selling_price", "reorder_level")),
                ("Chính sách bảo hành", "shield-check", ("warranty_enabled", "warranty_months", "warranty_notes")),
                ("Thông tin bổ sung", "card-text", ("image_url", "description", "is_active")),
            ],
            "categories": [("Thông tin danh mục", "tags", ("code", "name", "description", "is_active"))],
            "businesses": [
                ("Thông tin nhà cung cấp", "buildings", ("code", "name", "tax_code")),
                ("Thông tin liên hệ", "person-lines-fill", ("contact_person", "email", "phone")),
                ("Địa chỉ và ghi chú", "geo-alt", ("address", "notes")),
                ("Trạng thái", "toggle-on", ("is_active",)),
            ],
        }[self.key]


CATEGORIES = Resource("categories", "Danh mục sản phẩm", "tags", Category, CategoryForm, "code")
SUPPLIERS = Resource("businesses", "Nhà cung cấp", "buildings", Business, BusinessForm, "code")
PRODUCTS = Resource("products", "Sản phẩm", "box-seam", Product, ProductForm, "sku")
