"""
config.py — Konfigurasi koneksi database PostgreSQL/PostGIS
Bisa di-override dengan environment variable DB_PASSWORD
"""

import os

# Konfigurasi koneksi database PostgreSQL/PostGIS
DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "stunting_gis"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "123"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "connect_timeout": 5
}
