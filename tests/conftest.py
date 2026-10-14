"""Pytest Test Configuration and Fixtures.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides:
- Fully isolated in-memory test database for automated testing, ensuring tests
  never alter or corrupt development or production database files.
- Pre-seeded test fixtures for menu items, draft orders, and settings.
"""

from __future__ import annotations

import os
import sqlite3
import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.database.connection import create_connection
from app.database.migrations import init_db, seed_default_settings


@pytest.fixture
def app() -> Flask:
    """Create Flask test application configured for isolated testing."""
    os.environ["FLASK_ENV"] = "testing"
    test_app = create_app("testing")
    return test_app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Provide Flask test client for HTTP requests."""
    return app.test_client()


@pytest.fixture
def db_conn() -> sqlite3.Connection:
    """Provide a fresh in-memory SQLite database connection with initialized schema."""
    conn = create_connection(":memory:")
    init_db(conn)
    seed_default_settings(conn)
    yield conn
    conn.close()
