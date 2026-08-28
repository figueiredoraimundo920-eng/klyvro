from pathlib import Path
import re

ROOT = Path('.')


def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.18 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


def regex_once(path: str, pattern: str, replacement: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    next_text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.18 regex expected one target, found {count}: {pattern[:180]!r}')
    p.write_text(next_text, encoding='utf-8')


# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.17";', 'const KLYVRO_BUILD = "0.4.18";')
once('package.json', '"version": "0.4.17"', '"version": "0.4.18"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.17', 'VOZ • CORE v0.4.18')

# A successful Supabase heartbeat only proves signaling/presence reachability. It
# must not clear a WebRTC media failure. Recompute the aggregate call state from
# the live peer connections when the heartbeat recovers so the header remains
# truthful while any peer is failed/disconnected/negotiating. Anchor the whole
# heartbeat block because another recovery path intentionally has the same old
# one-line state transition.
once(
    'app/voice-room.tsx',
    '''      const voiceHeartbeat = async () => {
        const { error } = await supabase.rpc("klyvro_voice_heartbeat", { p_token: token, p_room_id: roomId });
        if (error) throw error;
        setState((current) => current === "error" ? "waiting" : current);
      };''',
    '''      const voiceHeartbeat = async () => {
        const { error } = await supabase.rpc("klyvro_voice_heartbeat", { p_token: token, p_room_id: roomId });
        if (error) throw error;
        setState((current) => {
          if (current !== "error") return current;
          const peerStates = [...pcs.current.values()].map((peer) => peer.connectionState);
          if (peerStates.some((peerState) => peerState === "failed" || peerState === "disconnected")) return "error";
          if (peerStates.length > 0 && peerStates.every((peerState) => peerState === "connected")) return "online";
          if (peerStates.length > 0) return "connecting";
          return "waiting";
        });
      };'''
)

# ICE gathering can produce the only viable route for a restrictive peer. A
# transient signaling RPC failure must not permanently discard that candidate.
# Replace the assembled connection's single ICE callback structurally because
# earlier source generations use slightly different toast wording. Retry only
# while the candidate still belongs to the exact same RTCPeerConnection.
regex_once(
    'app/voice-room.tsx',
    r'''        pc\.onicecandidate = \(event\) => \{.*?\n        \};(?=\n        pc\.ontrack = )''',
    '''        pc.onicecandidate = (event) => {
          if (!event.candidate) return;
          const candidate = event.candidate.toJSON();
          const sendCandidate = async (attempt = 1): Promise<void> => {
            if (pcs.current.get(remoteSlot) !== pc || pc.connectionState === "closed") return;
            try {
              await sendSignal(remoteSlot, "candidate", candidate);
            } catch (error) {
              if (attempt >= 3 || pcs.current.get(remoteSlot) !== pc || (pc.connectionState as string) === "closed") {
                console.warn("Klyvro ICE candidate signaling failed", { remoteSlot, attempt, error });
                onToast("Falha ao trocar rota de mídia. A recuperação da conexão continuará automaticamente.");
                return;
              }
              await new Promise<void>((resolve) => window.setTimeout(resolve, 250 * attempt));
              return sendCandidate(attempt + 1);
            }
          };
          void sendCandidate();
        };'''
)

# Apply the visual system after the reliability changes above. This runner only
# appends CSS; it intentionally does not change release metadata or call/chat
# data flow, so the v0.4.19 voice-navigation patch can still apply afterward.
visual_runner = Path('../patches/reliable/v0420-visual-css-only.py')
exec(compile(visual_runner.read_text(encoding='utf-8'), str(visual_runner), 'exec'), {'Path': Path, '__name__': '__main__'})

# Apply hi-res screen sharing and mention UI before v0.4.19 runs. The wrapper
# intentionally skips release metadata so the established version chain and
# validation remain unchanged.
feature_runner = Path('../patches/reliable/v0421-pre-v0419.py')
exec(compile(feature_runner.read_text(encoding='utf-8'), str(feature_runner), 'exec'), {'Path': Path, 're': re, '__name__': '__main__'})

# Keep the high single-viewer quality, but dynamically rebalance P2P screen
# bitrate/resolution as more viewers join so upload does not multiply unchecked.
adaptive_runner = Path('../patches/reliable/v0422-adaptive-screen-upload.py')
exec(compile(adaptive_runner.read_text(encoding='utf-8'), str(adaptive_runner), 'exec'), {'Path': Path, '__name__': '__main__'})

# Capture tab/system audio when the browser provides it, mix it with the mic on
# the existing audio path, and prefer smooth 1440p/60 over stutter-prone 4K/60.
screen_audio_runner = Path('../patches/reliable/v0423-screen-audio-smoothness.py')
exec(compile(screen_audio_runner.read_text(encoding='utf-8'), str(screen_audio_runner), 'exec'), {'Path': Path, 're': re, '__name__': '__main__'})

print('Klyvro v0.4.18 heartbeat/media-status + ICE retry + premium visual + mentions + adaptive smooth share/audio patch applied')
