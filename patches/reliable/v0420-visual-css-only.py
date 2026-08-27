from pathlib import Path

ROOT = Path('.')
source_path = Path('../patches/reliable/v0420-visual-refresh.py')
source = source_path.read_text(encoding='utf-8')
anchor = "css = ROOT / 'app/globals.css'"
start = source.find(anchor)
if start < 0:
    raise SystemExit('Klyvro visual refresh CSS anchor not found')

# Execute only the CSS portion of v0.4.20. Version metadata remains owned by
# the normal release chain so this visual pass cannot break the voice patches.
namespace = {'Path': Path, 'ROOT': ROOT, '__name__': '__main__'}
exec(compile(source[start:], str(source_path), 'exec'), namespace)
