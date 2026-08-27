from pathlib import Path

ROOT = Path('.')

def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.12 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.11";', 'const KLYVRO_BUILD = "0.4.12";')
once('package.json', '"version": "0.4.11"', '"version": "0.4.12"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.11', 'VOZ • CORE v0.4.12')

# In multi-peer calls, a single healthy peer must not overwrite the aggregate
# room state while another connection is still disconnected/failed/negotiating.
# Keep per-peer UI as-is, but derive the global state from every live PC.
old_handler = '''        pc.onconnectionstatechange = () => {
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

new_handler = '''        pc.onconnectionstatechange = () => {
          const connectionState = pc.connectionState;
          const connected = connectionState === "connected";
          setPeers((current) => current[remoteSlot] ? { ...current, [remoteSlot]: { ...current[remoteSlot], connected } } : current);
          if (connected) {
            reconnectAttempts.current.delete(remoteSlot);
            reconnectInFlight.current.delete(remoteSlot);
            const peerStates = [...pcs.current.values()].map((peer) => peer.connectionState);
            if (peerStates.some((peerState) => peerState === "failed" || peerState === "disconnected")) setState("error");
            else if (peerStates.length > 0 && peerStates.every((peerState) => peerState === "connected")) setState("online");
            else setState("connecting");
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
            return;
          }
          if (connectionState === "connecting" || connectionState === "new") setState("connecting");
        };'''

once('app/voice-room.tsx', old_handler, new_handler)

print('Klyvro v0.4.12 truthful multi-peer call status patch applied')
