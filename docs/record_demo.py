"""Record actual CLI output as asciicast plus a rendered GIF (not a desktop capture)."""
import json
from pathlib import Path
import subprocess
import sys
import time
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
font = ImageFont.truetype('DejaVuSansMono.ttf', 15)
lines = ['Invoice-to-Excel Automation | terminal recording', 'All invoices are synthetic', '']
frames, events = [], []
start = time.monotonic()
commands = [
    [sys.executable, '-m', 'invoice_automation', '--input', 'samples/invoices', '--output', 'samples/output'],
    [sys.executable, '-m', 'pytest', '-q', '--color=no'],
]
for args in commands:
    display = 'python ' + ' '.join(args[1:])
    chunks = ['$ ' + display + '\n']
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    chunks.extend((result.stdout + result.stderr).splitlines(keepends=True))
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    for chunk in chunks:
        events.append([round(time.monotonic() - start, 4), 'o', chunk.replace('\n', '\r\n')])
        lines.extend(chunk.rstrip().splitlines())
        canvas = Image.new('RGB', (1150, 680), '#101827')
        draw = ImageDraw.Draw(canvas)
        for i, line in enumerate(lines[-29:]):
            draw.text((24, 20 + i * 22), line, font=font, fill='#79e6b0' if line.startswith('$') else '#e4e9f0')
        frames.append(canvas)
(ROOT / 'docs/demo.cast').write_text(json.dumps({'version': 2, 'width': 120, 'height': 30, 'timestamp': int(time.time()), 'env': {'TERM': 'xterm-256color'}}) + '\n' + '\n'.join(json.dumps(e) for e in events) + '\n')
frames[0].save(ROOT / 'docs/demo.gif', save_all=True, append_images=frames[1:], duration=[800] * (len(frames) - 1) + [4000], loop=0)
print('Recorded docs/demo.cast and docs/demo.gif from successful commands')
