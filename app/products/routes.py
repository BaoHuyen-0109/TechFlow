from app.catalog.resources import PRODUCTS
from app.catalog.routes import build_blueprint

blueprint = build_blueprint(PRODUCTS, "/business/products")
