import os
import re

# Update HTML
html_path = 'index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

if '@phosphor-icons/web' not in html:
    html = html.replace('</head>', '  <!-- Phosphor Icons -->\n  <script src="https://unpkg.com/@phosphor-icons/web"></script>\n</head>')

replacements = {
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
}

for k, v in replacements.items():
    html = html.replace(k, v)

html = html.replace('data-theme="light"', 'data-theme="dark"')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print('HTML updated.')

# Update CSS
css_path = 'css/style.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

new_dark_theme = """[data-theme="dark"] {
  --bg-body:      #060B14;
  --bg-nav:       rgba(10, 18, 32, 0.85);
  --bg-sidebar:   rgba(10, 18, 32, 0.65);
  --bg-panel:     rgba(10, 18, 32, 0.65);
  --bg-card:      rgba(20, 30, 51, 0.65);
  --bg-card-2:    rgba(30, 41, 59, 0.65);
  --bg-hover:     rgba(59, 130, 246, 0.15);
  --bg-active:    rgba(59, 130, 246, 0.25);
  --bg-input:     rgba(10, 18, 32, 0.8);
  --bg-overlay:   rgba(6, 11, 20, 0.88);

  --text-1:       #F8FAFC;
  --text-2:       #E2E8F0;
  --text-3:       #94A3B8;
  --text-4:       #475569;

  --border:       rgba(59, 130, 246, 0.25);
  --border-focus: rgba(59, 130, 246, 0.6);

  --accent:       #3B82F6;
  --accent-soft:  rgba(59, 130, 246, 0.2);
  --accent-mid:   #2563EB;

  --green:        #10B981;
  --green-soft:   rgba(16, 185, 129, 0.2);
  --red:          #EF4444;
  --red-soft:     rgba(239, 68, 68, 0.2);
  --amber:        #F59E0B;
  --amber-soft:   rgba(245, 158, 11, 0.2);
  --teal:         #06B6D4;
  --teal-soft:    rgba(6, 182, 212, 0.2);
  --peach:        #F97316;
  --peach-soft:   rgba(249, 115, 22, 0.2);

  --shadow-xs:    0 1px 2px rgba(0,0,0,0.5);
  --shadow-sm:    0 1px 8px rgba(0,0,0,0.6);
  --shadow-md:    0 4px 18px rgba(0,0,0,0.6);
  --shadow-lg:    0 8px 36px rgba(0,0,0,0.8);
  --shadow-fab:   0 4px 22px rgba(59,130,246,0.5);
}"""

css = re.sub(r'\[data-theme="dark"\]\s*\{[\s\S]*?\}', new_dark_theme, css)

css = css.replace('.navbar {', '.navbar {\n  backdrop-filter: blur(12px);')
css = css.replace('.nav-sidebar {', '.nav-sidebar {\n  backdrop-filter: blur(12px);')
css = css.replace('.sidebar {', '.sidebar {\n  backdrop-filter: blur(12px);')
css = css.replace('.info-panel {', '.info-panel {\n  backdrop-filter: blur(12px);')
css = css.replace('.stat-card {', '.stat-card {\n  backdrop-filter: blur(8px);')

with open(css_path, 'w', encoding='utf-8') as f:
    f.write(css)
print('CSS updated.')
