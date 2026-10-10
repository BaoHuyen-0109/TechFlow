from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy import or_, select, func

from app.auth.permissions import business_required
from app.extensions import db
from app.models import Business, Category, Product, PurchaseReceipt
from app.services.catalog_service import CatalogError, persist


def build_blueprint(resource, prefix):
    blueprint = Blueprint(resource.key, __name__, url_prefix=prefix)

    def context(**values):
        return dict(resource=resource, active_page=resource.key,
                    workspace_home=url_for("dashboard.staff"), **values)

    def form_for(record=None):
        form = resource.form(obj=record)
        if resource.model is Product:
            form.category_id.choices = [(0, "Chọn danh mục")] + [(c.id, c.name + (" (ngừng hoạt động)" if not c.is_active else "")) for c in db.session.scalars(select(Category).order_by(Category.name))]
            form.business_id.choices = [(0, "Không chọn nhà cung cấp")] + [(b.id, b.name + (" (ngừng hoạt động)" if not b.is_active else "")) for b in db.session.scalars(select(Business).order_by(Business.name))]
            if request.method == "GET" and record and record.business_id is None:
                form.business_id.data = 0
        return form

    @blueprint.get("")
    @business_required
    def index():
        query = select(resource.model)
        search = request.args.get("q", "").strip()
        if len(search) > 120:
            abort(400)
        if search:
            columns = [getattr(resource.model, resource.code), resource.model.name]
            if resource.model is Business:
                columns += [Business.email, Business.phone]
            query = query.where(or_(*(column.contains(search, autoescape=True) for column in columns)))
        status = request.args.get("status", "")
        if status not in {"", "active", "inactive"}:
            abort(400)
        if status:
            query = query.where(resource.model.is_active == (status == "active"))
        if resource.model is Product:
            for field in ("category_id", "business_id"):
                raw = request.args.get(field, "")
                if raw:
                    if not raw.isascii() or not raw.isdigit() or len(raw) > 19 or int(raw) < 1:
                        abort(400)
                    query = query.where(getattr(Product, field) == int(raw))
        sort = request.args.get("sort", "newest")
        sorts = {"newest": resource.model.id.desc(), "oldest": resource.model.id.asc(),
                 "name": resource.model.name.asc(), "code": getattr(resource.model, resource.code).asc()}
        if sort not in sorts:
            abort(400)
        try:
            page = int(request.args.get("page", "1"))
            per_page = int(request.args.get("per_page", "10"))
            if page < 1 or page > 2147483647 or per_page not in {10, 20, 50}:
                raise ValueError
        except ValueError:
            abort(400)
        results = db.paginate(query.order_by(sorts[sort], resource.model.id), page=page, per_page=per_page, error_out=False)
        def page_url(number):
            args = request.args.to_dict()
            args["page"] = number
            return url_for(f"{resource.key}.index", **args)
        return render_template("catalog/index.html", **context(results=results, page_url=page_url,
            categories=db.session.scalars(select(Category).order_by(Category.name)).all() if resource.model is Product else [],
            suppliers=db.session.scalars(select(Business).order_by(Business.name)).all() if resource.model is Product else []))

    @blueprint.get("/<int:record_id>")
    @business_required
    def detail(record_id):
        record = db.get_or_404(resource.model, record_id)
        linked = None
        receipts = None
        receipt_history = []
        if resource.model in {Category, Business}:
            field = Product.category_id if resource.model is Category else Product.business_id
            linked = db.session.scalar(select(func.count()).select_from(Product).where(field == record.id))
        if resource.model is Business:
            receipts = db.session.scalar(select(func.count()).select_from(PurchaseReceipt).where(PurchaseReceipt.business_id == record.id))
            receipt_history = db.session.scalars(select(PurchaseReceipt).where(PurchaseReceipt.business_id == record.id)
                                                .order_by(PurchaseReceipt.receipt_date.desc(), PurchaseReceipt.id.desc()).limit(10)).all()
        return render_template("catalog/detail.html", **context(record=record, form=form_for(record), linked=linked, receipts=receipts, receipt_history=receipt_history))

    def save(record=None):
        form = form_for(record)
        message = None
        status = 200
        if form.validate_on_submit():
            target = record or resource.model()
            try:
                persist(resource, target, form)
                flash(f"{'Cập nhật' if record else 'Thêm'} {resource.singular} thành công.", "success")
                return redirect(url_for(f"{resource.key}.detail", record_id=target.id), code=303)
            except CatalogError as error:
                message, status = error.message, error.status
        elif request.method == "POST":
            status = 422
        return render_template("catalog/form.html", **context(form=form, record=record, message=message)), status

    @blueprint.route("/new", methods=["GET", "POST"])
    @business_required
    def create():
        return save()

    @blueprint.route("/<int:record_id>/edit", methods=["GET", "POST"])
    @business_required
    def edit(record_id):
        return save(db.get_or_404(resource.model, record_id))

    @blueprint.post("/<int:record_id>/delete")
    @business_required
    def delete(record_id):
        record = db.get_or_404(resource.model, record_id)
        try:
            persist(resource, record, delete=True)
        except CatalogError as error:
            return render_template("catalog/detail.html", **context(record=record, form=form_for(record), linked=None, receipts=None, message=error.message)), error.status
        flash(f"Xóa {resource.singular} thành công.", "success")
        return redirect(url_for(f"{resource.key}.index"), code=303)

    return blueprint
