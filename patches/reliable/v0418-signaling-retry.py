from pathlib import Path

ROOT = Path('.')


def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.18 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


def count_replace(path: str, old: str, new: str, expected: int):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != expected:
        raise SystemExit(f'{path}: v0.4.18 expected {expected} targets, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new), encoding='utf-8')


# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.17";', 'const KLYVRO_BUILD = "0.4.18";')
once('package.json', '"version": "0.4.17"', '"version": "0.4.18"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.17', 'VOZ • CORE v0.4.18')

# A rebuilt peer previously got only one chance to start renegotiation. If the
# offer RPC / restart-request RPC failed transiently, the replacement PC could
# remain in "new" forever because it had no connection-state transition to
# trigger another rebuild. Schedule a bounded fresh-peer retry, but rethrow the
# first failure so callers such as microphone recovery still report partial
# reconnection truthfully.
once(
    'app/voice-room.tsx',
    '''          ensurePeer(remoteSlot, remoteName);
          if (localSlot < remoteSlot) await maybeOffer(remoteSlot, remoteName);
          else await sendRestartRequestTo(remoteSlot);''',
    '''          ensurePeer(remoteSlot, remoteName);
          try {
            if (localSlot < remoteSlot) await maybeOffer(remoteSlot, remoteName);
            else await sendRestartRequestTo(remoteSlot);
          } catch (error) {
            console.warn("Klyvro peer renegotiation kickoff failed", { remoteSlot, attempt, error });
            const replacement = pcs.current.get(remoteSlot);
            if (replacement) {
              window.setTimeout(() => {
                const current = pcs.current.get(remoteSlot);
                if (current === replacement && current.connectionState !== "connected") {
                  void restartPeer(remoteSlot, remoteName, current).catch((retryError) => {
                    console.warn("Klyvro delayed peer renegotiation retry failed", { remoteSlot, retryError });
                  });
                }
              }, 1500);
            }
            throw error;
          }'''
)

# Connection-state callbacks deliberately fire-and-forget. Consume the rejection
# there so a transient signaling outage does not become an unhandled Promise,
# while restartPeer itself schedules the bounded retry above.
count_replace(
    'app/voice-room.tsx',
    '''                void restartPeer(remoteSlot, remoteName, pc);''',
    '''                void restartPeer(remoteSlot, remoteName, pc).catch((error) => {
                  console.warn("Klyvro automatic disconnected-peer restart failed", { remoteSlot, error });
                });''',
    1,
)
count_replace(
    'app/voice-room.tsx',
    '''            void restartPeer(remoteSlot, remoteName, pc);''',
    '''            void restartPeer(remoteSlot, remoteName, pc).catch((error) => {
              console.warn("Klyvro automatic failed-peer restart failed", { remoteSlot, error });
            });''',
    1,
)

print('Klyvro v0.4.18 bounded signaling-kickoff retry patch applied')
