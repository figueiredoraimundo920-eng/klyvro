from pathlib import Path
import re

ROOT = Path('.')

def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.10 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

def regex_once(path: str, pattern: str, replacement: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    next_text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.10 regex expected one target, found {count}: {pattern[:180]!r}')
    p.write_text(next_text, encoding='utf-8')

# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.9";', 'const KLYVRO_BUILD = "0.4.10";')
once('package.json', '"version": "0.4.9"', '"version": "0.4.10"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.9', 'VOZ • CORE v0.4.10')

# Track reconnect attempts/in-flight rebuilds per remote peer.
once(
    'app/voice-room.tsx',
    '''  const remoteVideoTracks = useRef(new Map<number, MediaStreamTrack>());
  const remoteScreenActive = useRef(new Set<number>());
  const remoteAudio = useRef(new Map<number, HTMLAudioElement>());''',
    '''  const remoteVideoTracks = useRef(new Map<number, MediaStreamTrack>());
  const remoteScreenActive = useRef(new Set<number>());
  const reconnectAttempts = useRef(new Map<number, number>());
  const reconnectInFlight = useRef(new Set<number>());
  const remoteAudio = useRef(new Map<number, HTMLAudioElement>());'''
)

once(
    'app/voice-room.tsx',
    '''    remoteVideoTracks.current.clear();
    remoteScreenActive.current.clear();
    pendingCandidates.current.clear();''',
    '''    remoteVideoTracks.current.clear();
    remoteScreenActive.current.clear();
    reconnectAttempts.current.clear();
    reconnectInFlight.current.clear();
    pendingCandidates.current.clear();'''
)

once(
    'app/voice-room.tsx',
    '''        remoteVideoTracks.current.delete(remoteSlot);
        remoteScreenActive.current.delete(remoteSlot);
        pendingCandidates.current.delete(remoteSlot);''',
    '''        remoteVideoTracks.current.delete(remoteSlot);
        remoteScreenActive.current.delete(remoteSlot);
        reconnectAttempts.current.delete(remoteSlot);
        reconnectInFlight.current.delete(remoteSlot);
        pendingCandidates.current.delete(remoteSlot);'''
)

# The assembled v0.4.9 source has evolved across several patches, so target the
# single connection-state handler structurally rather than depending on old copy.
connection_handler = '''        pc.onconnectionstatechange = () => {
          const connectionState = pc.connectionState;
          const connected = connectionState === "connected";
          setPeers((current) => current[remoteSlot] ? { ...current, [remoteSlot]: { ...current[remoteSlot], connected } } : current);
          if (connected) {
            reconnectAttempts.current.delete(remoteSlot);
            reconnectInFlight.current.delete(remoteSlot);
            setState("online");
            if (screenRef.current) void sendScreenStateTo(remoteSlot, true).catch(() => undefined);
            return;
          }
          if (connectionState === "disconnected") {
            setState("error");
            window.setTimeout(() => {
              if (pcs.current.get(remoteSlot) === pc && pc.connectionState === "disconnected") {
                void restartPeer(remoteSlot, remoteName, pc);
              }
            }, 1800);
            return;
          }
          if (connectionState === "failed") {
            setState("error");
            void restartPeer(remoteSlot, remoteName, pc);
          }
        };'''
regex_once(
    'app/voice-room.tsx',
    r'        pc\.onconnectionstatechange = \(\) => \{.*?\n        \};(?=\n        return pc;)',
    connection_handler
)

# A full RTCPeerConnection rebuild refreshes ICE candidates, audio receivers and
# the negotiated screen-share transceiver. Lower slot remains deterministic offerer.
once(
    'app/voice-room.tsx',
    '''      const handleSignal = async (signal: SignalRow) => {''',
    '''      const restartPeer = async (remoteSlot: number, remoteName: string, failedPc: RTCPeerConnection) => {
        if (pcs.current.get(remoteSlot) !== failedPc || reconnectInFlight.current.has(remoteSlot)) return;
        reconnectInFlight.current.add(remoteSlot);
        const attempt = (reconnectAttempts.current.get(remoteSlot) ?? 0) + 1;
        reconnectAttempts.current.set(remoteSlot, attempt);
        try {
          pcs.current.delete(remoteSlot);
          failedPc.onconnectionstatechange = null;
          failedPc.onicecandidate = null;
          failedPc.ontrack = null;
          failedPc.close();
          screenSenders.current.delete(remoteSlot);
          remoteVideoTracks.current.delete(remoteSlot);
          remoteScreenActive.current.delete(remoteSlot);
          pendingCandidates.current.delete(remoteSlot);
          offerStarted.current.delete(remoteSlot);
          detachRemoteScreen(remoteSlot);
          const element = remoteAudio.current.get(remoteSlot);
          if (element) {
            element.pause();
            element.srcObject = null;
            remoteAudio.current.delete(remoteSlot);
          }

          if (attempt > 3) {
            onToast(`Não consegui restabelecer a mídia com ${remoteName}. Esta rede pode precisar de TURN.`);
            return;
          }

          ensurePeer(remoteSlot, remoteName);
          if (localSlot < remoteSlot) await maybeOffer(remoteSlot, remoteName);
        } finally {
          reconnectInFlight.current.delete(remoteSlot);
        }
      };

      const handleSignal = async (signal: SignalRow) => {'''
)

# Signaling acknowledgement reliability: a row is acknowledged only after the
# browser successfully handles it. This prevents one transient SDP/WebRTC error
# from permanently discarding an offer/answer/screen event.
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
    '''    lastSignalIdRef.current = 0;
    joinedAtRef.current = Date.now();''',
    '''    lastSignalIdRef.current = 0;
    signalFailures.current.clear();
    joinedAtRef.current = Date.now();'''
)

signal_loop = '''        for (const raw of (data ?? []) as SignalRow[]) {
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
regex_once(
    'app/voice-room.tsx',
    r'        for \(const raw of \(data \?\? \[\]\) as SignalRow\[\]\) \{\n          lastSignalIdRef\.current = Math\.max\(lastSignalIdRef\.current, Number\(raw\.id\)\);\n          await handleSignal\(raw\).*?\n        \}',
    signal_loop
)

print('Klyvro v0.4.10 real WebRTC reconnect + signal acknowledgement patch applied')
