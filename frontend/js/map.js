/**
 * map.js — Leaflet Map Controller untuk WebGIS Stunting
 * Pekon Kresnomulyo Barat, Kec. Ambarawa, Kab. Pringsewu
 *
 * Fitur:
 * - Choropleth wilayah dari API (PostGIS) dengan fallback GeoJSON lokal
 * - Marker posyandu & faskes
 * - Interaksi: hover highlight, click popup + panel detail
 * - Pemilihan indikator: prev_stunt, air_bersih, sanitasi, sk_rentan
 */

// === Konfigurasi ===
const API_BASE = window.API_BASE_URL || 'http://localhost:5000/api';

// === State global ===
let map, wilayahLayer, posyanduLayer, faskesLayer, laporanLayer;
let currentIndikator = 'prev_stunt';
var wilayahData = null;
window.wilayahData = null;

// ============================================================
// INISIALISASI PETA
// ============================================================
function initMap() {
    // Center: Pekon Kresnomulyo Barat area
    map = L.map('map', {
        center: [-5.370, 104.975],
        zoom: 14,
        zoomControl: false,
        attributionControl: true
    });

    // Basemap tile layer is managed by theme.js
    Theme.registerMap(map);

    // Init layer groups
    posyanduLayer = L.layerGroup().addTo(map);
    faskesLayer = L.layerGroup().addTo(map);
    laporanLayer = L.layerGroup().addTo(map);

    // Auto-refresh laporan every 30 seconds
    setInterval(loadLaporan, 30000);
}


// ============================================================
// WARNA CHOROPLETH — berdasarkan indikator aktif
// ============================================================
function getWarna(nilai, indikator) {
    switch (indikator) {
        case 'prev_stunt':
            // Klasifikasi stunting
            if (nilai >= 30) return '#bd0026';
            if (nilai >= 20) return '#fd8d3c';
            if (nilai >= 10) return '#fed976';
            return '#ffffcc';

        case 'air_bersih':
            // Makin tinggi makin baik → hijau
            if (nilai >= 85) return '#2ecc71';
            if (nilai >= 70) return '#82e0aa';
            if (nilai >= 55) return '#f9e79f';
            return '#e74c3c';

        case 'sanitasi':
            // Makin tinggi makin baik → hijau
            if (nilai >= 80) return '#2ecc71';
            if (nilai >= 65) return '#82e0aa';
            if (nilai >= 50) return '#f9e79f';
            return '#e74c3c';

        case 'sk_rentan':
            // Makin tinggi makin rentan → merah
            if (nilai >= 0.5) return '#bd0026';
            if (nilai >= 0.35) return '#fd8d3c';
            if (nilai >= 0.2) return '#fed976';
            return '#ffffcc';

        default:
            return '#95a5a6';
    }
}


// ============================================================
// STYLE POLYGON WILAYAH
// ============================================================
function styleWilayah(feature) {
    const props = feature.properties;
    const nilai = props[currentIndikator] || 0;
    return {
        fillColor: getWarna(nilai, currentIndikator),
        weight: 2,
        opacity: 1,
        color: 'rgba(30, 41, 59, 0.35)',
        dashArray: '',
        fillOpacity: 0.7
    };
}

// Style saat hover
function highlightStyle() {
    return {
        weight: 3,
        color: '#1E293B',
        fillOpacity: 0.9,
        dashArray: ''
    };
}


// ============================================================
// BADGE HELPER
// ============================================================
function getBadgeClass(kat_stunt) {
    switch (kat_stunt) {
        case 'Rendah': return 'badge-rendah';
        case 'Sedang': return 'badge-sedang';
        case 'Tinggi': return 'badge-tinggi';
        case 'Sangat Tinggi': return 'badge-sangat';
        default: return 'badge-sedang';
    }
}

function getRentanBadgeClass(kat_rentan) {
    switch (kat_rentan) {
        case 'Aman': return 'badge-aman';
        case 'Waspada': return 'badge-waspada';
        case 'Rentan': return 'badge-rentan';
        case 'Sangat Rentan': return 'badge-sangat-rentan';
        default: return 'badge-waspada';
    }
}


// ============================================================
// POPUP CONTENT
// ============================================================
function buildPopup(props) {
    return `
        <div class="popup-title">${props.nama_wil}</div>
        <div class="popup-row"><span class="lbl">Balita</span><span class="val">${props.jml_balita}</span></div>
        <div class="popup-row"><span class="lbl">Stunting</span><span class="val">${props.jml_stunt}</span></div>
        <div class="popup-row"><span class="lbl">Prevalensi</span><span class="val">${props.prev_stunt}%</span></div>
        <div class="popup-row"><span class="lbl">Kategori</span><span class="val"><span class="kategori-badge ${getBadgeClass(props.kat_stunt)}">${props.kat_stunt}</span></span></div>
        <div class="popup-row"><span class="lbl">Air Bersih</span><span class="val">${props.air_bersih}%</span></div>
        <div class="popup-row"><span class="lbl">Sanitasi</span><span class="val">${props.sanitasi}%</span></div>
        <div class="popup-row"><span class="lbl">Kerentanan</span><span class="val"><span class="kategori-badge ${getRentanBadgeClass(props.kat_rentan)}">${props.kat_rentan}</span></span></div>
    `;
}


// ============================================================
// PANEL DETAIL KANAN — Semua field lengkap
// ============================================================
function showDetail(props) {
    const el = document.getElementById('detail-content');
    el.innerHTML = `
        <div class="detail-header">
            <h3>${props.nama_wil}</h3>
            <div class="detail-sub">${props.jenis_wil} • ${props.kode_wil}</div>
        </div>
        <table class="detail-table">
            <tr><td>Kode</td><td>${props.kode_wil}</td></tr>
            <tr><td>Jenis</td><td>${props.jenis_wil}</td></tr>
            <tr><td>Balita</td><td>${props.jml_balita} anak</td></tr>
            <tr><td>Stunting</td><td>${props.jml_stunt} anak</td></tr>
            <tr><td>Prevalensi</td><td><strong>${props.prev_stunt}%</strong></td></tr>
            <tr><td>Kategori</td><td><span class="kategori-badge ${getBadgeClass(props.kat_stunt)}">${props.kat_stunt}</span></td></tr>
            <tr><td>Ekonomi</td><td>${props.kat_ekon}</td></tr>
            <tr><td>Air Bersih</td><td>${props.air_bersih}%</td></tr>
            <tr><td>Sanitasi</td><td>${props.sanitasi}%</td></tr>
            <tr><td>Jamban</td><td>${props.jamban}%</td></tr>
            <tr><td>Bansos</td><td>${props.bansos} KK</td></tr>
            <tr><td>Posyandu</td><td>${props.jml_posyan} unit</td></tr>
            <tr><td>Skor Rentan</td><td><strong>${props.sk_rentan}</strong></td></tr>
            <tr><td>Kat. Rentan</td><td><span class="kategori-badge ${getRentanBadgeClass(props.kat_rentan)}">${props.kat_rentan}</span></td></tr>
            <tr><td>Tahun</td><td>${props.tahun}</td></tr>
            <tr><td>Sumber</td><td>${props.sumber}</td></tr>
        </table>
    `;
}


// ============================================================
// onEachFeature — Interaksi hover & click
// ============================================================
function onEachFeature(feature, layer) {
    const props = feature.properties;

    // Popup
    layer.bindPopup(buildPopup(props), { maxWidth: 280 });

    layer.on({
        // Mouseover → highlight
        mouseover: function (e) {
            const lyr = e.target;
            lyr.setStyle(highlightStyle());
            lyr.bringToFront();
        },

        // Mouseout → reset
        mouseout: function (e) {
            wilayahLayer.resetStyle(e.target);
        },

        // Click → popup + panel detail kanan
        click: function (e) {
            showDetail(props);
            map.fitBounds(e.target.getBounds(), { padding: [50, 50] });
        }
    });
}


// ============================================================
// LOAD WILAYAH — dari API, fallback ke GeoJSON lokal
// ============================================================
async function loadWilayah() {
    try {
        // Coba fetch dari API backend (PostGIS)
        const res = await fetch(`${API_BASE}/wilayah`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        wilayahData = await res.json();
        window.wilayahData = wilayahData;
        renderWilayah(wilayahData);
        showStatus('✅ Data berhasil dimuat dari API');

    } catch (apiErr) {
        console.warn('API tidak tersedia, mencoba fallback GeoJSON lokal...', apiErr);

        try {
            // Fallback: file GeoJSON lokal
            const fallback = await fetch('data/processed/kresnomulyo_webgis.geojson');
            if (!fallback.ok) throw new Error('GeoJSON lokal tidak ditemukan');
            wilayahData = await fallback.json();
            window.wilayahData = wilayahData;
            renderWilayah(wilayahData);
            showStatus('⚠️ Data dimuat dari file lokal (backend tidak aktif)');

        } catch (localErr) {
            console.warn('GeoJSON lokal juga tidak tersedia', localErr);
            showStatus('❌ Database belum terhubung — jalankan backend Flask dulu');
            hideLoading();
        }
    }
}


// ============================================================
// RENDER WILAYAH LAYER
// ============================================================
function renderWilayah(geojson) {
    if (wilayahLayer) {
        map.removeLayer(wilayahLayer);
    }

    wilayahLayer = L.geoJSON(geojson, {
        style: styleWilayah,
        onEachFeature: onEachFeature
    }).addTo(map);

    // Fit bounds ke data
    if (wilayahLayer.getBounds().isValid()) {
        map.fitBounds(wilayahLayer.getBounds(), { padding: [30, 30] });
    }

    hideLoading();
}


// ============================================================
// LOAD POSYANDU MARKERS
// ============================================================
async function loadPosyandu() {
    try {
        const res = await fetch(`${API_BASE}/posyandu`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        posyanduLayer.clearLayers();

        data.features.forEach(f => {
            const coords = f.geometry.coordinates;
            const props = f.properties;

            const icon = L.divIcon({
                html: '<div style="background:#3498db; width:26px; height:26px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; box-shadow:0 2px 8px rgba(52,152,219,0.5); border:2px solid #fff; color:white;"><i class="ph-fill ph-map-pin"></i></div>',
                className: '',
                iconSize: [26, 26],
                iconAnchor: [13, 13]
            });

            L.marker([coords[1], coords[0]], { icon })
                .bindPopup(`<div class="popup-title">${props.nama}</div><div class="popup-row"><span class="lbl">Alamat</span><span class="val">${props.alamat}</span></div>`)
                .addTo(posyanduLayer);
        });

    } catch (err) {
        console.warn('Posyandu data tidak tersedia, menggunakan fallback lokal:', err.message);
        // Fallback inline data posyandu
        const fallbackPosyandu = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": { "type": "Point", "coordinates": [104.9050, -5.4235] },
                    "properties": { "nama": "Posyandu Kenanga", "alamat": "Sumber Sari" }
                },
                {
                    "type": "Feature",
                    "geometry": { "type": "Point", "coordinates": [104.9155, -5.4295] },
                    "properties": { "nama": "Posyandu Cempaka", "alamat": "Karang Anyar" }
                }
            ]
        };
        posyanduLayer.clearLayers();
        fallbackPosyandu.features.forEach(f => {
            const coords = f.geometry.coordinates;
            const props = f.properties;
            const icon = L.divIcon({
                html: '<div style="background:#3498db; width:26px; height:26px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; box-shadow:0 2px 8px rgba(52,152,219,0.5); border:2px solid #fff; color:white;"><i class="ph-fill ph-map-pin"></i></div>',
                className: '',
                iconSize: [26, 26],
                iconAnchor: [13, 13]
            });
            L.marker([coords[1], coords[0]], { icon })
                .bindPopup(`<div class="popup-title">${props.nama}</div><div class="popup-row"><span class="lbl">Alamat</span><span class="val">${props.alamat}</span></div>`)
                .addTo(posyanduLayer);
        });
    }
}


// ============================================================
// LOAD FASKES MARKERS
// ============================================================
async function loadFaskes() {
    try {
        const res = await fetch(`${API_BASE}/faskes`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        faskesLayer.clearLayers();

        data.features.forEach(f => {
            const coords = f.geometry.coordinates;
            const props = f.properties;

            const icon = L.divIcon({
                html: '<div style="background:#27ae60; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:15px; box-shadow:0 2px 8px rgba(39,174,96,0.5); border:2px solid #fff; color:white;"><i class="ph-fill ph-hospital"></i></div>',
                className: '',
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            });

            L.marker([coords[1], coords[0]], { icon })
                .bindPopup(`<div class="popup-title">${props.nama}</div><div class="popup-row"><span class="lbl">Jenis</span><span class="val">${props.jenis}</span></div><div class="popup-row"><span class="lbl">Alamat</span><span class="val">${props.alamat}</span></div>`)
                .addTo(faskesLayer);
        });

    } catch (err) {
        console.warn('Faskes data tidak tersedia, menggunakan fallback lokal:', err.message);
        // Fallback inline data faskes
        const fallbackFaskes = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": { "type": "Point", "coordinates": [104.9720, -5.3720] },
                    "properties": { "nama": "Puskesmas Pembantu Ambarawa", "jenis": "Puskesmas Pembantu", "alamat": "Jl. Raya Kresnomulyo" }
                },
                {
                    "type": "Feature",
                    "geometry": { "type": "Point", "coordinates": [104.91738742007512, -5.420160252847154] },
                    "properties": { "nama": "Poskesdes Kresnomulyo Barat", "jenis": "Poskesdes", "alamat": "Pekon Kresnomulyo Barat" }
                }
            ]
        };
        faskesLayer.clearLayers();
        fallbackFaskes.features.forEach(f => {
            const coords = f.geometry.coordinates;
            const props = f.properties;
            const icon = L.divIcon({
                html: '<div style="background:#27ae60; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:15px; box-shadow:0 2px 8px rgba(39,174,96,0.5); border:2px solid #fff; color:white;"><i class="ph-fill ph-hospital"></i></div>',
                className: '',
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            });
            L.marker([coords[1], coords[0]], { icon })
                .bindPopup(`<div class="popup-title">${props.nama}</div><div class="popup-row"><span class="lbl">Jenis</span><span class="val">${props.jenis}</span></div><div class="popup-row"><span class="lbl">Alamat</span><span class="val">${props.alamat}</span></div>`)
                .addTo(faskesLayer);
        });
    }
}


// ============================================================
// LOAD LAPORAN KASUS — Warning markers
// ============================================================
async function loadLaporan() {
    try {
        const res = await fetch(`${API_BASE}/laporan`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        laporanLayer.clearLayers();

        // Inject pulse animation once
        if (!document.getElementById('laporan-pulse-style')) {
            const s = document.createElement('style');
            s.id = 'laporan-pulse-style';
            s.textContent = `
                @keyframes pulse-warning {
                    0%   { box-shadow: 0 0 0 0 rgba(231,76,60,0.7); }
                    70%  { box-shadow: 0 0 0 12px rgba(231,76,60,0); }
                    100% { box-shadow: 0 0 0 0 rgba(231,76,60,0); }
                }
                .laporan-marker-wrap {
                    animation: pulse-warning 2s ease-in-out infinite;
                    border-radius: 50%;
                }
            `;
            document.head.appendChild(s);
        }

        const pending = data.features.filter(f => f.properties.status === 'pending');
        const verified = data.features.filter(f => f.properties.status === 'verified');

        // Update badge in sidebar toggle label
        const badge = document.getElementById('laporan-count-badge');
        if (badge) badge.textContent = pending.length;

        data.features.forEach(f => {
            const coords = f.geometry.coordinates;
            const props = f.properties;

            // Color by status
            const isPending = props.status === 'pending';
            const isVerified = props.status === 'verified';
            const bgColor = isPending ? '#e74c3c' : isVerified ? '#27ae60' : '#7f8c8d';
            const iconName = isPending ? 'ph-warning' : isVerified ? 'ph-check-circle' : 'ph-x-circle';

            const icon = L.divIcon({
                html: `
                    <div class="laporan-marker-wrap" style="
                        background: ${bgColor};
                        width: 36px; height: 36px;
                        border-radius: 50%;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 18px; color: white;
                        border: 3px solid white;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.35);
                        ${isPending ? 'animation: pulse-warning 2s ease-in-out infinite;' : ''}
                    ">
                        <i class="ph-fill ${iconName}"></i>
                    </div>`,
                className: '',
                iconSize: [36, 36],
                iconAnchor: [18, 18]
            });

            const dateStr = new Date(props.tanggal).toLocaleDateString('id-ID', {
                day: 'numeric', month: 'short', year: 'numeric'
            });
            const statusLabel = isPending ? '⏳ Menunggu Verifikasi' : isVerified ? '✅ Terverifikasi' : '❌ Ditolak';

            L.marker([coords[1], coords[0]], { icon })
                .bindPopup(`
                    <div style="min-width:200px; font-family:inherit;">
                        <div style="font-weight:800; font-size:13px; color:#e74c3c; margin-bottom:8px;
                            display:flex; align-items:center; gap:5px;">
                            <i class="ph-fill ph-warning-octagon"></i> Laporan Kasus
                        </div>
                        <div style="font-weight:700; font-size:12px; margin-bottom:4px;">${props.judul}</div>
                        <div style="font-size:11px; color:#666; margin-bottom:6px;">
                            👤 ${props.pelapor} &nbsp;|&nbsp; 📅 ${dateStr}
                        </div>
                        <div style="font-size:11px; background:#f8f8f8; padding:8px; border-radius:6px; margin-bottom:8px; color:#333;">
                            ${props.deskripsi}
                        </div>
                        <div style="font-size:10px; font-weight:700;">${statusLabel}</div>
                    </div>
                `, { maxWidth: 280 })
                .addTo(laporanLayer);
        });

    } catch (err) {
        console.warn('Laporan data tidak tersedia:', err.message);
    }
}


// ============================================================
// LOAD STATISTIK → Isi stat cards + list rentan
// ============================================================
async function loadStatistik() {
    try {
        const res = await fetch(`${API_BASE}/statistik`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        // Isi 4 stat card
        document.getElementById('val-balita').textContent = data.total_balita;
        document.getElementById('val-stunting').textContent = data.total_stunting;
        document.getElementById('val-persen').textContent = data.prev_total + '%';
        document.getElementById('val-wilayah').textContent = data.total_wilayah;

        // Isi list prioritas kerentanan
        const listEl = document.getElementById('list-rentan');
        if (data.top_rentan && data.top_rentan.length > 0) {
            listEl.innerHTML = data.top_rentan.map((r, i) => `
                <div class="rentan-item">
                    <div>
                        <div class="rentan-nama">${i + 1}. ${r.nama_wil}</div>
                        <div class="rentan-detail">Prevalensi: ${r.prev_stunt}%</div>
                    </div>
                    <span class="rentan-badge ${getRentanBadgeClass(r.kat_rentan)}">${r.kat_rentan}</span>
                </div>
            `).join('');
        } else {
            listEl.innerHTML = '<div class="loading-text">Tidak ada data</div>';
        }

    } catch (err) {
        console.warn('Statistik tidak tersedia:', err.message);

        // Fallback: jika ada wilayahData, hitung dari GeoJSON
        if (wilayahData && wilayahData.features) {
            computeStatsFromGeoJSON(wilayahData.features);
        }
    }
}


// ============================================================
// FALLBACK: Hitung statistik dari GeoJSON (tanpa API)
// ============================================================
function computeStatsFromGeoJSON(features) {
    const totalBalita = features.reduce((s, f) => s + (f.properties.jml_balita || 0), 0);
    const totalStunt = features.reduce((s, f) => s + (f.properties.jml_stunt || 0), 0);
    const prevTotal = totalBalita > 0 ? ((totalStunt / totalBalita) * 100).toFixed(1) : '0';

    document.getElementById('val-balita').textContent = totalBalita;
    document.getElementById('val-stunting').textContent = totalStunt;
    document.getElementById('val-persen').textContent = prevTotal + '%';
    document.getElementById('val-wilayah').textContent = features.length;

    // Hitung kerentanan & top 3
    const rentanList = features.map(f => {
        const p = f.properties;
        const prev = p.prev_stunt || 0;
        const sk = p.sk_rentan || 0;
        const kat = p.kat_rentan || 'Aman';
        return { nama_wil: p.nama_wil, prev_stunt: prev, sk_rentan: sk, kat_rentan: kat };
    }).sort((a, b) => b.sk_rentan - a.sk_rentan);

    const top3 = rentanList.slice(0, 3);
    const listEl = document.getElementById('list-rentan');
    if (top3.length > 0) {
        listEl.innerHTML = top3.map((r, i) => `
            <div class="rentan-item">
                <div>
                    <div class="rentan-nama">${i + 1}. ${r.nama_wil}</div>
                    <div class="rentan-detail">Prevalensi: ${r.prev_stunt}%</div>
                </div>
                <span class="rentan-badge ${getRentanBadgeClass(r.kat_rentan)}">${r.kat_rentan}</span>
            </div>
        `).join('');
    }
}


// ============================================================
// UI HELPERS
// ============================================================
function showStatus(msg) {
    const el = document.getElementById('status-msg');
    el.textContent = msg;
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 5000);
}

function hideLoading() {
    const el = document.getElementById('loading-overlay');
    if (el) el.style.display = 'none';
}


// ============================================================
// EVENT LISTENERS
// ============================================================
function setupEventListeners() {
    // Select indikator → update layer style
    document.getElementById('select-indikator').addEventListener('change', function () {
        currentIndikator = this.value;
        if (wilayahLayer) {
            wilayahLayer.setStyle(styleWilayah);
        }
    });

    // Toggle posyandu
    document.getElementById('toggle-posyandu').addEventListener('change', function () {
        if (this.checked) {
            map.addLayer(posyanduLayer);
        } else {
            map.removeLayer(posyanduLayer);
        }
    });

    // Toggle faskes
    document.getElementById('toggle-faskes').addEventListener('change', function () {
        if (this.checked) {
            map.addLayer(faskesLayer);
        } else {
            map.removeLayer(faskesLayer);
        }
    });

    // Toggle laporan
    const toggleLaporan = document.getElementById('toggle-laporan');
    if (toggleLaporan) {
        toggleLaporan.addEventListener('change', function () {
            if (this.checked) {
                map.addLayer(laporanLayer);
            } else {
                map.removeLayer(laporanLayer);
            }
        });
    }
}


// ============================================================
// INISIALISASI APLIKASI
// ============================================================
async function initApp() {
    // 1. Init peta
    initMap();

    // 2. Setup event listeners
    setupEventListeners();

    // 3. Load data secara paralel
    await Promise.all([
        loadWilayah(),
        loadPosyandu(),
        loadFaskes(),
        loadStatistik(),
        loadLaporan()
    ]);

    console.log('🗺 WebGIS Stunting — Aplikasi siap.');
}

// Jalankan saat DOM ready
document.addEventListener('DOMContentLoaded', initApp);
