from pathlib import Path

ROOT = Path('.')


def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.15 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.14";', 'const KLYVRO_BUILD = "0.4.15";')
once('package.json', '"version": "0.4.14"', '"version": "0.4.15"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.14', 'VOZ • CORE v0.4.15')

# If microphone permission/device acquisition failed on join, the previous mute
# button could visually unmute even though there was no local audio track. Keep a
# retry hook that can acquire the mic later and rebuild existing peer connections
# so the recovered audio track is actually negotiated to every participant.
once(
    'app/voice-room.tsx',
    '''  const remoteAudio = useRef(new Map<number, HTMLAudioElement>());
  const deafenedRef = useRef(deafened);''',
    '''  const remoteAudio = useRef(new Map<number, HTMLAudioElement>());
  const deafenedRef = useRef(deafened);
  const retryMicRef = useRef<(() => Promise<void>) | null>(null);'''
)

once(
    'app/voice-room.tsx',
    '''    remoteAudio.current.clear();
    setScreen(null);''',
    '''    remoteAudio.current.clear();
    retryMicRef.current = null;
    setScreen(null);'''
)

once(
    'app/voice-room.tsx',
    '''      const handleSignal = async (signal: SignalRow) => {''',
    '''      retryMicRef.current = async () => {
        const liveTrack = mic.current?.getAudioTracks().find((track) => track.readyState === "live");
        if (liveTrack) {
          setMuted(false);
          return;
        }

        try {
          const constraints: MediaTrackConstraints = {
            ...(audio.inputDeviceId !== "default" ? { deviceId: { exact: audio.inputDeviceId } } : {}),
            echoCancellation: audio.echoCancellation,
            noiseSuppression: audio.noiseSuppression,
            autoGainControl: audio.autoGainControl,
          };
          const stream = await navigator.mediaDevices.getUserMedia({ audio: constraints });
          const track = stream.getAudioTracks()[0];
          if (!track) {
            stream.getTracks().forEach((item) => item.stop());
            throw new Error("Nenhuma faixa de microfone disponível");
          }

          mic.current?.getTracks().forEach((item) => item.stop());
          mic.current = stream;
          setMuted(false);

          const activePeers = [...pcs.current.entries()];
          reconnectAttempts.current.clear();
          await Promise.allSettled(activePeers.map(async ([remoteSlot, pc]) => {
            const row = profilesRef.current[remoteSlot];
            const remoteName = String(row?.display_name || `Jogador ${remoteSlot}`).slice(0, 24);
            await restartPeer(remoteSlot, remoteName, pc);
          }));
          onToast("Microfone liberado e reconectado à call.");
        } catch {
          setMuted(true);
          onToast("Ainda não consegui acessar o microfone. Verifique a permissão do navegador e tente novamente.");
        }
      };

      const handleSignal = async (signal: SignalRow) => {'''
)

# Both the full voice controls and the compact persistent dock use the same
# truthful behavior: if there is no live mic track, "Ativar microfone" retries
# permission/device acquisition instead of just flipping the visual state.
p = ROOT / 'app/voice-room.tsx'
text = p.read_text(encoding='utf-8')
old = 'onClick={() => setMuted((value) => !value)} aria-label={muted ? "Ativar microfone" : "Silenciar microfone"}'
new = 'onClick={() => { if (muted && !mic.current?.getAudioTracks().some((track) => track.readyState === "live")) { void retryMicRef.current?.(); return; } setMuted((value) => !value); }} aria-label={muted ? "Ativar microfone" : "Silenciar microfone"}'
count = text.count(old)
if count != 2:
    raise SystemExit(f'app/voice-room.tsx: v0.4.15 expected two mute controls, found {count}')
p.write_text(text.replace(old, new), encoding='utf-8')

print('Klyvro v0.4.15 in-call microphone permission/device recovery patch applied')
