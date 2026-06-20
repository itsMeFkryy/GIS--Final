"""
Regenerate all secondary pages with:
- Fixed sidebar (dynamic badges)
- Theme toggle working (Theme.init() + theme.js loaded)
- shared.js included
- Footer via shared.js
- Proper page titles
"""
import re

# Read the updated index.html to extract shell
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract HEAD section
head_match = re.search(r'(<head>.*?</head>)', html, re.DOTALL)
head = head_match.group(1)

# Extract NAVBAR
navbar_match = re.search(r'(<nav class="navbar">.*?</nav>)', html, re.DOTALL)
navbar = navbar_match.group(1)

# Extract NAV SIDEBAR (including aside open/close)
sidebar_match = re.search(r'(<aside class="nav-sidebar".*?</aside>)', html, re.DOTALL)
sidebar = sidebar_match.group(1)

# Common page shell function
def build_page(filename, title, active_href, content_html, extra_scripts='', extra_head=''):
    """Build a full HTML page with shared shell"""
    
    # Fix active state in sidebar
    page_sidebar = sidebar.replace('class="nav-item active"', 'class="nav-item"')
    # Make the correct nav item active
    if active_href:
        page_sidebar = page_sidebar.replace(
            f'class="nav-item" href="{active_href}"',
            f'class="nav-item active" href="{active_href}"'
        )
    
    # Fix page title
    page_head = head.replace(
        '<title>WebGIS Stunting — Pekon Kresnomulyo Barat</title>',
        f'<title>{title} — WebGIS Stunting</title>'
    )
    
    return f'''<!DOCTYPE html>
<html lang="id" data-theme="dark">
{page_head}
{extra_head}
<body>

{navbar}

<div class="app-wrapper" id="app-wrapper">

  {page_sidebar}

  <div class="content-area" style="overflow-y: auto; display: flex; flex-direction: column;">
    {content_html}
  </div>

</div>

<script src="js/theme.js"></script>
<script src="js/shared.js"></script>
<script>
  const NavSidebar = {{
    toggle() {{
      const wrapper = document.getElementById('app-wrapper');
      const sidebar = document.getElementById('nav-sidebar');
      const btn = document.getElementById('nav-collapse-btn');
      const isCollapsed = sidebar.classList.toggle('collapsed');
      wrapper.classList.toggle('nav-collapsed', isCollapsed);
      btn.title = isCollapsed ? 'Buka sidebar' : 'Tutup sidebar';
    }}
  }};
  Theme.init();
</script>
{extra_scripts}
</body>
</html>'''


# ============================================================
# ANALYSIS PAGE
# ============================================================
analysis_content = '''
<div style="padding: 28px; flex: 1;">
  <div style="margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px;">
    <h2 style="color: var(--text-1); font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif; margin-bottom: 4px;">Analisis Wilayah</h2>
    <p style="font-size: 13px; color: var(--text-3); margin: 0;">Analisis mendalam data stunting berdasarkan indikator wilayah. Data otomatis diambil dari backend.</p>
  </div>

  <!-- Summary Cards -->
  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 28px;" id="analysis-cards">
    <div class="analysis-card" style="background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:20px;">
      <div style="font-size:11px; color:var(--text-3); text-transform:uppercase; font-weight:700; letter-spacing:0.5px;">Total Wilayah</div>
      <div style="font-size:28px; font-weight:800; color:var(--text-1); margin-top:4px;" id="a-total-wil">—</div>
    </div>
    <div class="analysis-card" style="background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:20px;">
      <div style="font-size:11px; color:var(--text-3); text-transform:uppercase; font-weight:700; letter-spacing:0.5px;">Rata-rata Prevalensi</div>
      <div style="font-size:28px; font-weight:800; color:var(--red);" id="a-avg-prev">—</div>
    </div>
    <div class="analysis-card" style="background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:20px;">
      <div style="font-size:11px; color:var(--text-3); text-transform:uppercase; font-weight:700; letter-spacing:0.5px;">Wilayah Rentan</div>
      <div style="font-size:28px; font-weight:800; color:var(--amber);" id="a-rentan-count">—</div>
    </div>
    <div class="analysis-card" style="background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:20px;">
      <div style="font-size:11px; color:var(--text-3); text-transform:uppercase; font-weight:700; letter-spacing:0.5px;">Total Balita</div>
      <div style="font-size:28px; font-weight:800; color:var(--accent);" id="a-total-balita">—</div>
    </div>
  </div>

  <!-- Charts Row -->
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 28px;">
    <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:14px; padding:20px;">
      <div style="font-size:13px; font-weight:700; color:var(--text-1); margin-bottom:14px; display:flex; align-items:center; gap:6px;">
        <i class="ph-fill ph-chart-bar" style="color:var(--accent);"></i> Prevalensi Stunting per Wilayah
      </div>
      <canvas id="chart-prevalensi" height="220"></canvas>
    </div>
    <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:14px; padding:20px;">
      <div style="font-size:13px; font-weight:700; color:var(--text-1); margin-bottom:14px; display:flex; align-items:center; gap:6px;">
        <i class="ph-fill ph-chart-pie" style="color:var(--teal);"></i> Distribusi Kategori Kerentanan
      </div>
      <canvas id="chart-kerentanan" height="220"></canvas>
    </div>
  </div>

  <!-- Data Table -->
  <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:14px; padding:20px; overflow-x:auto;">
    <div style="font-size:13px; font-weight:700; color:var(--text-1); margin-bottom:14px; display:flex; align-items:center; gap:6px;">
      <i class="ph-fill ph-table" style="color:var(--accent);"></i> Tabel Data Wilayah
    </div>
    <table id="analysis-table" style="width:100%; border-collapse:collapse; font-size:12px;">
      <thead>
        <tr style="border-bottom:2px solid var(--border);">
          <th style="text-align:left; padding:10px 8px; color:var(--text-3); font-weight:700; font-size:10px; text-transform:uppercase;">No</th>
          <th style="text-align:left; padding:10px 8px; color:var(--text-3); font-weight:700; font-size:10px; text-transform:uppercase;">Wilayah</th>
          <th style="text-align:right; padding:10px 8px; color:var(--text-3); font-weight:700; font-size:10px; text-transform:uppercase;">Balita</th>
          <th style="text-align:right; padding:10px 8px; color:var(--text-3); font-weight:700; font-size:10px; text-transform:uppercase;">Stunting</th>
          <th style="text-align:right; padding:10px 8px; color:var(--text-3); font-weight:700; font-size:10px; text-transform:uppercase;">Prevalensi</th>
          <th style="text-align:right; padding:10px 8px; color:var(--text-3); font-weight:700; font-size:10px; text-transform:uppercase;">Air Bersih</th>
          <th style="text-align:right; padding:10px 8px; color:var(--text-3); font-weight:700; font-size:10px; text-transform:uppercase;">Sanitasi</th>
          <th style="text-align:center; padding:10px 8px; color:var(--text-3); font-weight:700; font-size:10px; text-transform:uppercase;">Kerentanan</th>
        </tr>
      </thead>
      <tbody id="analysis-tbody">
        <tr><td colspan="8" style="text-align:center; padding:30px; color:var(--text-3);">Memuat data...</td></tr>
      </tbody>
    </table>
  </div>
</div>
'''

analysis_scripts = '''
<script>
  async function loadAnalysis() {
    const apiBase = window.API_BASE_URL || 'http://localhost:5000/api';
    try {
      const res = await fetch(`${apiBase}/wilayah`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      const features = data.features || [];

      // Summary
      const totalWil = features.length;
      const totalBalita = features.reduce((s,f) => s + (f.properties.jml_balita||0), 0);
      const totalStunt = features.reduce((s,f) => s + (f.properties.jml_stunt||0), 0);
      const avgPrev = totalBalita > 0 ? ((totalStunt/totalBalita)*100).toFixed(1) : '0';
      const rentanCount = features.filter(f => ['Rentan','Sangat Rentan'].includes(f.properties.kat_rentan)).length;

      document.getElementById('a-total-wil').textContent = totalWil;
      document.getElementById('a-avg-prev').textContent = avgPrev + '%';
      document.getElementById('a-rentan-count').textContent = rentanCount;
      document.getElementById('a-total-balita').textContent = totalBalita.toLocaleString();

      // Sort by prevalensi
      const sorted = [...features].sort((a,b) => (b.properties.prev_stunt||0) - (a.properties.prev_stunt||0));

      // Table
      const tbody = document.getElementById('analysis-tbody');
      tbody.innerHTML = sorted.map((f,i) => {
        const p = f.properties;
        const badgeCls = {
          'Aman':'badge-aman','Waspada':'badge-waspada','Rentan':'badge-rentan','Sangat Rentan':'badge-sangat-rentan'
        }[p.kat_rentan] || 'badge-aman';
        return `<tr style="border-bottom:1px solid var(--border);">
          <td style="padding:10px 8px; color:var(--text-2);">${i+1}</td>
          <td style="padding:10px 8px; color:var(--text-1); font-weight:600;">${p.nama_wil}</td>
          <td style="padding:10px 8px; text-align:right; color:var(--text-2);">${p.jml_balita||0}</td>
          <td style="padding:10px 8px; text-align:right; color:var(--text-2);">${p.jml_stunt||0}</td>
          <td style="padding:10px 8px; text-align:right; font-weight:700; color:var(--red);">${(p.prev_stunt||0).toFixed(1)}%</td>
          <td style="padding:10px 8px; text-align:right; color:var(--text-2);">${(p.air_bersih||0).toFixed(1)}%</td>
          <td style="padding:10px 8px; text-align:right; color:var(--text-2);">${(p.sanitasi||0).toFixed(1)}%</td>
          <td style="padding:10px 8px; text-align:center;"><span class="kategori-badge ${badgeCls}">${p.kat_rentan||'Aman'}</span></td>
        </tr>`;
      }).join('');

      // Chart 1: Bar chart prevalensi
      const labels = sorted.map(f => f.properties.nama_wil);
      const prevData = sorted.map(f => f.properties.prev_stunt || 0);
      new Chart(document.getElementById('chart-prevalensi'), {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Prevalensi (%)',
            data: prevData,
            backgroundColor: prevData.map(v => v >= 30 ? '#bd0026' : v >= 20 ? '#fd8d3c' : v >= 10 ? '#fecc5c' : '#31a354'),
            borderRadius: 6,
            barThickness: 24
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, grid: { color: 'rgba(128,128,128,0.1)' }, ticks: { color: '#999' } },
            x: { grid: { display: false }, ticks: { color: '#999', font: { size: 10 } } }
          }
        }
      });

      // Chart 2: Doughnut kerentanan
      const katCounts = {};
      features.forEach(f => {
        const k = f.properties.kat_rentan || 'Aman';
        katCounts[k] = (katCounts[k]||0) + 1;
      });
      new Chart(document.getElementById('chart-kerentanan'), {
        type: 'doughnut',
        data: {
          labels: Object.keys(katCounts),
          datasets: [{
            data: Object.values(katCounts),
            backgroundColor: ['#31a354','#fecc5c','#fd8d3c','#bd0026'],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          cutout: '55%',
          plugins: { legend: { position: 'bottom', labels: { color: '#999', padding: 16 } } }
        }
      });

    } catch(e) {
      document.getElementById('analysis-tbody').innerHTML = '<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--red);"><i class="ph-fill ph-warning-circle"></i> Gagal memuat data. Pastikan backend berjalan.</td></tr>';
    }
  }
  document.addEventListener('DOMContentLoaded', loadAnalysis);
</script>
'''

# ============================================================
# VERIFICATION PAGE (CRUD)
# ============================================================
verif_content = '''
<div style="padding: 28px; flex: 1;">
  <div style="margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
    <div>
      <h2 style="color: var(--text-1); font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif; margin-bottom: 4px;">Verifikasi Laporan</h2>
      <p style="font-size: 13px; color: var(--text-3); margin: 0;">Tinjau, verifikasi, atau tolak laporan yang masuk dari masyarakat.</p>
    </div>
    <div style="display:flex; gap:8px;">
      <select id="filter-status" onchange="fetchLaporan()" style="padding:8px 12px; border-radius:8px; border:1px solid var(--border); background:var(--bg-card); color:var(--text-1); font-size:12px; outline:none;">
        <option value="all">Semua Status</option>
        <option value="pending">Menunggu</option>
        <option value="verified">Terverifikasi</option>
        <option value="rejected">Ditolak</option>
      </select>
      <button onclick="fetchLaporan()" style="padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-1); font-size: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">
        <i class="ph ph-arrows-clockwise"></i> Segarkan
      </button>
    </div>
  </div>

  <!-- Stats mini -->
  <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:24px;" id="verif-stats">
    <div style="background:var(--amber-soft); border:1px solid var(--amber); border-radius:10px; padding:14px 18px; display:flex; align-items:center; gap:12px;">
      <i class="ph-fill ph-clock" style="font-size:24px; color:var(--amber);"></i>
      <div><div style="font-size:10px; color:var(--amber); font-weight:700; text-transform:uppercase;">Menunggu</div><div style="font-size:22px; font-weight:800; color:var(--amber);" id="v-pending">0</div></div>
    </div>
    <div style="background:var(--green-soft); border:1px solid var(--green); border-radius:10px; padding:14px 18px; display:flex; align-items:center; gap:12px;">
      <i class="ph-fill ph-check-circle" style="font-size:24px; color:var(--green);"></i>
      <div><div style="font-size:10px; color:var(--green); font-weight:700; text-transform:uppercase;">Terverifikasi</div><div style="font-size:22px; font-weight:800; color:var(--green);" id="v-verified">0</div></div>
    </div>
    <div style="background:var(--red-soft); border:1px solid var(--red); border-radius:10px; padding:14px 18px; display:flex; align-items:center; gap:12px;">
      <i class="ph-fill ph-x-circle" style="font-size:24px; color:var(--red);"></i>
      <div><div style="font-size:10px; color:var(--red); font-weight:700; text-transform:uppercase;">Ditolak</div><div style="font-size:22px; font-weight:800; color:var(--red);" id="v-rejected">0</div></div>
    </div>
  </div>

  <div id="laporan-container" style="display: grid; gap: 14px;">
    <div style="text-align: center; padding: 40px; color: var(--text-3);">Memuat data laporan...</div>
  </div>
</div>
'''

verif_scripts = '''
<script>
  async function fetchLaporan() {
    const container = document.getElementById('laporan-container');
    const filter = document.getElementById('filter-status').value;
    container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-3);">Memuat...</div>';
    const apiBase = window.API_BASE_URL || 'http://localhost:5000/api';
    try {
      const res = await fetch(`${apiBase}/laporan`);
      const data = await res.json();
      let features = data.features || [];

      // Update stats
      const pendingC = features.filter(f=>f.properties.status==='pending').length;
      const verifiedC = features.filter(f=>f.properties.status==='verified').length;
      const rejectedC = features.filter(f=>f.properties.status==='rejected').length;
      document.getElementById('v-pending').textContent = pendingC;
      document.getElementById('v-verified').textContent = verifiedC;
      document.getElementById('v-rejected').textContent = rejectedC;

      // Filter
      if (filter !== 'all') features = features.filter(f => f.properties.status === filter);

      if (features.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-3);"><i class="ph ph-check-circle" style="font-size:32px; color:var(--green); display:block; margin-bottom:8px;"></i>Tidak ada laporan yang cocok dengan filter.</div>';
        return;
      }
      container.innerHTML = '';
      features.forEach(f => {
        const p = f.properties;
        const d = new Date(p.tanggal);
        const dStr = d.toLocaleDateString('id-ID',{day:'numeric',month:'short',year:'numeric'}) + ' ' + d.toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'});
        const statusMap = {
          pending: {label:'Menunggu Verifikasi', bg:'var(--amber-soft)', color:'var(--amber)', border:'var(--amber)', icon:'ph-clock'},
          verified: {label:'Terverifikasi', bg:'var(--green-soft)', color:'var(--green)', border:'var(--green)', icon:'ph-check-circle'},
          rejected: {label:'Ditolak', bg:'var(--red-soft)', color:'var(--red)', border:'var(--red)', icon:'ph-x-circle'}
        };
        const s = statusMap[p.status] || statusMap.pending;

        const card = document.createElement('div');
        card.style.cssText = 'background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:18px 22px; transition:all 0.2s;';
        card.onmouseenter = () => card.style.boxShadow = 'var(--shadow-md)';
        card.onmouseleave = () => card.style.boxShadow = '';

        let actionBtns = '';
        if (p.status === 'pending') {
          actionBtns = `
            <button onclick="updateStatus('${p.id}','verified')" style="padding:8px 14px; border-radius:6px; border:none; background:var(--green); color:white; font-size:11px; font-weight:700; cursor:pointer; display:inline-flex; align-items:center; gap:4px;"><i class="ph ph-check"></i> Verifikasi</button>
            <button onclick="updateStatus('${p.id}','rejected')" style="padding:8px 14px; border-radius:6px; border:1px solid var(--red); background:transparent; color:var(--red); font-size:11px; font-weight:700; cursor:pointer; display:inline-flex; align-items:center; gap:4px;"><i class="ph ph-x"></i> Tolak</button>`;
        } else {
          actionBtns = `
            <button onclick="updateStatus('${p.id}','pending')" style="padding:8px 14px; border-radius:6px; border:1px solid var(--amber); background:transparent; color:var(--amber); font-size:11px; font-weight:700; cursor:pointer; display:inline-flex; align-items:center; gap:4px;"><i class="ph ph-arrow-counter-clockwise"></i> Reset</button>`;
        }
        actionBtns += `<button onclick="deleteLaporan('${p.id}')" style="padding:8px 14px; border-radius:6px; border:1px solid var(--red); background:transparent; color:var(--red); font-size:11px; font-weight:700; cursor:pointer; display:inline-flex; align-items:center; gap:4px;"><i class="ph ph-trash"></i> Hapus</button>`;

        card.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
            <div>
              <div style="font-size:15px; font-weight:700; color:var(--text-1); margin-bottom:3px;">${p.judul}</div>
              <div style="font-size:11px; color:var(--text-3); display:flex; gap:12px; flex-wrap:wrap;">
                <span><i class="ph-fill ph-user"></i> ${p.pelapor}</span>
                <span><i class="ph-fill ph-calendar"></i> ${dStr}</span>
                <span><i class="ph-fill ph-map-pin"></i> ${Number(p.lat).toFixed(4)}, ${Number(p.lng).toFixed(4)}</span>
              </div>
            </div>
            <span style="padding:4px 12px; border-radius:20px; font-size:10px; font-weight:700; background:${s.bg}; color:${s.color}; border:1px solid ${s.border}; flex-shrink:0; display:flex; align-items:center; gap:4px;">
              <i class="ph-fill ${s.icon}"></i> ${s.label}
            </span>
          </div>
          <div style="font-size:12px; color:var(--text-2); background:var(--bg-card-2,rgba(0,0,0,0.06)); padding:10px 14px; border-radius:8px; margin-bottom:12px; border:1px dashed var(--border);">
            ${p.deskripsi}
          </div>
          <div style="display:flex; justify-content:flex-end; gap:8px;">
            ${actionBtns}
          </div>
        `;
        container.appendChild(card);
      });
    } catch(e) {
      container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--red);"><i class="ph-fill ph-warning-circle" style="font-size:32px;"></i><br>Gagal memuat data.</div>';
    }
  }

  async function updateStatus(id, status) {
    const apiBase = window.API_BASE_URL || 'http://localhost:5000/api';
    try {
      await fetch(`${apiBase}/laporan/${id}/verifikasi`, {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({status})
      });
      fetchLaporan();
    } catch { alert('Gagal mengupdate status.'); }
  }

  async function deleteLaporan(id) {
    if (!confirm('Yakin ingin menghapus laporan ini?')) return;
    const apiBase = window.API_BASE_URL || 'http://localhost:5000/api';
    try {
      await fetch(`${apiBase}/laporan/${id}`, { method: 'DELETE' });
      fetchLaporan();
    } catch { alert('Gagal menghapus.'); }
  }

  document.addEventListener('DOMContentLoaded', fetchLaporan);
</script>
'''

# ============================================================
# SIMPLE PLACEHOLDER PAGES
# ============================================================
def placeholder_content(title, icon, desc):
    return f'''
    <div style="padding: 40px; display: flex; flex-direction: column; align-items: center; justify-content: center; flex:1; color: var(--text-2); text-align: center;">
      <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 20px; padding: 40px 60px; box-shadow: var(--shadow-lg); backdrop-filter: blur(10px); max-width: 500px;">
        <i class="{icon}" style="font-size: 64px; color: var(--accent); margin-bottom: 20px;"></i>
        <h2 style="color: var(--text-1); font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif; margin-bottom: 10px;">{title}</h2>
        <p style="font-size: 14px; color: var(--text-3); line-height: 1.6;">{desc}</p>
        <a href="index.html" style="display: inline-block; margin-top: 24px; padding: 10px 24px; background: linear-gradient(135deg, var(--accent), var(--teal)); color: white; border-radius: 50px; text-decoration: none; font-weight: 700; font-size: 13px; font-family: 'Plus Jakarta Sans', sans-serif; box-shadow: 0 4px 12px rgba(37,99,235,0.3);">Kembali ke Dashboard</a>
      </div>
    </div>'''


# ============================================================
# IMPORT CSV PAGE
# ============================================================
import_content = '''
<div style="padding: 28px; flex: 1;">
  <div style="margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border);">
    <h2 style="color: var(--text-1); font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif; margin-bottom: 4px;">Import Data CSV</h2>
    <p style="font-size: 13px; color: var(--text-3); margin: 0;">Unggah data stunting baru menggunakan file CSV untuk memperbarui data pada peta.</p>
  </div>

  <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 24px; margin-bottom: 24px;">
    <div class="csv-dropzone" id="csv-dropzone" style="border: 2px dashed var(--border); border-radius: 12px; padding: 40px; text-align: center; cursor: pointer; transition: all 0.2s; margin-bottom: 20px; background: rgba(0,0,0,0.02);">
      <div class="dz-icon" style="margin-bottom: 12px;"><i class="ph ph-upload-simple" style="font-size: 48px; color: var(--accent);"></i></div>
      <p style="margin: 0; font-size: 15px; font-weight: 600; color: var(--text-1);">Drag &amp; drop file CSV di sini atau klik untuk memilih</p>
      <p style="margin: 4px 0 0 0; font-size: 12px; color: var(--text-3);">Format kolom: kode_wil · jml_balita · jml_stunt</p>
    </div>
    
    <input type="file" id="csv-file-input" accept=".csv" style="display: none;">
    
    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
      <button onclick="CSVHandler.downloadTemplate()" style="padding: 10px 20px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-1); font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: all 0.2s;">
        <i class="ph ph-download-simple"></i> Download Template CSV
      </button>
      <button onclick="CSVHandler.exportCSV()" style="padding: 10px 20px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-1); font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: all 0.2s;">
        <i class="ph ph-export"></i> Ekspor Data Saat Ini
      </button>
    </div>
    
    <div id="csv-status" class="csv-status" style="margin-top: 16px; padding: 12px; border-radius: 8px; font-size: 13px; font-weight: 500; display: none;"></div>
  </div>
</div>

<!-- ============================================================
     CSV PREVIEW MODAL
     ============================================================ -->
<div class="csv-modal-backdrop" id="csv-modal-backdrop">
  <div class="csv-modal">
    <div class="csv-modal-header">
      <div>
        <h3><i class="ph-fill ph-table"></i> Preview Import CSV</h3>
        <span>Periksa data sebelum diterapkan ke peta</span>
      </div>
      <button class="ai-close-btn" onclick="CSVHandler.closePreviewModal()">✕</button>
    </div>
    <div class="csv-modal-body">
      <div class="csv-summary">
        <div class="csv-summary-card matched">
          <div class="csv-summary-val" id="csv-count-matched">0</div>
          <div class="csv-summary-lbl"><i class="ph-fill ph-check-circle"></i> Wilayah Cocok</div>
        </div>
        <div class="csv-summary-card new-rows">
          <div class="csv-summary-val" id="csv-count-new">0</div>
          <div class="csv-summary-lbl"><i class="ph-fill ph-arrows-clockwise"></i> Diperbarui</div>
        </div>
        <div class="csv-summary-card skipped">
          <div class="csv-summary-val" id="csv-count-skip">0</div>
          <div class="csv-summary-lbl"><i class="ph-fill ph-warning"></i> Dilewati</div>
        </div>
      </div>
      <div id="csv-skip-info" style="display:none;font-size:11px;padding:7px 10px;border-radius:7px;margin-bottom:10px;font-weight:500;line-height:1.5;background:var(--amber-soft);color:var(--amber);border:1px solid var(--amber)"></div>
      <div style="overflow-x:auto">
        <table class="csv-preview-table">
          <thead>
            <tr>
              <th>Nama Wilayah</th><th>Balita</th><th>Stunting</th>
              <th>Prevalensi</th><th>Kategori</th><th>Kerentanan</th>
            </tr>
          </thead>
          <tbody id="csv-preview-tbody">
            <tr><td colspan="6" style="text-align:center;color:var(--text-4);padding:14px">Memuat preview...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="csv-modal-footer">
      <button class="csv-cancel-btn" onclick="CSVHandler.closePreviewModal()">Batal</button>
      <button class="csv-apply-btn" onclick="CSVHandler.applyImport()"><i class="ph-fill ph-check-circle"></i> Terapkan ke Peta</button>
    </div>
  </div>
</div>
'''

import_scripts = '''
<script src="js/csv-handler.js"></script>
'''


# Build pages
pages = {
    'analysis.html': {
        'title': 'Analisis Wilayah',
        'active': 'analysis.html',
        'content': analysis_content,
        'scripts': analysis_scripts
    },
    'verification.html': {
        'title': 'Verifikasi Laporan',
        'active': 'verification.html',
        'content': verif_content,
        'scripts': verif_scripts
    },
    'import.html': {
        'title': 'Import Data CSV',
        'active': 'import.html',
        'content': import_content,
        'scripts': import_scripts
    },


}

for filename, cfg in pages.items():
    html = build_page(filename, cfg['title'], cfg['active'], cfg['content'], cfg['scripts'])
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  [OK] {filename}')

print('\\nAll pages regenerated with theme, badges, footer!')
