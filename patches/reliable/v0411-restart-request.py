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

# A higher-slot peer can detect a broken P2P path before the deterministic
# lower-slot offerer does. Add a tiny control signal so it can request that the
# offerer rebuild and renegotiate instead of waiting indefinitely.
once(
    'app/voice-room.tsx',
    'type SignalRow = { id: number; from_slot: number; kind: "description" | "candidate" | "screen"; payload: RTCSessionDescriptionInit | RTCIceCandidateInit | { active?: boolean }; created_at: string };',
    'type SignalRow = { id: number; from_slot: number; kind: "description" | "candidate" | "screen" | "restart"; payload: RTCSessionDescriptionInit | RTCIceCandidateInit | { active?: boolean } | Record<string, never>; created_at: string };'
)

once(
    'app/voice-room.tsx',
    '''  const broadcastScreenState = useCallback(async (active: boolean) => {
    await Promise.allSettled([...pcs.current.keys()].map((slot) => sendScreenStateTo(slot, active)));
  }, [sendScreenStateTo]);''',
    '''  const sendRestartRequestTo = useCallback(async (toSlot: number) => {
    const token = tokenRef.current;
    const localSlot = localSlotRef.current;
    if (!token || !localSlot || !toSlot || toSlot === localSlot) return;
    const { error } = await supabase.rpc("klyvro_send_voice_signal", {
      p_token: token,
      p_room_id: roomId,
      p_to_slot: toSlot,
      p_kind: "restart",
      p_payload: {},
    });
    if (error) throw error;
  }, [roomId]);

  const broadcastScreenState = useCallback(async (active: boolean) => {
    await Promise.allSettled([...pcs.current.keys()].map((slot) => sendScreenStateTo(slot, active)));
  }, [sendScreenStateTo]);'''
)

once(
    'app/voice-room.tsx',
    '''          ensurePeer(remoteSlot, remoteName);
          if (localSlot < remoteSlot) await maybeOffer(remoteSlot, remoteName);''',
    '''          ensurePeer(remoteSlot, remoteName);
          if (localSlot < remoteSlot) await maybeOffer(remoteSlot, remoteName);
          else await sendRestartRequestTo(remoteSlot);'''
)

once(
    'app/voice-room.tsx',
    '''        if (signal.kind === "screen") {''',
    '''        if (signal.kind === "restart") {
          // Only the deterministic lower-slot offerer acts on restart requests.
          // This resolves one-sided network failures without introducing SDP glare.
          if (localSlot < remoteSlot) {
            const current = pcs.current.get(remoteSlot);
            if (current) await restartPeer(remoteSlot, remoteName, current);
            else {
              ensurePeer(remoteSlot, remoteName);
              await maybeOffer(remoteSlot, remoteName);
            }
          }
          return;
        }

        if (signal.kind === "screen") {'''
)

print('Klyvro v0.4.11 asymmetric WebRTC restart request patch applied')
