from pathlib import Path

ROOT = Path('.')

def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.11 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.10";', 'const KLYVRO_BUILD = "0.4.11";')
once('package.json', '"version": "0.4.10"', '"version": "0.4.11"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.10', 'VOZ • CORE v0.4.11')

# Track transient failures per signal. A signaling cursor must never acknowledge
# an offer/answer/candidate/screen event before the browser has handled it.
once(
    'app/voice-room.tsx',
    '''  const lastSignalIdRef = useRef(0);
  const profilesRef = useRef<Record<number, ProfileRow>>({});''',
    '''  const lastSignalIdRef = useRef(0);
  const signalFailures = useRef(new Map<number, number>());
  const profilesRef = useRef<Record<number, ProfileRow>>({});'''
)

once(
    'app/voice-room.tsx',
    '''    reconnectAttempts.current.clear();
    reconnectInFlight.current.clear();
    pendingCandidates.current.clear();''',
    '''    reconnectAttempts.current.clear();
    reconnectInFlight.current.clear();
    signalFailures.current.clear();
    pendingCandidates.current.clear();'''
)

once(
    'app/voice-room.tsx',
    '''    lastSignalIdRef.current = 0;
    joinedAtRef.current = Date.now();''',
    '''    lastSignalIdRef.current = 0;
    signalFailures.current.clear();
    joinedAtRef.current = Date.now();'''
)

# Process signals in order. On a transient browser/WebRTC failure, leave the
# cursor behind and retry the same row on the next poll instead of losing it.
# After three failures, skip only that row so a permanently unusable signal
# cannot block the room forever.
once(
    'app/voice-room.tsx',
    '''        for (const raw of (data ?? []) as SignalRow[]) {
          lastSignalIdRef.current = Math.max(lastSignalIdRef.current, Number(raw.id));
          await handleSignal(raw).catch(() => notify("Erro ao negociar uma conexão de áudio."));
        }''',
    '''        for (const raw of (data ?? []) as SignalRow[]) {
          const signalId = Number(raw.id);
          try {
            await handleSignal(raw);
            signalFailures.current.delete(signalId);
            lastSignalIdRef.current = Math.max(lastSignalIdRef.current, signalId);
          } catch (error) {
            const failures = (signalFailures.current.get(signalId) ?? 0) + 1;
            signalFailures.current.set(signalId, failures);
            console.warn("Klyvro voice signal processing failed", { signalId, kind: raw.kind, failures, error });
            if (failures >= 3) {
              signalFailures.current.delete(signalId);
              lastSignalIdRef.current = Math.max(lastSignalIdRef.current, signalId);
              notify("Um sinal de mídia falhou repetidamente e foi ignorado para a call continuar.");
              continue;
            }
            break;
          }
        }'''
)

print('Klyvro v0.4.11 signaling acknowledgement/retry patch applied')
