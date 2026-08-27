from pathlib import Path

ROOT = Path('.')


def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.14 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.13";', 'const KLYVRO_BUILD = "0.4.14";')
once('package.json', '"version": "0.4.13"', '"version": "0.4.14"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.13', 'VOZ • CORE v0.4.14')

# ensurePeer/ontrack is created inside join(), so it can retain the value of
# deafened from the moment the call started. If the user deafens later and a new
# peer joins afterwards, that late peer's Audio element must still start muted.
once(
    'app/voice-room.tsx',
    '''  const remoteAudio = useRef(new Map<number, HTMLAudioElement>());''',
    '''  const remoteAudio = useRef(new Map<number, HTMLAudioElement>());
  const deafenedRef = useRef(deafened);'''
)

once(
    'app/voice-room.tsx',
    '''  useEffect(() => { remoteAudio.current.forEach((element) => { element.muted = deafened; }); }, [deafened]);''',
    '''  useEffect(() => {
    deafenedRef.current = deafened;
    remoteAudio.current.forEach((element) => { element.muted = deafened; });
  }, [deafened]);'''
)

once(
    'app/voice-room.tsx',
    '''          element.muted = deafened;
          element.srcObject = stream;''',
    '''          element.muted = deafenedRef.current;
          element.srcObject = stream;'''
)

print('Klyvro v0.4.14 late-peer deafen synchronization patch applied')
