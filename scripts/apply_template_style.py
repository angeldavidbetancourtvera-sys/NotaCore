from pathlib import Path
import re

root = Path('templates')
files = sorted(root.rglob('*.html'))
for path in files:
    if path.name == '_base.html':
        continue
    text = path.read_text(encoding='utf-8')

    if '{% extends' in text or 'bg-[radial-gradient' in text:
        continue

    if '<link rel="stylesheet" href="https://unpkg.com/tailwindcss@2.2.19/dist/tailwind.min.css"' not in text:
        text = text.replace('</head>', '    <link rel="stylesheet" href="https://unpkg.com/tailwindcss@2.2.19/dist/tailwind.min.css" />\n    <style>\n        body { font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }\n        form p { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 1rem; color: #cbd5e1; }\n        form label { font-size: 0.875rem; font-weight: 600; color: #e2e8f0; }\n        form input, form select, form textarea { width: 100%; border: 1px solid #334155; border-radius: 0.85rem; background: #020617; color: #f8fafc; padding: 0.7rem 0.9rem; outline: none; box-sizing: border-box; }\n        form input:focus, form select:focus, form textarea:focus { border-color: #22d3ee; box-shadow: 0 0 0 2px rgba(34,211,238,0.2); }\n        form button, form input[type="submit"], form input[type="button"] { border-radius: 9999px; background: linear-gradient(135deg, #06b6d4, #2563eb); color: white; padding: 0.7rem 1rem; font-weight: 600; cursor: pointer; border: none; }\n        table { width: 100%; border-collapse: collapse; overflow: hidden; border-radius: 1rem; }\n        table th, table td { border: 1px solid #334155; padding: 0.75rem 0.9rem; text-align: left; }\n        table thead { background: rgba(2, 6, 23, 0.9); color: #e2e8f0; }\n        table tbody tr:nth-child(even) { background: rgba(15, 23, 42, 0.7); }\n        a { color: inherit; text-decoration: none; }\n        .btn-secondary { display: inline-flex; align-items: center; justify-content: center; padding: 0.6rem 1rem; border-radius: 9999px; border: 1px solid #334155; background: rgba(15, 23, 42, 0.7); color: #e2e8f0; }\n    </style>\n</head>', 1)

    if '<body' in text and 'min-h-screen bg-slate-950 text-slate-100' not in text:
        text = text.replace('<body>', '<body class="min-h-screen bg-slate-950 text-slate-100">', 1)

    if '<body' in text and 'bg-[radial-gradient' not in text and 'class="min-h-screen bg-slate-950 text-slate-100">' in text:
        text = text.replace('<body class="min-h-screen bg-slate-950 text-slate-100">', '<body class="min-h-screen bg-slate-950 text-slate-100">\n    <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(37,99,235,0.35),_transparent_35%),linear-gradient(135deg,_#020617_0%,_#111827_45%,_#0f172a_100%)]">\n        <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">\n            <div class="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl shadow-slate-950/40 backdrop-blur">', 1)
        text = text.replace('</body>', '            </div>\n        </div>\n    </div>\n</body>', 1)

    path.write_text(text, encoding='utf-8')

print('Styled templates:', len(files))
