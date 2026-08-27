from pathlib import Path
import re

ROOT = Path('.')
source_path = Path('../patches/reliable/v0421-hires-mentions.py')
source = source_path.read_text(encoding='utf-8')
anchor = '# ---------------------------------------------------------------------------\n# Screen sharing:'
start = source.find(anchor)
if start < 0:
    raise SystemExit('Klyvro hi-res/mentions feature anchor not found')

# Run only the feature body here. Release metadata remains owned by the normal
# v0.4.18 -> v0.4.19 chain, so the existing validation and later voice
# navigation patch remain deterministic.
namespace = {'Path': Path, 're': re, 'ROOT': ROOT, '__name__': '__main__'}
exec(compile(source[start:], str(source_path), 'exec'), namespace)
