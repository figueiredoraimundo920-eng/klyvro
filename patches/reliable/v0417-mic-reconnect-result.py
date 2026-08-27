from pathlib import Path

ROOT = Path('.')


def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.17 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.16";', 'const KLYVRO_BUILD = "0.4.17";')
once('package.json', '"version": "0.4.16"', '"version": "0.4.17"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.16', 'VOZ • CORE v0.4.17')

# v0.4.15 correctly reacquires a missing microphone and starts peer rebuilds, but
# Promise.allSettled intentionally never throws. The old code ignored rejected
# peer restarts and always claimed that the microphone had been reconnected to
# the call. Keep the recovered microphone, but report signaling failures
# truthfully so a partial reconnection is not presented as fully successful.
once(
    'app/voice-room.tsx',
    '''          const activePeers = [...pcs.current.entries()];
          reconnectAttempts.current.clear();
          await Promise.allSettled(activePeers.map(async ([remoteSlot, pc]) => {
            const row = profilesRef.current[remoteSlot];
            const remoteName = String(row?.display_name || `Jogador ${remoteSlot}`).slice(0, 24);
            await restartPeer(remoteSlot, remoteName, pc);
          }));
          onToast("Microfone liberado e reconectado à call.");''',
    '''          const activePeers = [...pcs.current.entries()];
          reconnectAttempts.current.clear();
          const restartResults = await Promise.allSettled(activePeers.map(async ([remoteSlot, pc]) => {
            const row = profilesRef.current[remoteSlot];
            const remoteName = String(row?.display_name || `Jogador ${remoteSlot}`).slice(0, 24);
            await restartPeer(remoteSlot, remoteName, pc);
          }));
          const failedRestarts = restartResults.filter((result) => result.status === "rejected").length;
          if (failedRestarts > 0) {
            setState("error");
            onToast(`Microfone liberado, mas ${failedRestarts} conexão${failedRestarts === 1 ? "" : "ões"} de mídia ainda precisa${failedRestarts === 1 ? "" : "m"} reconectar.`);
          } else if (activePeers.length > 0) {
            onToast("Microfone liberado. Renegociação de mídia iniciada com a call.");
          } else {
            onToast("Microfone liberado.");
          }'''
)

print('Klyvro v0.4.17 truthful microphone peer-reconnect result patch applied')
