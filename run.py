"""Application Entry Point.

Restaurant Billing System — TQM Q11: Improve Maintainability
Student: Swati Melkani
Branch: CSE, Section: B
Course: BBAT104 — Fundamentals of Total Quality Management (TQM)
Academic Session: 2026–27
Assigned Quality Goal: Q11 — Improve Maintainability

Usage:
    python run.py
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    host = app.config.get("HOST", "127.0.0.1")
    port = app.config.get("PORT", 5000)
    debug = app.config.get("DEBUG", True)

    print("=" * 72)
    print("  RESTAURANT BILLING SYSTEM — TQM Q11: IMPROVE MAINTAINABILITY")
    print("  Student: Swati Melkani | CSE - Section B | Academic Session: 2026-27")
    print("  Course : BBAT104 — Fundamentals of Total Quality Management (TQM)")
    print(f"  Status : Running at http://{host}:{port}/")
    print("=" * 72)

    app.run(host=host, port=port, debug=debug)
