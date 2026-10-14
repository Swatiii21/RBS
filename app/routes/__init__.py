"""Routes package initialization and blueprint registration."""

from flask import Flask

from app.routes.dashboard import dashboard_bp
from app.routes.menu import menu_bp
from app.routes.orders import orders_bp
from app.routes.billing import billing_bp
from app.routes.settings import settings_bp
from app.routes.activity_logs import logs_bp
from app.routes.quality import quality_bp


def register_routes(app: Flask) -> None:
    """Register all modular application blueprints with the Flask instance."""
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(quality_bp)
