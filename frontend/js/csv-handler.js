/**
 * csv-handler.js — CSV Import/Export untuk WebGIS Stunting
 *
 * Import CSV: Update atribut wilayah di peta berdasarkan kode/nama wilayah
 * Export CSV: Download data saat ini sebagai CSV
 * Template:   Download template CSV dengan kolom yang benar
 *
 * Dependencies: window.wilayahData, renderWilayah(), computeStatsFromGeoJSON()
 */

const CSVHandler = (() => {

    // Kolom yang wajib ada di CSV import (minimal)
    const REQUIRED_COLS = ['jml_balita', 'jml_stunt'];

    // Kolom yang bisa diimport (opsional)
    const OPTIONAL_COLS = [
        'kat_ekon', 'air_bersih', 'sanitasi', 'jamban',
        'bansos', 'jml_posyan', 'tahun', 'sumber'
    ];

    // Semua kolom yang diexport
    const EXPORT_COLS = [
        'kode_wil', 'nama_wil', 'jenis_wil',
        'jml_balita', 'jml_stunt', 'prev_stunt', 'kat_stunt',
        'kat_ekon', 'air_bersih', 'sanitasi', 'jamban',
        'bansos', 'jml_posyan', 'sk_rentan', 'kat_rentan',
        'tahun', 'sumber'
    ];

    // State preview modal
    let parsedPreviewData = null;

    // ============================================================
    // HELPER: Hitung prev & kerentanan (sama dgn logic app.py)
    // ============================================================
    function hitungPrev(jmlStunt, jmlBalita) {
        if (!jmlBalita || jmlBalita === 0) return 0;
        return parseFloat(((jmlStunt / jmlBalita) * 100).toFixed(2));
    }

    function klasifikasiStunting(prev) {
        if (prev < 10)  return 'Rendah';
        if (prev < 20)  return 'Sedang';
        if (prev < 30)  return 'Tinggi';
        return 'Sangat Tinggi';
    }

    function hitungSkRentan(prevStunt, bansos, jmlBalita, sanitasi) {
        if (!jmlBalita || jmlBalita === 0) return 0;
        const sk = (prevStunt / 100) * 0.4
                 + (bansos / jmlBalita) * 0.3
                 + ((100 - sanitasi) / 100) * 0.3;
        return parseFloat(sk.toFixed(4));
    }

    function klasifikasiRentan(sk) {
        if (sk < 0.2)  return 'Aman';
        if (sk < 0.35) return 'Waspada';
        if (sk < 0.5)  return 'Rentan';
        return 'Sangat Rentan';
    }

    // ============================================================
    // PARSE CSV — return array of objects
    // ============================================================
    function parseCSV(text) {
        const lines = text.trim().split(/\r?\n/);
        if (lines.length < 2) throw new Error('CSV harus memiliki header dan minimal 1 baris data.');

        // Detect separator (comma or semicolon)
        const sep = lines[0].includes(';') ? ';' : ',';
        const headers = lines[0].split(sep).map(h => h.trim().toLowerCase().replace(/['"]/g, ''));

        const rows = [];
        for (let i = 1; i < lines.length; i++) {
            if (!lines[i].trim()) continue;
            const vals = lines[i].split(sep).map(v => v.trim().replace(/^["']|["']$/g, ''));
            const row = {};
            headers.forEach((h, idx) => { row[h] = vals[idx] || ''; });
            rows.push(row);
        }

        return { headers, rows };
    }

    // ============================================================
    // VALIDATE HEADERS
    // ============================================================
    function validateHeaders(headers) {
        const errors = [];

        // Harus ada identifier wilayah
        const hasIdentifier = headers.includes('kode_wil') || headers.includes('nama_wil');
        if (!hasIdentifier) {
            errors.push('Kolom "kode_wil" atau "nama_wil" wajib ada untuk mencocokkan wilayah.');
        }

        // Harus ada data stunting
        REQUIRED_COLS.forEach(col => {
            if (!headers.includes(col)) {
                errors.push(`Kolom wajib tidak ditemukan: "${col}"`);
            }
        });

        return errors;
    }

    // ============================================================
    // MATCH & MERGE — cocokkan CSV row dengan GeoJSON feature
    // ============================================================
    function matchAndMerge(rows, features) {
        const results = {
            matched: [],
            skipped: [],
        };

        rows.forEach(row => {
            const rowKode = (row['kode_wil'] || '').trim().toLowerCase();
            const rowNama = (row['nama_wil'] || '').trim().toLowerCase();

            // Cari feature yang cocok
            const feature = features.find(f => {
                const p = f.properties;
                const fKode = (p.kode_wil || '').trim().toLowerCase();
                const fNama = (p.nama_wil || '').trim().toLowerCase();
                return (rowKode && fKode === rowKode) || (rowNama && fNama === rowNama);
            });

            if (!feature) {
                results.skipped.push({ row, reason: `Wilayah "${row['nama_wil'] || row['kode_wil']}" tidak ditemukan di peta.` });
                return;
            }

            const p = feature.properties;

            // Ambil nilai baru dari CSV, gunakan nilai lama sebagai fallback
            const jmlBalita = parseInt(row['jml_balita']) || p.jml_balita || 0;
            const jmlStunt  = parseInt(row['jml_stunt'])  || p.jml_stunt  || 0;
            const bansos    = parseInt(row['bansos'])     ?? p.bansos    ?? 0;
            const sanitasi  = parseFloat(row['sanitasi']) || p.sanitasi  || 0;

            // Hitung ulang nilai derivatif
            const prevStunt  = hitungPrev(jmlStunt, jmlBalita);
            const katStunt   = klasifikasiStunting(prevStunt);
            const skRentan   = hitungSkRentan(prevStunt, bansos, jmlBalita, sanitasi);
            const katRentan  = klasifikasiRentan(skRentan);

            // Buat versi updated properties
            const updatedProps = {
                ...p,
                jml_balita: jmlBalita,
                jml_stunt:  jmlStunt,
                prev_stunt: prevStunt,
                kat_stunt:  katStunt,
                sk_rentan:  skRentan,
                kat_rentan: katRentan,
            };

            // Update kolom opsional jika ada di CSV
            OPTIONAL_COLS.forEach(col => {
                if (row[col] !== undefined && row[col] !== '') {
                    const num = parseFloat(row[col]);
                    updatedProps[col] = isNaN(num) ? row[col] : num;
                }
            });

            results.matched.push({
                nama: p.nama_wil,
                kode: p.kode_wil,
                oldProps: { ...p },
                newProps: updatedProps,
                feature,
            });
        });

        return results;
    }

    // ============================================================
    // TRIGGER FILE PICKER
    // ============================================================
    function triggerImport() {
        document.getElementById('csv-file-input').click();
    }

    // ============================================================
    // HANDLE FILE — parse → preview modal
    // ============================================================
    function handleFile(file) {
        if (!file) return;
        if (!file.name.endsWith('.csv')) {
            showStatus('error', '❌ File harus berformat .csv');
            return;
        }

        showStatus('info', '⏳ Memproses file CSV...');

        const reader = new FileReader();
        reader.onload = e => {
            try {
                const { headers, rows } = parseCSV(e.target.result);

                // Validasi header
                const errors = validateHeaders(headers);
                if (errors.length > 0) {
                    showStatus('error', '❌ ' + errors.join(' | '));
                    return;
                }

                // Cek wilayahData tersedia
                if (!window.wilayahData || !window.wilayahData.features) {
                    showStatus('error', '❌ Data peta belum dimuat. Tunggu peta selesai loading.');
                    return;
                }

                // Match CSV ke features
                const mergeResult = matchAndMerge(rows, window.wilayahData.features);
                parsedPreviewData = mergeResult;

                showStatus('info', `✅ File diproses: ${mergeResult.matched.length} cocok, ${mergeResult.skipped.length} dilewati`);
                openPreviewModal(mergeResult);

            } catch (err) {
                showStatus('error', `❌ Error: ${err.message}`);
            }
        };
        reader.readAsText(file, 'UTF-8');
    }

    // ============================================================
    // APPLY IMPORT — update wilayahData & re-render peta
    // ============================================================
    function applyImport() {
        if (!parsedPreviewData || !parsedPreviewData.matched.length) {
            closePreviewModal();
            return;
        }

        showStatus('info', '⏳ Menyimpan data ke server...');

        // Format data untuk dikirim ke backend
        const payload = parsedPreviewData.matched.map(item => {
            const np = item.newProps;
            return {
                kode_wil: item.kode,
                nama_wil: item.nama,
                jml_balita: np.jml_balita,
                jml_stunt: np.jml_stunt,
                air_bersih: np.air_bersih,
                sanitasi: np.sanitasi,
                jamban: np.jamban,
                bansos: np.bansos,
                jml_posyan: np.jml_posyan,
                tahun: np.tahun,
                sumber: np.sumber
            };
        });

        const apiBase = window.API_BASE_URL || 'http://localhost:5000/api';

        fetch(`${apiBase}/wilayah/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(res => {
            if (!res.ok) throw new Error('Respon server tidak sukses');
            return res.json();
        })
        .then(resData => {
            // Update properties di wilayahData (in-place)
            parsedPreviewData.matched.forEach(item => {
                item.feature.properties = item.newProps;
            });

            // Re-render peta dengan data baru
            if (typeof renderWilayah === 'function') {
                renderWilayah(window.wilayahData);
            }

            // Update stat cards
            if (typeof computeStatsFromGeoJSON === 'function') {
                computeStatsFromGeoJSON(window.wilayahData.features);
            }

            const n = parsedPreviewData.matched.length;
            showStatus('success', `✅ ${n} wilayah berhasil diperbarui di database!`);
            parsedPreviewData = null;
            closePreviewModal();

            // Reset file input supaya bisa upload file yang sama lagi
            const fileInput = document.getElementById('csv-file-input');
            if (fileInput) fileInput.value = '';
        })
        .catch(err => {
            console.error(err);
            showStatus('error', `❌ Gagal menyimpan ke server: ${err.message}`);
        });
    }

    // ============================================================
    // EXPORT CSV — download data saat ini
    // ============================================================
    function exportCSV() {
        if (!window.wilayahData || !window.wilayahData.features) {
            showStatus('error', '❌ Tidak ada data untuk diekspor.');
            return;
        }

        const features = window.wilayahData.features;
        const lines = [EXPORT_COLS.join(',')];

        features.forEach(f => {
            const p = f.properties;
            const row = EXPORT_COLS.map(col => {
                const val = p[col] !== undefined ? p[col] : '';
                // Escape koma dalam string
                return String(val).includes(',') ? `"${val}"` : val;
            });
            lines.push(row.join(','));
        });

        const csvContent = lines.join('\n');
        downloadFile(csvContent, 'data_stunting_kresnomulyo.csv', 'text/csv;charset=utf-8;');
        showStatus('success', `✅ ${features.length} wilayah berhasil diekspor.`);
    }

    // ============================================================
    // DOWNLOAD TEMPLATE CSV
    // ============================================================
    function downloadTemplate() {
        const templateCols = ['kode_wil', 'nama_wil', 'jml_balita', 'jml_stunt',
                              'kat_ekon', 'air_bersih', 'sanitasi', 'jamban',
                              'bansos', 'jml_posyan', 'tahun', 'sumber'];

        const exampleRow = ['KRN-001', 'Contoh Dusun 1', '50', '8',
                            'Menengah', '75.5', '68.0', '70.0',
                            '5', '2', '2024', 'Puskesmas Ambarawa'];

        const note = ['# PETUNJUK:', '# Kolom wajib: kode_wil (atau nama_wil), jml_balita, jml_stunt',
                      '# Kolom opsional: kat_ekon, air_bersih, sanitasi, jamban, bansos, jml_posyan, tahun, sumber',
                      '# prev_stunt, kat_stunt, sk_rentan, kat_rentan dihitung otomatis',
                      '# Hapus baris yang diawali # sebelum import', ''].join('\n');

        const csvContent = note + templateCols.join(',') + '\n' + exampleRow.join(',');
        downloadFile(csvContent, 'template_stunting.csv', 'text/csv;charset=utf-8;');
        showStatus('success', '✅ Template CSV berhasil diunduh.');
    }

    // ============================================================
    // PREVIEW MODAL
    // ============================================================
    function openPreviewModal(mergeResult) {
        const modal = document.getElementById('csv-modal-backdrop');
        const matched = mergeResult.matched;
        const skipped = mergeResult.skipped;

        // Summary cards
        document.getElementById('csv-count-matched').textContent = matched.length;
        document.getElementById('csv-count-new').textContent = 0; // import update-only
        document.getElementById('csv-count-skip').textContent  = skipped.length;

        // Build preview table (max 8 rows untuk ringkas)
        const tbody = document.getElementById('csv-preview-tbody');
        const previewRows = matched.slice(0, 8);
        tbody.innerHTML = previewRows.map(item => {
            const np = item.newProps;
            const op = item.oldProps;
            const changed = op.prev_stunt !== np.prev_stunt;
            return `
                <tr class="${changed ? 'row-ok' : ''}">
                    <td><strong>${item.nama}</strong></td>
                    <td>${np.jml_balita}</td>
                    <td>${np.jml_stunt}</td>
                    <td style="color:${np.prev_stunt > 20 ? '#EF5350' : '#2DC87E'}">${np.prev_stunt}%</td>
                    <td>${np.kat_stunt}</td>
                    <td>${np.kat_rentan}</td>
                </tr>
            `;
        }).join('');

        if (matched.length > 8) {
            tbody.innerHTML += `<tr><td colspan="6" style="text-align:center;color:#94A3B8;font-size:10px;padding:8px">... dan ${matched.length - 8} wilayah lainnya</td></tr>`;
        }

        // Skipped rows info
        const skipInfo = document.getElementById('csv-skip-info');
        if (skipped.length > 0) {
            skipInfo.style.display = 'block';
            skipInfo.innerHTML = `⚠️ Dilewati (${skipped.length}): ${skipped.map(s => s.row['nama_wil'] || s.row['kode_wil'] || '?').join(', ')}`;
        } else {
            skipInfo.style.display = 'none';
        }

        modal.classList.add('open');
    }

    function closePreviewModal() {
        document.getElementById('csv-modal-backdrop').classList.remove('open');
    }

    // ============================================================
    // UI HELPERS
    // ============================================================
    function showStatus(type, msg) {
        const el = document.getElementById('csv-status');
        if (!el) return;
        el.className = `csv-status show ${type}`;
        el.textContent = msg;
        if (type === 'success') {
            setTimeout(() => el.classList.remove('show'), 5000);
        }
    }

    function downloadFile(content, filename, mimeType) {
        const blob = new Blob(['\ufeff' + content], { type: mimeType }); // BOM for Excel
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // ============================================================
    // DRAG-DROP ZONE
    // ============================================================
    function setupDragDrop() {
        const dropzone = document.getElementById('csv-dropzone');
        if (!dropzone) return;

        dropzone.addEventListener('dragover', e => {
            e.preventDefault();
            dropzone.classList.add('dragging');
        });
        dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragging'));
        dropzone.addEventListener('drop', e => {
            e.preventDefault();
            dropzone.classList.remove('dragging');
            const file = e.dataTransfer.files[0];
            if (file) handleFile(file);
        });
        dropzone.addEventListener('click', () => triggerImport());
    }

    // ============================================================
    // INIT
    // ============================================================
    function init() {
        // File input change
        const fileInput = document.getElementById('csv-file-input');
        if (fileInput) {
            fileInput.addEventListener('change', e => {
                handleFile(e.target.files[0]);
            });
        }
        setupDragDrop();

        // Fetch wilayahData if not present (e.g. standalone import page)
        if (!window.wilayahData) {
            const apiBase = window.API_BASE_URL || 'http://localhost:5000/api';
            fetch(`${apiBase}/wilayah`)
                .then(res => res.json())
                .then(data => {
                    window.wilayahData = data;
                })
                .catch(err => {
                    console.error('Gagal mengambil data wilayah dari backend:', err);
                });
        }
    }

    // Public API
    return {
        init,
        triggerImport,
        exportCSV,
        downloadTemplate,
        applyImport,
        closePreviewModal,
    };
})();

document.addEventListener('DOMContentLoaded', () => CSVHandler.init());
