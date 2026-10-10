"""Catalog persistence. Stock and receipt/order operations are deliberately excluded."""
from flask import request
from flask_login import current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select
import re

from app.extensions import db
from app.models import AuditLog, Product


class CatalogError(Exception):
    def __init__(self, message, status=409):
        self.message, self.status = message, status


def persist(resource, record, form=None, delete=False):
    try:
        if delete:
            if isinstance(record, Product):
                # Share a row lock with future inventory services so stock cannot
                # change between the availability check and deletion.
                record = db.session.scalar(select(Product).where(Product.id == record.id)
                                           .with_for_update().execution_options(populate_existing=True))
                if record is None:
                    raise CatalogError("Sản phẩm không còn tồn tại. Vui lòng tải lại trang.", 404)
            if isinstance(record, Product) and record.stock_quantity:
                raise CatalogError("Không thể xóa sản phẩm còn tồn kho. Hãy chuyển sang ngừng hoạt động.")
            action = "delete"
            entity_id = record.id
            db.session.delete(record)
        else:
            action = "update" if record.id else "create"
            if isinstance(record, Product) and current_user.role != 'admin' and any(
                    name in request.form for name in ('warranty_enabled','warranty_months','warranty_notes')):
                raise CatalogError('Chỉ Admin được cấu hình chính sách bảo hành.',403)
            # Explicit form whitelist: never accept stock_quantity, IDs or timestamps.
            for name in resource.form.__dict__:
                if name.startswith("_") or name not in form._fields:
                    continue
                if name.startswith('warranty_') and current_user.role != 'admin':
                    continue
                value = form[name].data
                if isinstance(value, str):
                    value = value.strip() or None
                if name == "business_id":
                    value = value or None
                setattr(record, name, value)
            db.session.add(record)
            db.session.flush()
            entity_id = record.id
        db.session.add(AuditLog(user_id=current_user.id, action=action,
                                entity_type=resource.model.__tablename__, entity_id=entity_id,
                                description="Thao tác danh mục kinh doanh", ip_address=request.remote_addr))
        db.session.commit()
    except CatalogError:
        db.session.rollback()
        raise
    except IntegrityError as error:
        db.session.rollback()
        number = error.orig.args[0]
        if number == 1062:
            # Extract only the constraint identifier, never display/log the value.
            match = re.search(r"for key ['`]([^'`]+)['`]", str(error.orig.args[1]))
            key = match.group(1).split(".")[-1] if match else ""
            messages = {"uq_products_sku": "Mã SKU đã tồn tại.",
                        "uq_categories_code": "Mã danh mục đã tồn tại.",
                        "uq_categories_name": "Tên danh mục đã tồn tại.",
                        "uq_businesses_code": "Mã nhà cung cấp đã tồn tại.",
                        "uq_businesses_tax_code": "Mã số thuế đã tồn tại."}
            raise CatalogError(messages.get(key, "Thông tin đã tồn tại. Vui lòng kiểm tra lại.")) from None
        if number == 1451:
            messages = {"categories": "Danh mục này đang được sử dụng bởi sản phẩm.",
                        "businesses": "Không thể xóa nhà cung cấp vì còn dữ liệu liên kết.",
                        "products": "Không thể xóa sản phẩm vì còn dữ liệu liên kết."}
            raise CatalogError(messages[resource.key] + " Hãy chuyển sang ngừng hoạt động.") from None
        raise CatalogError("Dữ liệu liên kết đã thay đổi. Vui lòng tải lại trang và thử lại.") from None
    except SQLAlchemyError:
        db.session.rollback()
        raise CatalogError("Chưa thể lưu dữ liệu. Vui lòng thử lại sau.", 503) from None
