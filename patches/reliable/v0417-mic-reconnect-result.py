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

# A rebuilt peer previously got only one chance to kick off renegotiation. A
# transient failure in either the offer RPC or the asymmetric restart-request RPC
# could leave the replacement RTCPeerConnection in "new" forever. Schedule a
# bounded fresh-peer retry. Rethrow the first failure so microphone recovery and
# other awaited callers keep reporting partial reconnection truthfully.
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

# The connection-state callbacks intentionally fire-and-forget. Consume the
# rejection there; restartPeer already schedules the bounded retry above.
once(
    'app/voice-room.tsx',
    '''                void restartPeer(remoteSlot, remoteName, pc);''',
    '''                void restartPeer(remoteSlot, remoteName, pc).catch((error) => {
                  console.warn("Klyvro automatic disconnected-peer restart failed", { remoteSlot, error });
                });'''
)
once(
    'app/voice-room.tsx',
    '''            void restartPeer(remoteSlot, remoteName, pc);''',
    '''            void restartPeer(remoteSlot, remoteName, pc).catch((error) => {
              console.warn("Klyvro automatic failed-peer restart failed", { remoteSlot, error });
            });'''
)

print('Klyvro v0.4.17 truthful mic status + bounded signaling retry patch applied')
