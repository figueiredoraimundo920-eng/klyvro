from pathlib import Path
import re

ROOT = Path('.')


def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.16 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.15";', 'const KLYVRO_BUILD = "0.4.16";')
once('package.json', '"version": "0.4.15"', '"version": "0.4.16"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.15', 'VOZ • CORE v0.4.16')

# A microphone track can end while the user remains in the call (USB/Bluetooth
# device removed, OS route switched, browser permission/device failure). The old
# UI stayed visually unmuted until the user toggled twice. Bind the live track to
# a lifecycle handler so the UI becomes truthful immediately and the existing
# one-click v0.4.15 retry path becomes available.
once(
    'app/voice-room.tsx',
    '''  const deafenedRef = useRef(deafened);
  const retryMicRef = useRef<(() => Promise<void>) | null>(null);''',
    '''  const deafenedRef = useRef(deafened);
  const retryMicRef = useRef<(() => Promise<void>) | null>(null);

  const bindMicTrackLifecycle = (track: MediaStreamTrack) => {
    track.onended = () => {
      const current = mic.current?.getAudioTracks()[0];
      if (!current || current.id !== track.id) return;
      setMuted(true);
      onToast("Microfone desconectado. Clique em Ativar microfone para tentar novamente.");
    };
  };'''
)

# Bind the track obtained during the initial join.
once(
    'app/voice-room.tsx',
    '''        mic.current = await navigator.mediaDevices.getUserMedia({ audio: constraints });''',
    '''        mic.current = await navigator.mediaDevices.getUserMedia({ audio: constraints });
        const initialMicTrack = mic.current.getAudioTracks()[0];
        if (initialMicTrack) bindMicTrackLifecycle(initialMicTrack);'''
)

# Before replacing an old stream, detach its ended callback; then bind the new
# track so a later hardware/device loss is reflected immediately.
once(
    'app/voice-room.tsx',
    '''          mic.current?.getTracks().forEach((item) => item.stop());
          mic.current = stream;
          setMuted(false);''',
    '''          mic.current?.getTracks().forEach((item) => { item.onended = null; item.stop(); });
          mic.current = stream;
          bindMicTrackLifecycle(track);
          setMuted(false);'''
)

# Cleanup is intentional, so suppress the user-facing "microphone disconnected"
# path before stopping the tracks while leaving/unmounting the call.
once(
    'app/voice-room.tsx',
    '''    mic.current?.getTracks().forEach((track) => track.stop());
    mic.current = null;''',
    '''    mic.current?.getTracks().forEach((track) => { track.onended = null; track.stop(); });
    mic.current = null;'''
)

# Stopping screen share from the browser's native sharing chip/button ends the
# display track without invoking Klyvro's own "Parar tela" button. Previously
# that path only cleared the local preview, leaving the negotiated sender and
# explicit remote screen state active. Route native track end through stopScreen
# so replaceTrack(null) and the screen=false signal reach every peer too.
p = ROOT / 'app/voice-room.tsx'
text = p.read_text(encoding='utf-8')
pattern = re.compile(
    r'(?:stream\.getVideoTracks\(\)\[0\]|track)\.onended\s*=\s*\(\)\s*=>\s*\{\s*screenRef\.current\s*=\s*null;\s*setScreen\(null\);\s*\};'
)
text, count = pattern.subn('track.onended = () => { stopScreen(false); };', text, count=1)
if count != 1:
    raise SystemExit(f'app/voice-room.tsx: v0.4.16 expected one native screen-ended handler, found {count}')
p.write_text(text, encoding='utf-8')

print('Klyvro v0.4.16 microphone lifecycle + native screen-stop recovery patch applied')
