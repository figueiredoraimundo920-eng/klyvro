from pathlib import Path
import re

ROOT = Path('.')
source_path = Path('../patches/reliable/v0421-features-safe.py')
source = source_path.read_text(encoding='utf-8')

# Feature-only runner: keeps the established v0.4.18 -> v0.4.19 release chain
# intact while applying hi-res P2P screen sharing and chat mentions.
namespace = {'Path': Path, 're': re, 'ROOT': ROOT, '__name__': '__main__'}
exec(compile(source, str(source_path), 'exec'), namespace)
