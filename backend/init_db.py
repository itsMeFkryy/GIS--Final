import json
import os
import sys
import psycopg2
from config import DB_CONFIG

def init_db():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
    except Exception as e:
        print(f"Error: Gagal terhubung ke database. Cek config.py atau pastikan PostgreSQL berjalan.\\nDetail: {e}")
        sys.exit(1)

    print("Enabling PostGIS extension...")
    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    except Exception as e:
        print(f"Error: Gagal mengaktifkan ekstensi PostGIS. Pastikan database user memiliki hak superuser.\\nDetail: {e}")
        sys.exit(1)

    # 1. Wilayah table
    print("Re-creating table 'wilayah'...")
    cur.execute("DROP TABLE IF EXISTS wilayah CASCADE;")
    cur.execute("""
        CREATE TABLE wilayah (
            kode_wil VARCHAR(50) PRIMARY KEY,
            nama_wil VARCHAR(100) NOT NULL,
            jenis_wil VARCHAR(50),
            jml_balita INTEGER DEFAULT 0,
            jml_stunt INTEGER DEFAULT 0,
            kat_ekon VARCHAR(50),
            air_bersih NUMERIC DEFAULT 0,
            sanitasi NUMERIC DEFAULT 0,
            jamban NUMERIC DEFAULT 0,
            bansos INTEGER DEFAULT 0,
            jml_posyan INTEGER DEFAULT 0,
            tahun INTEGER,
            sumber VARCHAR(150),
            geom GEOMETRY(Geometry, 4326)
        );
    """)
    cur.execute("CREATE INDEX wilayah_geom_idx ON wilayah USING GIST (geom);")

    # 2. Posyandu table
    print("Re-creating table 'posyandu'...")
    cur.execute("DROP TABLE IF EXISTS posyandu CASCADE;")
    cur.execute("""
        CREATE TABLE posyandu (
            id SERIAL PRIMARY KEY,
            nama VARCHAR(100) NOT NULL,
            alamat TEXT,
            geom GEOMETRY(Point, 4326)
        );
    """)
    cur.execute("CREATE INDEX posyandu_geom_idx ON posyandu USING GIST (geom);")

    # 3. Faskes table
    print("Re-creating table 'faskes'...")
    cur.execute("DROP TABLE IF EXISTS faskes CASCADE;")
    cur.execute("""
        CREATE TABLE faskes (
            id SERIAL PRIMARY KEY,
            nama VARCHAR(100) NOT NULL,
            jenis VARCHAR(100),
            alamat TEXT,
            geom GEOMETRY(Point, 4326)
        );
    """)
    cur.execute("CREATE INDEX faskes_geom_idx ON faskes USING GIST (geom);")

    geojson_path = os.path.join(os.path.dirname(__file__), "kresnomulyo_webgis.geojson")
    if not os.path.exists(geojson_path):
        print(f"Error: File geojson tidak ditemukan di {geojson_path}")
        sys.exit(1)

    print(f"Loading geojson boundaries from {geojson_path}...")
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    inserted_wilayah = 0
    for feat in geojson_data.get("features", []):
        p = feat["properties"]
        geom_json = json.dumps(feat["geometry"])
        
        cur.execute("""
            INSERT INTO wilayah (
                kode_wil, nama_wil, jenis_wil, jml_balita, jml_stunt,
                kat_ekon, air_bersih, sanitasi, jamban, bansos,
                jml_posyan, tahun, sumber, geom
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
            )
        """, (
            p.get("kode_wil"), p.get("nama_wil"), p.get("jenis_wil"), p.get("jml_balita", 0), p.get("jml_stunt", 0),
            p.get("kat_ekon"), p.get("air_bersih", 0), p.get("sanitasi", 0), p.get("jamban", 0), p.get("bansos", 0),
            p.get("jml_posyan", 0), p.get("tahun"), p.get("sumber"), geom_json
        ))
        inserted_wilayah += 1

    print(f"Successfully inserted {inserted_wilayah} wilayah records.")

    # Populate default Posyandu points
    print("Inserting default posyandu points...")
    default_posyandu = [
        {"nama": "Posyandu Kenanga", "alamat": "Sumber Sari", "lng": 104.9050, "lat": -5.4235},
        {"nama": "Posyandu Cempaka", "alamat": "Karang Anyar", "lng": 104.9155, "lat": -5.4295}
    ]
    for pos in default_posyandu:
        geom_pt = json.dumps({"type": "Point", "coordinates": [pos["lng"], pos["lat"]]})
        cur.execute("""
            INSERT INTO posyandu (nama, alamat, geom)
            VALUES (%s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
        """, (pos["nama"], pos["alamat"], geom_pt))

    # Populate default Faskes points
    print("Inserting default faskes points...")
    default_faskes = [
        {"nama": "Puskesmas Pembantu Ambarawa", "jenis": "Puskesmas Pembantu", "alamat": "Jl. Raya Kresnomulyo", "lng": 104.9165, "lat": -5.4205},
        {"nama": "Poskesdes Kresnomulyo Barat", "jenis": "Poskesdes", "alamat": "Pekon Kresnomulyo Barat", "lng": 104.91738742007512, "lat": -5.420160252847154}
    ]
    for fas in default_faskes:
        geom_pt = json.dumps({"type": "Point", "coordinates": [fas["lng"], fas["lat"]]})
        cur.execute("""
            INSERT INTO faskes (nama, jenis, alamat, geom)
            VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
        """, (fas["nama"], fas["jenis"], fas["alamat"], geom_pt))

    cur.close()
    conn.close()
    print("Database initialization completed successfully!")

if __name__ == "__main__":
    init_db()
