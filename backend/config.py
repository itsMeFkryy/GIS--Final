"""
config.py — Konfigurasi koneksi database PostgreSQL/PostGIS
Bisa di-override dengan environment variable DB_PASSWORD
"""

import os

# Konfigurasi koneksi database PostgreSQL/PostGIS
DB_CONFIG = {
    "dbname": "stunting_gis",
    "user": "postgres",
    "password": "123",
    "host": "localhost",
    "port": 5432
}
