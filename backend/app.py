"""
app.py — Flask backend API untuk WebGIS Stunting
Menyediakan endpoint GeoJSON dari PostgreSQL/PostGIS
"""

from flask import Flask, jsonify
from flask_cors import CORS
from config import DB_CONFIG
import psycopg2
import psycopg2.extras
import json
import os
import uuid
import datetime

# Laporan data is now queried dynamically from PostgreSQL 'laporan' table.
FALLBACK_REPORTS = [
    {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [104.9110, -5.4240]},
        "properties": {
            "id": "demo-1", "pelapor": "Budi Santoso (Kader)",
            "judul": "Indikasi Gizi Buruk",
            "deskripsi": "Terdapat anak usia 2 tahun yang berat badannya tidak naik selama 3 bulan.",
            "lat": -5.4240, "lng": 104.9110,
            "status": "pending", "tanggal": "2024-05-12T10:00:00Z"
        }
    }
]

def get_fallback_geojson():
    """Membaca data GeoJSON lokal jika database tidak terhubung"""
    try:
        path = os.path.join(os.path.dirname(__file__), "kresnomulyo_webgis.geojson")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading fallback geojson: {e}")
        return None

import time

# Reusable shared database connection
_shared_conn = None

class SharedConnectionWrapper:
    """Wrapper agar pemanggilan conn.close() tidak memutus koneksi fisik database"""
    def __init__(self, real_conn):
        self.real_conn = real_conn
    def cursor(self, *args, **kwargs):
        return self.real_conn.cursor(*args, **kwargs)
    def commit(self):
        self.real_conn.commit()
    def rollback(self):
        self.real_conn.rollback()
    def close(self):
        # Sengaja tidak menutup koneksi fisik agar bisa dipakai lagi
        pass

# Cache data structure
API_CACHE = {
    "wilayah": {"data": None, "timestamp": 0},
    "posyandu": {"data": None, "timestamp": 0},
    "faskes": {"data": None, "timestamp": 0},
    "statistik": {"data": None, "timestamp": 0},
    "laporan": {"data": None, "timestamp": 0}
}
CACHE_TTL = 15  # Cache time-to-live in seconds

def get_cached_data(key):
    """Mengambil data dari cache jika masih fresh (di bawah TTL)"""
    cache_item = API_CACHE.get(key)
    if cache_item and cache_item["data"] is not None:
        if time.time() - cache_item["timestamp"] < CACHE_TTL:
            return cache_item["data"]
    return None

def set_cached_data(key, data):
    """Menyimpan data ke cache dengan timestamp saat ini"""
    API_CACHE[key] = {
        "data": data,
        "timestamp": time.time()
    }

def clear_api_cache():
    """Menghapus semua cache saat terjadi pembaruan data (POST/DELETE)"""
    for key in API_CACHE:
        API_CACHE[key]["data"] = None
        API_CACHE[key]["timestamp"] = 0

app = Flask(__name__)
CORS(app)


# === HELPER: Koneksi database ===
def get_db():
    """Membuka koneksi ke database PostgreSQL/PostGIS dengan re-use koneksi"""
    global _shared_conn
    
    # Cek apakah koneksi lama masih hidup menggunakan SELECT 1
    if _shared_conn is not None:
        try:
            with _shared_conn.cursor() as test_cur:
                test_cur.execute("SELECT 1")
        except Exception:
            # Jika mati, tutup fisik dan set None agar dibuka kembali
            try:
                _shared_conn.close()
            except Exception:
                pass
            _shared_conn = None

    # Buka koneksi baru jika belum ada atau terputus
    if _shared_conn is None or _shared_conn.closed != 0:
        _shared_conn = psycopg2.connect(**DB_CONFIG)
        
    return SharedConnectionWrapper(_shared_conn)



# === HELPER: Hitung prevalensi stunting ===
def hitung_prev(jml_stunt, jml_balita):
    """Menghitung prevalensi stunting dalam persen"""
    if jml_balita == 0:
        return 0.0
    return round((jml_stunt / jml_balita) * 100, 2)


# === HELPER: Klasifikasi kategori stunting ===
def klasifikasi_stunting(prev):
    """Menentukan kategori stunting berdasarkan prevalensi"""
    if prev < 10:
        return "Rendah"
    elif prev < 20:
        return "Sedang"
    elif prev < 30:
        return "Tinggi"
    else:
        return "Sangat Tinggi"


# === HELPER: Hitung skor kerentanan ===
def hitung_sk_rentan(prev_stunt, bansos, jml_balita, sanitasi):
    """
    Skor kerentanan = (prev_stunt/100)*0.4 + (bansos/jml_balita)*0.3
                      + ((100-sanitasi)/100)*0.3
    """
    if jml_balita == 0:
        return 0.0
    skor = (prev_stunt / 100) * 0.4 \
         + (bansos / jml_balita) * 0.3 \
         + ((100 - sanitasi) / 100) * 0.3
    return round(skor, 4)


# === HELPER: Klasifikasi kerentanan ===
def klasifikasi_rentan(sk):
    """Menentukan kategori kerentanan berdasarkan skor"""
    if sk < 0.2:
        return "Aman"
    elif sk < 0.35:
        return "Waspada"
    elif sk < 0.5:
        return "Rentan"
    else:
        return "Sangat Rentan"


# === HELPER: Bangun properti lengkap dari row ===
def build_properties(row):
    """Membangun dict properti lengkap dari satu row database"""
    prev = hitung_prev(row["jml_stunt"], row["jml_balita"])
    sk = hitung_sk_rentan(prev, row["bansos"], row["jml_balita"], row["sanitasi"])
    return {
        "kode_wil":   row["kode_wil"],
        "nama_wil":   row["nama_wil"],
        "jenis_wil":  row["jenis_wil"],
        "jml_balita": row["jml_balita"],
        "jml_stunt":  row["jml_stunt"],
        "prev_stunt": prev,
        "kat_stunt":  klasifikasi_stunting(prev),
        "kat_ekon":   row["kat_ekon"],
        "air_bersih": float(row["air_bersih"]),
        "sanitasi":   float(row["sanitasi"]),
        "jamban":     float(row["jamban"]),
        "bansos":     row["bansos"],
        "jml_posyan": row["jml_posyan"],
        "sk_rentan":  sk,
        "kat_rentan": klasifikasi_rentan(sk),
        "tahun":      row.get("tahun", 2024),
        "sumber":     row.get("sumber", "Puskesmas Ambarawa")
    }


# ============================================================
# ENDPOINT: GET /api/wilayah — Semua wilayah sebagai GeoJSON
# ============================================================
@app.route("/api/wilayah", methods=["GET"])
def get_wilayah():
    """Mengembalikan GeoJSON FeatureCollection semua wilayah"""
    cached = get_cached_data("wilayah")
    if cached is not None:
        return jsonify(cached)

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT kode_wil, nama_wil, jenis_wil,
                   jml_balita, jml_stunt, kat_ekon,
                   air_bersih, sanitasi, jamban,
                   bansos, jml_posyan, tahun, sumber,
                   ST_AsGeoJSON(geom)::json AS geometry
            FROM wilayah
            ORDER BY kode_wil
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        features = []
        for row in rows:
            feat = {
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": build_properties(row)
            }
            features.append(feat)

        result = {
            "type": "FeatureCollection",
            "features": features
        }
        set_cached_data("wilayah", result)
        return jsonify(result)

    except Exception as e:
        print(f"Database error in get_wilayah, trying fallback: {e}")
        fallback_data = get_fallback_geojson()
        if fallback_data:
            return jsonify(fallback_data)
        return jsonify({"error": str(e)}), 500


# ============================================================
# ENDPOINT: POST /api/wilayah/update — Update data wilayah (CSV Import)
# ============================================================
@app.route("/api/wilayah/update", methods=["POST"])
def update_wilayah_data():
    from flask import request
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Data kosong"}), 400

        # Coba update database PostgreSQL jika tersambung
        db_connected = False
        try:
            conn = get_db()
            cur = conn.cursor()
            for row in data:
                update_fields = []
                params = []
                for field in ['jml_balita', 'jml_stunt', 'air_bersih', 'sanitasi', 'jamban', 'bansos', 'jml_posyan', 'tahun', 'sumber']:
                    if field in row:
                        update_fields.append(f"{field} = %s")
                        params.append(row[field])
                
                if update_fields and 'kode_wil' in row:
                    params.append(row['kode_wil'])
                    cur.execute(f"""
                        UPDATE wilayah
                        SET {', '.join(update_fields)}
                        WHERE kode_wil = %s
                    """, tuple(params))
            conn.commit()
            cur.close()
            conn.close()
            db_connected = True
        except Exception as db_err:
            print(f"Gagal update PostgreSQL: {db_err}")

        # Selalu update file fallback GeoJSON jika ada agar sinkron
        try:
            path = os.path.join(os.path.dirname(__file__), "kresnomulyo_webgis.geojson")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    geojson_data = json.load(f)
                
                # Update features
                updated_count = 0
                for row in data:
                    row_kode = str(row.get("kode_wil", "")).strip().lower()
                    row_nama = str(row.get("nama_wil", "")).strip().lower()
                    
                    for feat in geojson_data.get("features", []):
                        p = feat["properties"]
                        f_kode = str(p.get("kode_wil", "")).strip().lower()
                        f_nama = str(p.get("nama_wil", "")).strip().lower()
                        
                        if (row_kode and f_kode == row_kode) or (row_nama and f_nama == row_nama):
                            # Update fields
                            for field in ['jml_balita', 'jml_stunt', 'air_bersih', 'sanitasi', 'jamban', 'bansos', 'jml_posyan', 'tahun', 'sumber']:
                                if field in row:
                                    p[field] = row[field]
                            
                            # Hitung prevalensi stunting dll.
                            p["prev_stunt"] = hitung_prev(p["jml_stunt"], p["jml_balita"])
                            p["kat_stunt"] = klasifikasi_stunting(p["prev_stunt"])
                            p["sk_rentan"] = hitung_sk_rentan(p["prev_stunt"], p.get("bansos", 0), p["jml_balita"], p.get("sanitasi", 0))
                            p["kat_rentan"] = klasifikasi_rentan(p["sk_rentan"])
                            updated_count += 1
                
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(geojson_data, f, ensure_ascii=False, indent=2)
        except Exception as file_err:
            print(f"Gagal update fallback GeoJSON: {file_err}")

        clear_api_cache()
        return jsonify({"status": "success", "message": "Data wilayah berhasil diperbarui"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ============================================================
# ENDPOINT: GET /api/wilayah/<kode> — Detail satu wilayah
# ============================================================
@app.route("/api/wilayah/<kode>", methods=["GET"])
def get_wilayah_detail(kode):
    """Mengembalikan GeoJSON Feature detail satu wilayah"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT kode_wil, nama_wil, jenis_wil,
                   jml_balita, jml_stunt, kat_ekon,
                   air_bersih, sanitasi, jamban,
                   bansos, jml_posyan, tahun, sumber,
                   ST_AsGeoJSON(geom)::json AS geometry
            FROM wilayah
            WHERE kode_wil = %s
        """, (kode,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return jsonify({"error": "Wilayah tidak ditemukan"}), 404

        return jsonify({
            "type": "Feature",
            "geometry": row["geometry"],
            "properties": build_properties(row)
        })

    except Exception as e:
        print(f"Database error in get_wilayah_detail, trying fallback: {e}")
        fallback_data = get_fallback_geojson()
        if fallback_data:
            for feat in fallback_data.get("features", []):
                if feat["properties"]["kode_wil"] == kode:
                    return jsonify(feat)
            return jsonify({"error": "Wilayah tidak ditemukan (fallback)"}), 404
        return jsonify({"error": str(e)}), 500


# ============================================================
# ENDPOINT: GET /api/posyandu — Titik posyandu sebagai GeoJSON
# ============================================================
@app.route("/api/posyandu", methods=["GET"])
def get_posyandu():
    """Mengembalikan GeoJSON FeatureCollection titik posyandu"""
    cached = get_cached_data("posyandu")
    if cached is not None:
        return jsonify(cached)

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT nama, alamat,
                   ST_AsGeoJSON(geom)::json AS geometry
            FROM posyandu
            ORDER BY nama
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        features = []
        for row in rows:
            feat = {
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {
                    "nama": row["nama"],
                    "alamat": row.get("alamat", "-")
                }
            }
            features.append(feat)

        result = {
            "type": "FeatureCollection",
            "features": features
        }
        set_cached_data("posyandu", result)
        return jsonify(result)

    except Exception as e:
        print(f"Database error in get_posyandu, trying fallback: {e}")
        return jsonify({
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [104.9050, -5.4235]},
                    "properties": {"nama": "Posyandu Kenanga", "alamat": "Sumber Sari"}
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [104.9155, -5.4295]},
                    "properties": {"nama": "Posyandu Cempaka", "alamat": "Karang Anyar"}
                }
            ]
        })


# ============================================================
# ENDPOINT: GET /api/faskes — Titik fasilitas kesehatan
# ============================================================
@app.route("/api/faskes", methods=["GET"])
def get_faskes():
    """Mengembalikan GeoJSON FeatureCollection fasilitas kesehatan"""
    cached = get_cached_data("faskes")
    if cached is not None:
        return jsonify(cached)

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT nama, jenis, alamat,
                   ST_AsGeoJSON(geom)::json AS geometry
            FROM faskes
            ORDER BY nama
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        features = []
        for row in rows:
            feat = {
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {
                    "nama": row["nama"],
                    "jenis": row.get("jenis", "-"),
                    "alamat": row.get("alamat", "-")
                }
            }
            features.append(feat)

        result = {
            "type": "FeatureCollection",
            "features": features
        }
        set_cached_data("faskes", result)
        return jsonify(result)

    except Exception as e:
        print(f"Database error in get_faskes, trying fallback: {e}")
        return jsonify({
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [104.9165, -5.4205]},
                    "properties": {"nama": "Puskesmas Pembantu Ambarawa", "jenis": "Puskesmas Pembantu", "alamat": "Jl. Raya Kresnomulyo"}
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [104.91738742007512, -5.420160252847154]},
                    "properties": {"nama": "Poskesdes Kresnomulyo Barat", "jenis": "Poskesdes", "alamat": "Pekon Kresnomulyo Barat"}
                }
            ]
        })


# ============================================================
# ENDPOINT: GET /api/statistik — Ringkasan statistik
# ============================================================
@app.route("/api/statistik", methods=["GET"])
def get_statistik():
    """Mengembalikan JSON ringkasan statistik stunting"""
    cached = get_cached_data("statistik")
    if cached is not None:
        return jsonify(cached)

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT kode_wil, nama_wil, jml_balita, jml_stunt,
                   air_bersih, sanitasi, bansos
            FROM wilayah
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Hitung statistik agregat
        total_balita = sum(r["jml_balita"] for r in rows)
        total_stunt = sum(r["jml_stunt"] for r in rows)
        prev_total = round((total_stunt / total_balita) * 100, 2) if total_balita > 0 else 0
        rata_air = round(sum(float(r["air_bersih"]) for r in rows) / len(rows), 1) if rows else 0
        rata_san = round(sum(float(r["sanitasi"]) for r in rows) / len(rows), 1) if rows else 0

        # Klasifikasi per wilayah
        kat_rendah = 0
        kat_sedang = 0
        kat_tinggi = 0
        kat_sangat = 0
        rentan_list = []

        for r in rows:
            prev = hitung_prev(r["jml_stunt"], r["jml_balita"])
            kat = klasifikasi_stunting(prev)
            if kat == "Rendah":
                kat_rendah += 1
            elif kat == "Sedang":
                kat_sedang += 1
            elif kat == "Tinggi":
                kat_tinggi += 1
            else:
                kat_sangat += 1

            sk = hitung_sk_rentan(prev, r["bansos"], r["jml_balita"], float(r["sanitasi"]))
            rentan_list.append({
                "nama_wil":   r["nama_wil"],
                "prev_stunt": prev,
                "sk_rentan":  sk,
                "kat_rentan": klasifikasi_rentan(sk)
            })

        # Top 3 wilayah paling rentan
        rentan_list.sort(key=lambda x: x["sk_rentan"], reverse=True)
        top_rentan = rentan_list[:3]

        result = {
            "total_balita":  total_balita,
            "total_stunting": total_stunt,
            "prev_total":    prev_total,
            "rata_air":      rata_air,
            "rata_sanitasi": rata_san,
            "total_wilayah": len(rows),
            "kat_rendah":    kat_rendah,
            "kat_sedang":    kat_sedang,
            "kat_tinggi":    kat_tinggi,
            "kat_sangat":    kat_sangat,
            "top_rentan":    top_rentan
        }
        set_cached_data("statistik", result)
        return jsonify(result)

    except Exception as e:
        print(f"Database error in get_statistik, trying fallback: {e}")
        fallback_data = get_fallback_geojson()
        if fallback_data:
            features = fallback_data.get("features", [])
            total_balita = sum(f["properties"]["jml_balita"] for f in features)
            total_stunt = sum(f["properties"]["jml_stunt"] for f in features)
            prev_total = round((total_stunt / total_balita) * 100, 2) if total_balita > 0 else 0
            rata_air = round(sum(f["properties"]["air_bersih"] for f in features) / len(features), 1) if features else 0
            rata_san = round(sum(f["properties"]["sanitasi"] for f in features) / len(features), 1) if features else 0

            kat_rendah = sum(1 for f in features if f["properties"]["kat_stunt"] == "Rendah")
            kat_sedang = sum(1 for f in features if f["properties"]["kat_stunt"] == "Sedang")
            kat_tinggi = sum(1 for f in features if f["properties"]["kat_stunt"] == "Tinggi")
            kat_sangat = sum(1 for f in features if f["properties"]["kat_stunt"] == "Sangat Tinggi")

            rentan_list = [{
                "nama_wil": f["properties"]["nama_wil"],
                "prev_stunt": f["properties"]["prev_stunt"],
                "sk_rentan": f["properties"]["sk_rentan"],
                "kat_rentan": f["properties"]["kat_rentan"]
            } for f in features]
            rentan_list.sort(key=lambda x: x["sk_rentan"], reverse=True)

            return jsonify({
                "total_balita":  total_balita,
                "total_stunting": total_stunt,
                "prev_total":    prev_total,
                "rata_air":      rata_air,
                "rata_sanitasi": rata_san,
                "total_wilayah": len(features),
                "kat_rendah":    kat_rendah,
                "kat_sedang":    kat_sedang,
                "kat_tinggi":    kat_tinggi,
                "kat_sangat":    kat_sangat,
                "top_rentan":    rentan_list[:3]
            })
        return jsonify({"error": str(e)}), 500


# ============================================================
# ENDPOINT: GET/POST /api/laporan — Form Laporan Masyarakat
# ============================================================
@app.route("/api/laporan", methods=["GET", "POST"])
def api_laporan():
    from flask import request
    if request.method == "GET":
        cached = get_cached_data("laporan")
        if cached is not None:
            return jsonify(cached)

        try:
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT id, pelapor, judul, deskripsi, 
                       lat, lng, status, tanggal
                FROM laporan
                ORDER BY tanggal DESC
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            features = []
            for row in rows:
                lat_val = float(row["lat"])
                lng_val = float(row["lng"])
                if isinstance(row["tanggal"], (datetime.datetime, datetime.date)):
                    tgl_str = row["tanggal"].isoformat() + "Z"
                else:
                    tgl_str = str(row["tanggal"])

                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lng_val, lat_val]
                    },
                    "properties": {
                        "id": row["id"],
                        "pelapor": row["pelapor"],
                        "judul": row["judul"],
                        "deskripsi": row["deskripsi"],
                        "lat": lat_val,
                        "lng": lng_val,
                        "status": row["status"],
                        "tanggal": tgl_str
                    }
                })
            result = {
                "type": "FeatureCollection",
                "features": features
            }
            set_cached_data("laporan", result)
            return jsonify(result)
        except Exception as e:
            print(f"Error getting reports from DB, using fallback: {e}")
            # Fallback jika database belum dimigrasi / error
            return jsonify({
                "type": "FeatureCollection",
                "features": FALLBACK_REPORTS
            })

    elif request.method == "POST":
        data = request.json
        if not data:
            return jsonify({"error": "Data kosong"}), 400
            
        new_id = str(uuid.uuid4())
        pelapor = data.get("pelapor", "Anonim")
        judul = data.get("judul", "Laporan Tanpa Judul")
        deskripsi = data.get("deskripsi", "")
        lat = float(data.get("lat", 0))
        lng = float(data.get("lng", 0))
        status = "pending"
        tanggal = datetime.datetime.now()

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO laporan (id, pelapor, judul, deskripsi, lat, lng, status, tanggal)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (new_id, pelapor, judul, deskripsi, lat, lng, status, tanggal))
            conn.commit()
            cur.close()
            conn.close()

            clear_api_cache()
            return jsonify({
                "status": "success", 
                "data": {
                    "id": new_id,
                    "pelapor": pelapor,
                    "judul": judul,
                    "deskripsi": deskripsi,
                    "lat": lat,
                    "lng": lng,
                    "status": status,
                    "tanggal": tanggal.isoformat() + "Z"
                }
            })
        except Exception as e:
            print(f"Error saving report to DB, using fallback: {e}")
            # Fallback (save to memory so UI works)
            new_report = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lng, lat]},
                "properties": {
                    "id": new_id, "pelapor": pelapor, "judul": judul, "deskripsi": deskripsi,
                    "lat": lat, "lng": lng, "status": status, "tanggal": tanggal.isoformat() + "Z"
                }
            }
            FALLBACK_REPORTS.insert(0, new_report)
            clear_api_cache()
            return jsonify({
                "status": "success", 
                "data": new_report["properties"]
            })

@app.route("/api/laporan/<laporan_id>/verifikasi", methods=["POST"])
def verify_laporan(laporan_id):
    from flask import request
    data = request.json
    status = data.get("status", "verified") # bisa 'verified' atau 'rejected'
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE laporan
            SET status = %s
            WHERE id = %s
        """, (status, laporan_id))
        conn.commit()
        rowcount = cur.rowcount
        cur.close()
        conn.close()

        if rowcount == 0:
            return jsonify({"error": "Laporan tidak ditemukan"}), 404

        clear_api_cache()
        return jsonify({"status": "success", "message": f"Status laporan diubah menjadi {status}"})
    except Exception as e:
        print(f"Error verifying report in DB, using fallback: {e}")
        # Fallback to in-memory list
        for report in FALLBACK_REPORTS:
            if report["properties"]["id"] == laporan_id:
                report["properties"]["status"] = status
                clear_api_cache()
                return jsonify({"status": "success", "message": f"Status laporan diubah menjadi {status} (Fallback)"})
        return jsonify({"error": "Laporan tidak ditemukan (Fallback)"}), 404

@app.route("/api/laporan/<laporan_id>", methods=["DELETE"])
def delete_laporan_endpoint(laporan_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM laporan
            WHERE id = %s
        """, (laporan_id,))
        conn.commit()
        rowcount = cur.rowcount
        cur.close()
        conn.close()

        if rowcount == 0:
            return jsonify({"error": "Laporan tidak ditemukan"}), 404

        clear_api_cache()
        return jsonify({"status": "success", "message": "Laporan berhasil dihapus"})
    except Exception as e:
        print(f"Error deleting report from DB, using fallback: {e}")
        # Fallback to in-memory list
        for i, report in enumerate(FALLBACK_REPORTS):
            if report["properties"]["id"] == laporan_id:
                del FALLBACK_REPORTS[i]
                clear_api_cache()
                return jsonify({"status": "success", "message": "Laporan berhasil dihapus (Fallback)"})
        return jsonify({"error": "Laporan tidak ditemukan (Fallback)"}), 404


# === Main entry point ===
if __name__ == "__main__":
    print("[GIS] WebGIS Stunting API -- http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
