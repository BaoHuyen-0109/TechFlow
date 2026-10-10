from app.catalog.resources import SUPPLIERS
from app.catalog.routes import build_blueprint

blueprint = build_blueprint(SUPPLIERS, "/business/suppliers")
