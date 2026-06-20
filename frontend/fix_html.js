const fs = require('fs');
let html = fs.readFileSync('index.html', 'utf-8');

if (!html.includes('@phosphor-icons/web')) {
  html = html.replace('</head>', '  <!-- Phosphor Icons -->\n  <script src="https://unpkg.com/@phosphor-icons/web"></script>\n</head>');
}

const replacements = {
  '<span class="brand-icon">🗺️</span>': '<i class="ph-fill ph-map-trifold brand-icon" style="font-size: 28px; color: var(--accent);"></i>',
  '📄 Export PDF': '<i class="ph ph-file-pdf"></i> Export PDF',
  '📊 Export CSV': '<i class="ph ph-file-csv"></i> Export CSV',
  '<span>🌙</span>': '<i class="ph-fill ph-moon"></i>',
  '<span class="nav-icon">🏠</span>': '<i class="ph ph-house nav-icon"></i>',
  '<span class="nav-icon">📊</span>': '<i class="ph ph-chart-bar nav-icon"></i>',
  '<span class="nav-icon">🏥</span>': '<i class="ph ph-hospital nav-icon"></i>',
  '<span class="nav-icon">📋</span>': '<i class="ph ph-clipboard-text nav-icon"></i>',
  '<span class="nav-icon">✅</span>': '<i class="ph ph-check-circle nav-icon"></i>',
  '<span class="nav-icon">📈</span>': '<i class="ph ph-trend-up nav-icon"></i>',
  '<span class="nav-icon">📂</span>': '<i class="ph ph-folder-open nav-icon"></i>',
  '<span class="nav-icon">⚙️</span>': '<i class="ph ph-gear nav-icon"></i>',
  '<span class="nav-icon">❓</span>': '<i class="ph ph-question nav-icon"></i>',
  '<span class="nav-icon">🚪</span>': '<i class="ph ph-sign-out nav-icon"></i>',
  '<span class="icon">📊</span> Ringkasan Data': '<i class="ph-fill ph-chart-pie-slice icon"></i> Ringkasan Data',
  '<span class="icon">🎯</span> Indikator Peta': '<i class="ph-fill ph-target icon"></i> Indikator Peta',
  '<span class="icon">📍</span> Layer Titik': '<i class="ph-fill ph-map-pin icon"></i> Layer Titik',
  '<span class="toggle-label">📍 Posyandu</span>': '<span class="toggle-label"><i class="ph-fill ph-map-pin" style="color:#3498db; margin-right:4px; font-size: 14px;"></i> Posyandu</span>',
  '<span class="toggle-label">🏥 Fasilitas Kesehatan</span>': '<span class="toggle-label"><i class="ph-fill ph-hospital" style="color:#27ae60; margin-right:4px; font-size: 14px;"></i> Fasilitas Kesehatan</span>',
  '<span class="icon">⚠️</span> Prioritas Kerentanan': '<i class="ph-fill ph-warning-circle icon"></i> Prioritas Kerentanan',
  '<span class="icon">🎨</span> Legenda Stunting': '<i class="ph-fill ph-palette icon"></i> Legenda Stunting',
  '<span class="icon">📁</span> Import Data': '<i class="ph-fill ph-folder-open icon"></i> Import Data',
  '<div class="dz-icon">📂</div>': '<div class="dz-icon"><i class="ph ph-upload-simple" style="font-size: 32px; color: var(--accent);"></i></div>',
  '⬆️ Import CSV Baru': '<i class="ph ph-upload"></i> Import CSV Baru',
  '📋 Download Template': '<i class="ph ph-download-simple"></i> Download Template',
  '✨ Tanya AI': '<i class="ph-fill ph-sparkle"></i> Tanya AI',
  '<span class="icon">📋</span> Detail Wilayah': '<i class="ph-fill ph-info icon"></i> Detail Wilayah',
  '<div class="icon-big">🗺️</div>': '<div class="icon-big"><i class="ph-fill ph-map-trifold"></i></div>',
  '<div class="ai-panel-icon">✨</div>': '<div class="ai-panel-icon"><i class="ph-fill ph-sparkle"></i></div>',
  '🗑': '<i class="ph ph-trash"></i>',
  '<div class="ai-welcome-icon">✨</div>': '<div class="ai-welcome-icon"><i class="ph-fill ph-sparkle"></i></div>',
  '💡 Pertanyaan cepat': '<i class="ph-fill ph-lightbulb"></i> Pertanyaan cepat',
  '🎯 Wilayah paling berisiko': '<i class="ph ph-target"></i> Wilayah paling berisiko',
  '💊 Rekomendasi intervensi': '<i class="ph ph-pill"></i> Rekomendasi intervensi',
  '🔍 Faktor risiko utama': '<i class="ph ph-magnifying-glass"></i> Faktor risiko utama',
  '📋 Ringkasan eksekutif': '<i class="ph ph-clipboard-text"></i> Ringkasan eksekutif',
  '🧮 Hitung target': '<i class="ph ph-calculator"></i> Hitung target',
  '<h3>📊 Preview Import CSV</h3>': '<h3><i class="ph-fill ph-table"></i> Preview Import CSV</h3>',
  '✅ Wilayah Cocok': '<i class="ph-fill ph-check-circle"></i> Wilayah Cocok',
  '🔄 Diperbarui': '<i class="ph-fill ph-arrows-clockwise"></i> Diperbarui',
  '⚠️ Dilewati': '<i class="ph-fill ph-warning"></i> Dilewati',
  '✅ Terapkan ke Peta': '<i class="ph-fill ph-check-circle"></i> Terapkan ke Peta',
};

for (const [key, value] of Object.entries(replacements)) {
  html = html.split(key).join(value);
}

html = html.replace('data-theme="light"', 'data-theme="dark"');

fs.writeFileSync('index.html', html);
console.log('HTML updated successfully');
