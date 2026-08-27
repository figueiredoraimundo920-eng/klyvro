from pathlib import Path

ROOT = Path('.')

def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.10 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

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

# Replace the old "failed -> waiting" behavior with an actual peer rebuild. A
# short grace period handles transient Chromium disconnected states; hard failed
# connections rebuild immediately. The lower profile slot remains the deterministic
# offerer, preventing glare while both browsers recover at roughly the same time.
once(
    'app/voice-room.tsx',
    '''        pc.onconnectionstatechange = () => {
          const connected = pc.connectionState === "connected";
          setPeers((current) => current[remoteSlot] ? { ...current, [remoteSlot]: { ...current[remoteSlot], connected } } : current);
          if (connected) {
            setState("online");
            if (screenRef.current) void sendScreenStateTo(remoteSlot, true).catch(() => undefined);
          }
          if (pc.connectionState === "failed") {
            setState("waiting");
            onToast(`Áudio com ${remoteName} não fechou. A rede pode exigir TURN.`);
          }
        };''',
    '''        pc.onconnectionstatechange = () => {
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
)

# A full RTCPeerConnection rebuild is more interoperable than only changing the
# label to "reconnecting". It refreshes ICE candidates, audio receivers and the
# negotiated screen-share transceiver. Existing screen sharing is rebound by the
# normal ensurePeer/connected path.
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

print('Klyvro v0.4.10 real WebRTC reconnect patch applied')
