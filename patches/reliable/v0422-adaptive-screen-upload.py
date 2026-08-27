from pathlib import Path

ROOT = Path('.')
voice_path = ROOT / 'app/voice-room.tsx'
voice = voice_path.read_text(encoding='utf-8')

old_quality = '''const SCREEN_MAX_BITRATE = 24_000_000;
const SCREEN_MAX_FPS = 60;

async function tuneScreenSender(sender: RTCRtpSender) {
  try {
    const parameters = sender.getParameters();
    if (!parameters.encodings || parameters.encodings.length === 0) parameters.encodings = [{}];
    for (const encoding of parameters.encodings) {
      encoding.maxBitrate = SCREEN_MAX_BITRATE;
      encoding.maxFramerate = SCREEN_MAX_FPS;
      encoding.scaleResolutionDownBy = 1;
    }
    const tuned = parameters as RTCRtpSendParameters & { degradationPreference?: "maintain-resolution" };
    tuned.degradationPreference = "maintain-resolution";
    await sender.setParameters(tuned);
  } catch (error) {
    console.warn("Klyvro could not apply the full screen quality ceiling", error);
  }
}
'''

new_quality = '''type ScreenQualityProfile = { bitrate: number; fps: number; targetWidth: number; label: string };

function screenQualityProfile(viewerCount: number): ScreenQualityProfile {
  if (viewerCount <= 1) return { bitrate: 20_000_000, fps: 60, targetWidth: 3840, label: "4K/60" };
  if (viewerCount === 2) return { bitrate: 8_000_000, fps: 60, targetWidth: 2560, label: "1440p/60" };
  if (viewerCount === 3) return { bitrate: 5_200_000, fps: 60, targetWidth: 1920, label: "1080p/60" };
  return { bitrate: 4_000_000, fps: 45, targetWidth: 1920, label: "1080p adaptativo" };
}

async function tuneScreenSender(sender: RTCRtpSender, viewerCount: number) {
  try {
    const profile = screenQualityProfile(Math.max(1, viewerCount));
    const sourceWidth = Number(sender.track?.getSettings().width || profile.targetWidth);
    const scale = Math.max(1, sourceWidth / profile.targetWidth);
    const parameters = sender.getParameters();
    if (!parameters.encodings || parameters.encodings.length === 0) parameters.encodings = [{}];
    for (const encoding of parameters.encodings) {
      encoding.maxBitrate = profile.bitrate;
      encoding.maxFramerate = profile.fps;
      encoding.scaleResolutionDownBy = scale;
    }
    const tuned = parameters as RTCRtpSendParameters & { degradationPreference?: "maintain-resolution" };
    tuned.degradationPreference = "maintain-resolution";
    await sender.setParameters(tuned);
  } catch (error) {
    console.warn("Klyvro could not rebalance screen quality", error);
  }
}
'''

if voice.count(old_quality) != 1:
    raise SystemExit(f'app/voice-room.tsx: adaptive quality helper expected once, found {voice.count(old_quality)}')
voice = voice.replace(old_quality, new_quality, 1)

bind_anchor = '  const bindNegotiatedVideoSender = useCallback((remoteSlot: number, pc: RTCPeerConnection) => {'
if voice.count(bind_anchor) != 1:
    raise SystemExit(f'app/voice-room.tsx: bindNegotiatedVideoSender anchor expected once, found {voice.count(bind_anchor)}')
rebalance = '''  const rebalanceScreenQuality = useCallback(async () => {
    if (!screenRef.current) return;
    const activeSenders = [...screenSenders.current.values()].filter((sender) => sender.track?.kind === "video");
    const viewerCount = Math.max(1, activeSenders.length);
    await Promise.allSettled(activeSenders.map((sender) => tuneScreenSender(sender, viewerCount)));
  }, []);

'''
voice = voice.replace(bind_anchor, rebalance + bind_anchor, 1)

late_old = 'if (activeTrack) void negotiated.sender.replaceTrack(activeTrack).then(() => tuneScreenSender(negotiated.sender)).catch(() => undefined);'
late_new = 'if (activeTrack) void negotiated.sender.replaceTrack(activeTrack).then(() => rebalanceScreenQuality()).catch(() => undefined);'
if voice.count(late_old) != 1:
    raise SystemExit(f'app/voice-room.tsx: late peer quality target expected once, found {voice.count(late_old)}')
voice = voice.replace(late_old, late_new, 1)

bind_tail_old = '''    if (activeTrack) void negotiated.sender.replaceTrack(activeTrack).then(() => rebalanceScreenQuality()).catch(() => undefined);
  }, []);'''
bind_tail_new = '''    if (activeTrack) void negotiated.sender.replaceTrack(activeTrack).then(() => rebalanceScreenQuality()).catch(() => undefined);
  }, [rebalanceScreenQuality]);'''
if voice.count(bind_tail_old) != 1:
    raise SystemExit(f'app/voice-room.tsx: bind callback dependency target expected once, found {voice.count(bind_tail_old)}')
voice = voice.replace(bind_tail_old, bind_tail_new, 1)

fanout_old = 'await Promise.allSettled([...screenSenders.current.values()].map((sender) => tuneScreenSender(sender)));'
fanout_new = 'await rebalanceScreenQuality();'
if voice.count(fanout_old) != 1:
    raise SystemExit(f'app/voice-room.tsx: initial quality fanout expected once, found {voice.count(fanout_old)}')
voice = voice.replace(fanout_old, fanout_new, 1)

delete_anchor = 'screenSenders.current.delete(remoteSlot);'
delete_count = voice.count(delete_anchor)
if delete_count < 1:
    raise SystemExit('app/voice-room.tsx: no screen sender cleanup target found')
voice = voice.replace(delete_anchor, delete_anchor + '\n          if (screenRef.current) window.setTimeout(() => { void rebalanceScreenQuality(); }, 0);')

old_toast = 'onToast("Sua tela agora está sendo transmitida para a call • até 4K/60 FPS quando a rede permitir");'
new_toast = 'onToast("Sua tela agora está sendo transmitida para a call • qualidade automática: máximo com 1 espectador, upload equilibrado com vários");'
if voice.count(old_toast) == 1:
    voice = voice.replace(old_toast, new_toast, 1)

voice_path.write_text(voice, encoding='utf-8')
print(f'Klyvro adaptive screen-share upload balancing applied; cleanup_paths={delete_count}')