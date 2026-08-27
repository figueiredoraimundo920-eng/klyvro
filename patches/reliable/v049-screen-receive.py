from pathlib import Path

ROOT = Path('.')

def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.9 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.8";', 'const KLYVRO_BUILD = "0.4.9";')
once('package.json', '"version": "0.4.8"', '"version": "0.4.9"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.8', 'VOZ • CORE v0.4.9')

# Screen state becomes an explicit signaling message instead of relying only on
# browser-specific MediaStreamTrack mute/unmute behavior.
once(
    'app/voice-room.tsx',
    'type SignalRow = { id: number; from_slot: number; kind: "description" | "candidate"; payload: RTCSessionDescriptionInit | RTCIceCandidateInit; created_at: string };',
    'type SignalRow = { id: number; from_slot: number; kind: "description" | "candidate" | "screen"; payload: RTCSessionDescriptionInit | RTCIceCandidateInit | { active?: boolean }; created_at: string };'
)

once(
    'app/voice-room.tsx',
    '''  const screenSenders = useRef(new Map<number, RTCRtpSender>());
  const remoteAudio = useRef(new Map<number, HTMLAudioElement>());''',
    '''  const screenSenders = useRef(new Map<number, RTCRtpSender>());
  const remoteVideoTracks = useRef(new Map<number, MediaStreamTrack>());
  const remoteScreenActive = useRef(new Set<number>());
  const remoteAudio = useRef(new Map<number, HTMLAudioElement>());'''
)

once(
    'app/voice-room.tsx',
    '''  const stopScreen = useCallback((announce = true) => {''',
    '''  const sendScreenStateTo = useCallback(async (toSlot: number, active: boolean) => {
    const token = tokenRef.current;
    const localSlot = localSlotRef.current;
    if (!token || !localSlot || !toSlot || toSlot === localSlot) return;
    const { error } = await supabase.rpc("klyvro_send_voice_signal", {
      p_token: token,
      p_room_id: roomId,
      p_to_slot: toSlot,
      p_kind: "screen",
      p_payload: { active },
    });
    if (error) throw error;
  }, [roomId]);

  const broadcastScreenState = useCallback(async (active: boolean) => {
    await Promise.allSettled([...pcs.current.keys()].map((slot) => sendScreenStateTo(slot, active)));
  }, [sendScreenStateTo]);

  const bindNegotiatedVideoSender = useCallback((remoteSlot: number, pc: RTCPeerConnection) => {
    const videoTransceivers = pc.getTransceivers().filter((transceiver) => transceiver.receiver.track?.kind === "video");
    const negotiated = videoTransceivers.find((transceiver) => transceiver.mid !== null) ?? videoTransceivers[0];
    if (!negotiated) return;
    try {
      if (negotiated.direction === "recvonly" || negotiated.direction === "inactive") negotiated.direction = "sendrecv";
    } catch {
      // Some browsers lock direction briefly while applying an SDP. The sender can still be rebound.
    }
    screenSenders.current.set(remoteSlot, negotiated.sender);
    const activeTrack = screenRef.current?.getVideoTracks()[0] ?? null;
    if (activeTrack) void negotiated.sender.replaceTrack(activeTrack).catch(() => undefined);
  }, []);

  const stopScreen = useCallback((announce = true) => {'''
)

once(
    'app/voice-room.tsx',
    '''    setScreenBusy(false);
    void replaceScreenTrackForPeers(null);''',
    '''    setScreenBusy(false);
    void replaceScreenTrackForPeers(null);
    void broadcastScreenState(false);'''
)

once(
    'app/voice-room.tsx',
    '''  }, [onToast, replaceScreenTrackForPeers]);''',
    '''  }, [broadcastScreenState, onToast, replaceScreenTrackForPeers]);'''
)

once(
    'app/voice-room.tsx',
    '''    screenSenders.current.clear();
    pendingCandidates.current.clear();''',
    '''    screenSenders.current.clear();
    remoteVideoTracks.current.clear();
    remoteScreenActive.current.clear();
    pendingCandidates.current.clear();'''
)

once(
    'app/voice-room.tsx',
    '''        screenSenders.current.delete(remoteSlot);
        pendingCandidates.current.delete(remoteSlot);''',
    '''        screenSenders.current.delete(remoteSlot);
        remoteVideoTracks.current.delete(remoteSlot);
        remoteScreenActive.current.delete(remoteSlot);
        pendingCandidates.current.delete(remoteSlot);'''
)

# Keep the receiver's video track even when it starts muted. Chromium-family
# browsers do not all emit onunmute consistently after replaceTrack(null -> screen).
old_ontrack = '''        pc.ontrack = (event) => {
          if (event.track.kind === "video") {
            const remoteStream = event.streams[0] ?? new MediaStream([event.track]);
            const showRemoteScreen = () => setRemoteScreens((current) => ({ ...current, [remoteSlot]: remoteStream }));
            if (!event.track.muted) showRemoteScreen();
            event.track.onended = () => detachRemoteScreen(remoteSlot, event.track.id);
            event.track.onmute = () => detachRemoteScreen(remoteSlot, event.track.id);
            event.track.onunmute = showRemoteScreen;
            return;
          }
'''
new_ontrack = '''        pc.ontrack = (event) => {
          if (event.track.kind === "video") {
            remoteVideoTracks.current.set(remoteSlot, event.track);
            const remoteStream = event.streams[0] ?? new MediaStream([event.track]);
            const showRemoteScreen = () => setRemoteScreens((current) => ({ ...current, [remoteSlot]: remoteStream }));
            if (remoteScreenActive.current.has(remoteSlot) || !event.track.muted) showRemoteScreen();
            event.track.onended = () => {
              remoteVideoTracks.current.delete(remoteSlot);
              remoteScreenActive.current.delete(remoteSlot);
              detachRemoteScreen(remoteSlot, event.track.id);
            };
            event.track.onmute = () => {
              if (!remoteScreenActive.current.has(remoteSlot)) detachRemoteScreen(remoteSlot, event.track.id);
            };
            event.track.onunmute = showRemoteScreen;
            return;
          }
'''
once('app/voice-room.tsx', old_ontrack, new_ontrack)

# When a peer connection reaches connected while our screen is already active,
# tell that new peer immediately.
once(
    'app/voice-room.tsx',
    '''          if (connected) setState("online");''',
    '''          if (connected) {
            setState("online");
            if (screenRef.current) void sendScreenStateTo(remoteSlot, true).catch(() => undefined);
          }'''
)

# The answerer can get a browser-created remote video transceiver. Rebind our
# screen sender to the transceiver that actually received a negotiated MID before
# creating the answer, fixing the one-way screen-share case.
once(
    'app/voice-room.tsx',
    '''          await pc.setRemoteDescription(description);
          await flushCandidates(remoteSlot, pc);
          const answer = await pc.createAnswer();''',
    '''          await pc.setRemoteDescription(description);
          bindNegotiatedVideoSender(remoteSlot, pc);
          await flushCandidates(remoteSlot, pc);
          const answer = await pc.createAnswer();'''
)

once(
    'app/voice-room.tsx',
    '''        } else if (pc.signalingState === "have-local-offer") {
          await pc.setRemoteDescription(description);
          await flushCandidates(remoteSlot, pc);
        }''',
    '''        } else if (pc.signalingState === "have-local-offer") {
          await pc.setRemoteDescription(description);
          bindNegotiatedVideoSender(remoteSlot, pc);
          await flushCandidates(remoteSlot, pc);
        }'''
)

# Explicit remote screen start/stop state. The already-negotiated receiver track
# is reused; no extra media permission is needed to WATCH a friend's screen.
once(
    'app/voice-room.tsx',
    '''        if (signal.kind === "candidate") {''',
    '''        if (signal.kind === "screen") {
          const active = Boolean((signal.payload as { active?: boolean })?.active);
          if (!active) {
            remoteScreenActive.current.delete(remoteSlot);
            detachRemoteScreen(remoteSlot);
            return;
          }
          remoteScreenActive.current.add(remoteSlot);
          const track = remoteVideoTracks.current.get(remoteSlot)
            ?? pc.getReceivers().find((receiver) => receiver.track?.kind === "video")?.track;
          if (track) {
            remoteVideoTracks.current.set(remoteSlot, track);
            const remoteStream = new MediaStream([track]);
            setRemoteScreens((current) => ({ ...current, [remoteSlot]: remoteStream }));
          }
          return;
        }

        if (signal.kind === "candidate") {'''
)

once(
    'app/voice-room.tsx',
    '''      await replaceScreenTrackForPeers(track);
      setScreenBusy(false);''',
    '''      await replaceScreenTrackForPeers(track);
      await broadcastScreenState(true);
      setScreenBusy(false);'''
)

print('Klyvro v0.4.9 symmetric screen-share patch applied')
