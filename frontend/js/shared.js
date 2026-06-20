/**
 * shared.js — Shared utilities for all pages
 * - Auto-update sidebar badges (laporan count, verification pending)
 * - Inject beautiful footer
 * - Theme sync
 */

const API_BASE = window.API_BASE_URL || 'http://localhost:5000/api';

// ============================================================
// SIDEBAR BADGE AUTO-UPDATE
// ============================================================
async function updateSidebarBadges() {
    try {
        const res = await fetch(`${API_BASE}/laporan`);
        if (!res.ok) return;
        const data = await res.json();
        const features = data.features || [];
        const totalLaporan = features.length;
        const pendingCount = features.filter(f => f.properties.status === 'pending').length;

        // Update "Laporan Kasus" badge in nav sidebar
        const laporanBadge = document.getElementById('sidebar-badge-laporan');
        if (laporanBadge) {
            laporanBadge.textContent = totalLaporan;
            laporanBadge.style.display = totalLaporan > 0 ? '' : 'none';
        }

        // Update "Verifikasi Laporan" badge in nav sidebar
        const verifBadge = document.getElementById('sidebar-badge-verifikasi');
        if (verifBadge) {
            verifBadge.textContent = pendingCount;
            verifBadge.style.display = pendingCount > 0 ? '' : 'none';
        }
    } catch (e) {
        // silently fail
    }
}

// ============================================================
// FOOTER INJECTION
// ============================================================
function injectFooter() {
    // Don't inject on dashboard (has map taking full space)
    const contentArea = document.querySelector('.content-area');
    if (!contentArea) return;
    // Check if already injected
    if (document.getElementById('app-footer')) return;

    const footer = document.createElement('footer');
    footer.id = 'app-footer';
    footer.innerHTML = `
        <div class="footer-inner">
            <div class="footer-left">
                <div class="footer-brand">
                    <i class="ph-fill ph-map-trifold" style="font-size:20px; color:var(--accent);"></i>
                    <span style="font-weight:800; color:var(--text-1);">SIG Stunting</span>
                </div>
                <div class="footer-desc">Sistem Informasi Geografis Persebaran Kasus Stunting<br>Pekon Kresnomulyo Barat, Kec. Ambarawa, Kab. Pringsewu</div>
            </div>
            <div class="footer-center">
                <div class="footer-links">
                    <a href="index.html"><i class="ph ph-house"></i> Dashboard</a>
                    <a href="reports.html"><i class="ph ph-clipboard-text"></i> Laporan</a>
                    <a href="analysis.html"><i class="ph ph-chart-bar"></i> Analisis</a>
                </div>
            </div>
            <div class="footer-right">
                <div class="footer-copy">&copy; 2024 WebGIS Stunting</div>
                <div class="footer-tech">
                    <span class="footer-tech-badge"><i class="ph ph-leaf"></i> Leaflet</span>
                    <span class="footer-tech-badge"><i class="ph ph-flask"></i> Flask</span>
                    <span class="footer-tech-badge"><i class="ph ph-database"></i> PostGIS</span>
                </div>
            </div>
        </div>
    `;
    // Append after content-area's parent (app-wrapper)
    const appWrapper = document.getElementById('app-wrapper');
    if (appWrapper) {
        contentArea.appendChild(footer);
    }
}

// ============================================================
// FOOTER STYLES (inject once)
// ============================================================
function injectFooterStyles() {
    if (document.getElementById('footer-styles')) return;
    const style = document.createElement('style');
    style.id = 'footer-styles';
    style.textContent = `
        #app-footer {
            background: var(--bg-card);
            border-top: 1px solid var(--border);
            padding: 28px 32px;
            font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
            margin-top: auto;
        }
        .footer-inner {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 32px;
            max-width: 1200px;
            margin: 0 auto;
            flex-wrap: wrap;
        }
        .footer-left { flex: 1; min-width: 200px; }
        .footer-brand { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
        .footer-desc { font-size: 11px; color: var(--text-3); line-height: 1.6; }
        .footer-center { flex: 1; min-width: 200px; }
        .footer-links {
            display: flex; gap: 16px; flex-wrap: wrap;
        }
        .footer-links a {
            font-size: 12px; color: var(--text-2); text-decoration: none;
            display: flex; align-items: center; gap: 4px;
            transition: color 0.2s;
        }
        .footer-links a:hover { color: var(--accent); }
        .footer-right { text-align: right; min-width: 160px; }
        .footer-copy { font-size: 11px; color: var(--text-3); margin-bottom: 8px; }
        .footer-tech { display: flex; gap: 6px; justify-content: flex-end; flex-wrap: wrap; }
        .footer-tech-badge {
            font-size: 10px; color: var(--text-3); background: var(--bg-card-2, rgba(0,0,0,0.1));
            padding: 3px 8px; border-radius: 12px; display: inline-flex; align-items: center; gap: 3px;
            border: 1px solid var(--border);
        }
        @media (max-width: 768px) {
            .footer-inner { flex-direction: column; text-align: center; }
            .footer-right { text-align: center; }
            .footer-tech { justify-content: center; }
            .footer-links { justify-content: center; }
        }
    `;
    document.head.appendChild(style);
}

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    // Update badges immediately and every 15s
    updateSidebarBadges();
    setInterval(updateSidebarBadges, 15000);

    // Footer
    injectFooterStyles();
    // Only inject footer on non-dashboard pages
    const isIndex = window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/');
    if (!isIndex) {
        injectFooter();
    }
});
