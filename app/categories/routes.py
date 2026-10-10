from app.catalog.resources import CATEGORIES
from app.catalog.routes import build_blueprint

blueprint = build_blueprint(CATEGORIES, "/business/categories")
