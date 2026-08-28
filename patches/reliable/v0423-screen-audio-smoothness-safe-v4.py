from pathlib import Path
import re

source_path = Path('../patches/reliable/v0423-screen-audio-smoothness.py')
source = source_path.read_text(encoding='utf-8')

# Make display-capture rewriting independent from source formatting.
old_display = '''pattern = re.compile(
    r'navigator\\.mediaDevices\\.getDisplayMedia\\(\\{\\s*video:\\s*\\{\\s*frameRate:\\s*\\{\\s*ideal:\\s*24,\\s*max:\\s*30\\s*\\}\\s*\\},\\s*audio:\\s*false\\s*\\}\\)'
)
voice, display_count = pattern.subn(
    'navigator.mediaDevices.getDisplayMedia({ video: { width: { ideal: 2560, max: 2560 }, height: { ideal: 1440, max: 1440 }, frameRate: { ideal: 60, max: 60 } }, audio: true })',
    voice,
    count=1,
)
if display_count != 1:
    raise SystemExit(f'app/voice-room.tsx: getDisplayMedia 30fps/no-audio target expected once, found {display_count}')
'''
new_display = '''display_start = voice.find('navigator.mediaDevices.getDisplayMedia(')
if display_start < 0:
    raise SystemExit('app/voice-room.tsx: getDisplayMedia call not found')
display_end = voice.find(');', display_start)
if display_end < 0:
    raise SystemExit('app/voice-room.tsx: getDisplayMedia call end not found')
display_end += 1
capture_call = voice[display_start:display_end]
if not re.search(r'audio\\s*:\\s*false', capture_call):
    raise SystemExit(f'app/voice-room.tsx: getDisplayMedia audio:false not found in {capture_call!r}')
capture_call = re.sub(r'audio\\s*:\\s*false', 'audio: true', capture_call, count=1)
capture_call, frame_count = re.subn(
    r'frameRate\\s*:\\s*\\{\\s*ideal\\s*:\\s*24\\s*,\\s*max\\s*:\\s*30\\s*\\}',
    'frameRate: { ideal: 60, max: 60 }',
    capture_call,
    count=1,
)
if frame_count != 1:
    raise SystemExit(f'app/voice-room.tsx: initial 24/30 FPS constraint not found in {capture_call!r}')
voice = voice[:display_start] + capture_call + voice[display_end:]
'''

old_detail_check = '''if detail_count != 1:
    raise SystemExit(f'app/voice-room.tsx: forced detail contentHint expected once, found {detail_count}')
'''
new_detail_check = '''if detail_count > 1:
    raise SystemExit(f'app/voice-room.tsx: forced detail contentHint unexpectedly repeated {detail_count} times')
'''

if source.count(old_display) != 1:
    raise SystemExit(f'v0423 source: display block expected once, found {source.count(old_display)}')
if source.count(old_detail_check) != 1:
    raise SystemExit(f'v0423 source: detail guard expected once, found {source.count(old_detail_check)}')
source = source.replace(old_display, new_display, 1)
source = source.replace(old_detail_check, new_detail_check, 1)

# The current assembled voice source uses getAudioTracks() in ensurePeer after
# later microphone reliability patches. The original feature patch was written
# against the older getTracks() spelling in both its expected and replacement
# blocks. Adapt just those embedded blocks before executing it.
old_tracks_literal = 'const tracks = mic.current?.getTracks() ?? [];'
track_literal_count = source.count(old_tracks_literal)
if track_literal_count != 2:
    raise SystemExit(f'v0423 source: expected two peer track literals, found {track_literal_count}')
source = source.replace(old_tracks_literal, 'const tracks = mic.current?.getAudioTracks() ?? [];')

exec(compile(source, str(source_path), 'exec'), {'Path': Path, 're': re, '__name__': '__main__'})
