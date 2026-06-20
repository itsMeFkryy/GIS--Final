const fs = require('fs');
let css = fs.readFileSync('css/style.css', 'utf-8');

const newDarkTheme = `[data-theme="dark"] {
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
}`;

css = css.replace(/\[data-theme="dark"\]\s*\{[\s\S]*?\}/, newDarkTheme);

css = css.replace('.navbar {', '.navbar {\n  backdrop-filter: blur(12px);');
css = css.replace('.nav-sidebar {', '.nav-sidebar {\n  backdrop-filter: blur(12px);');
css = css.replace('.sidebar {', '.sidebar {\n  backdrop-filter: blur(12px);');
css = css.replace('.info-panel {', '.info-panel {\n  backdrop-filter: blur(12px);');
css = css.replace('.stat-card {', '.stat-card {\n  backdrop-filter: blur(8px);');

fs.writeFileSync('css/style.css', css);
console.log('CSS updated successfully');
