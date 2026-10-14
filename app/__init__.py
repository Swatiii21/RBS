"""Application Factory for Restaurant Billing System.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides:
- Application factory pattern (create_app) enabling multiple isolated configurations (dev, test)
- Startup configuration validation
- Database teardown handling
- Centralized error handlers with safe user messages and detailed technical logging
- Context processors providing global metadata across all templates
"""

from __future__ import annotations

import os
from typing import Optional
from flask import Flask, render_template

from app.config import get_config
from app.database.connection import close_db, create_connection
from app.database.migrations import init_db, seed_default_settings, seed_sample_menu, seed_tqm_sample_data
from app.routes import register_routes
from app.services.logging_service import setup_application_logger, get_logger


def create_app(config_name: Optional[str] = None) -> Flask:
    """Create and configure a Flask application instance.

    Args:
        config_name: Environment name ('development', 'testing', 'production').

    Returns:
        Flask: Fully initialized Flask application.
    """
    app = Flask(__name__)

    # 1. Load and apply configuration
    cfg = get_config(config_name)
    app.config.from_object(cfg)

    # 2. Setup technical logging
    setup_application_logger(
        log_file=app.config.get("LOG_FILE", "logs/app.log"),
        log_level=app.config.get("LOG_LEVEL", "INFO"),
        max_bytes=app.config.get("LOG_MAX_BYTES", 1048576),
        backup_count=app.config.get("LOG_BACKUP_COUNT", 5),
    )
    logger = get_logger()
    logger.info("Initializing Restaurant Billing System (Q11: Maintainability)...")

    # 3. Register database teardown
    app.teardown_appcontext(close_db)

    # 4. Bootstrap database if newly created
    with app.app_context():
        try:
            conn = create_connection(app.config.get("DATABASE_PATH"))
            init_db(conn)
            seed_default_settings(conn)
            # Only seed demo sample items if not testing or explicitly required
            seed_sample_menu(conn)
            seed_tqm_sample_data(conn)
            conn.close()
            logger.info("Database schema and baseline seed validated successfully.")
        except Exception as e:
            logger.error(f"Failed to bootstrap database: {e}", exc_info=True)
            raise

    # 5. Global Template Context Processors
    @app.context_processor
    def inject_global_metadata():
        from app.database.connection import get_db
        from app.services.settings_service import get_setting

        db_conn = get_db()
        currency_sym = get_setting(db_conn, "currency_symbol", "₹")
        app_title = get_setting(db_conn, "app_name", "Restaurant Billing System — Q11")
        rest_name = get_setting(db_conn, "restaurant_name", "Emerald Dine Restaurant")

        return {
            "app_title": app_title,
            "restaurant_name": rest_name,
            "currency_symbol": currency_sym,
            "student_name": app.config.get("STUDENT_NAME", "Swati Melkani"),
            "student_branch": app.config.get("STUDENT_BRANCH", "CSE - B"),
            "course_name": app.config.get("COURSE_NAME", "BBAT104 — Fundamentals of TQM"),
            "academic_session": app.config.get("ACADEMIC_SESSION", "2026–27"),
            "assigned_goal": app.config.get("ASSIGNED_GOAL", "Q11 — Improve Maintainability"),
        }

    # 6. Centralized HTTP Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal server error encountered: {e}", exc_info=True)
        return render_template("errors/500.html"), 500

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("errors/400.html", message=str(e)), 400

    # 7. Register Modular Blueprints
    register_routes(app)

    logger.info("All modular route blueprints successfully mounted.")
    return app
