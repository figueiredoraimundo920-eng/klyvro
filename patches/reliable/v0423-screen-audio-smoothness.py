from pathlib import Path
import re

ROOT = Path('.')
voice_path = ROOT / 'app/voice-room.tsx'
voice = voice_path.read_text(encoding='utf-8')

# ---------------------------------------------------------------------------
# Smooth high-quality sharing: the previous path initially requested 30 FPS,
# then tried to push 4K/60 and told WebRTC to preserve resolution. On normal
# consumer CPUs/uplinks that can create stutter even with one viewer. Use a
# practical 1440p/60 ceiling and prefer frame-rate for motion while keeping the
# multi-viewer upload budget bounded.
# ---------------------------------------------------------------------------
old_quality = '''type ScreenQualityProfile = { bitrate: number; fps: number; targetWidth: number; label: string };

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
new_quality = '''type ScreenQualityProfile = { bitrate: number; fps: number; targetWidth: number; label: string };

function screenQualityProfile(viewerCount: number): ScreenQualityProfile {
  if (viewerCount <= 1) return { bitrate: 10_000_000, fps: 60, targetWidth: 2560, label: "1440p/60" };
  if (viewerCount === 2) return { bitrate: 6_000_000, fps: 60, targetWidth: 1920, label: "1080p/60" };
  if (viewerCount === 3) return { bitrate: 4_200_000, fps: 45, targetWidth: 1920, label: "1080p/45" };
  return { bitrate: 3_000_000, fps: 30, targetWidth: 1600, label: "900p/30 adaptativo" };
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
    const tuned = parameters as RTCRtpSendParameters & { degradationPreference?: "maintain-resolution" | "maintain-framerate" | "balanced" };
    tuned.degradationPreference = sender.track?.contentHint === "motion" ? "maintain-framerate" : "balanced";
    await sender.setParameters(tuned);
  } catch (error) {
    console.warn("Klyvro could not rebalance screen quality", error);
  }
}
'''
if voice.count(old_quality) != 1:
    raise SystemExit(f'app/voice-room.tsx: smooth quality profile expected once, found {voice.count(old_quality)}')
voice = voice.replace(old_quality, new_quality, 1)

old_capture_constraints = '''        await track.applyConstraints({
          width: { ideal: 3840, max: 3840 },
          height: { ideal: 2160, max: 2160 },
          frameRate: { ideal: 60, max: 60 },
        });'''
new_capture_constraints = '''        await track.applyConstraints({
          width: { ideal: 2560, max: 2560 },
          height: { ideal: 1440, max: 1440 },
          frameRate: { ideal: 60, max: 60 },
        });'''
if voice.count(old_capture_constraints) != 1:
    raise SystemExit(f'app/voice-room.tsx: 4K capture block expected once, found {voice.count(old_capture_constraints)}')
voice = voice.replace(old_capture_constraints, new_capture_constraints, 1)
voice = voice.replace(
    'console.warn("Klyvro 4K/60 capture constraints unavailable; keeping the browser\'s best native capture", qualityError);',
    'console.warn("Klyvro 1440p/60 capture constraints unavailable; keeping the browser\'s best native capture", qualityError);',
    1,
)

# Ask the display picker for 60 FPS from the start and request captured audio.
# The browser still controls whether system/tab audio is actually available and
# the user must enable the audio checkbox in the chooser when it is offered.
pattern = re.compile(
    r'navigator\.mediaDevices\.getDisplayMedia\(\{\s*video:\s*\{\s*frameRate:\s*\{\s*ideal:\s*24,\s*max:\s*30\s*\}\s*\},\s*audio:\s*false\s*\}\)'
)
voice, display_count = pattern.subn(
    'navigator.mediaDevices.getDisplayMedia({ video: { width: { ideal: 2560, max: 2560 }, height: { ideal: 1440, max: 1440 }, frameRate: { ideal: 60, max: 60 } }, audio: true })',
    voice,
    count=1,
)
if display_count != 1:
    raise SystemExit(f'app/voice-room.tsx: getDisplayMedia 30fps/no-audio target expected once, found {display_count}')

# An older screen-share layer forced contentHint back to detail after the newer
# adaptive code selected motion/detail. Remove that override so 60 FPS capture
# can actually prefer motion and avoid visible stutter.
forced_detail = re.compile(r'\s*try\s*\{\s*track\.contentHint\s*=\s*"detail";\s*\}\s*catch\s*\{\s*\}')
voice, detail_count = forced_detail.subn('', voice, count=1)
if detail_count != 1:
    raise SystemExit(f'app/voice-room.tsx: forced detail contentHint expected once, found {detail_count}')

# ---------------------------------------------------------------------------
# Screen audio. Reuse the already-negotiated voice audio m-line instead of
# adding a second remote audio element. During screen share we create one Web
# Audio mix containing microphone + captured tab/system audio and replace the
# existing outbound audio track. Mute/PTT still controls the physical mic track,
# while screen audio remains audible. Stopping share restores the mic track.
# ---------------------------------------------------------------------------
refs_anchor = '  const screenSenders = useRef(new Map<number, RTCRtpSender>());'
if voice.count(refs_anchor) != 1:
    raise SystemExit(f'app/voice-room.tsx: screen sender ref expected once, found {voice.count(refs_anchor)}')
voice = voice.replace(
    refs_anchor,
    refs_anchor + '''\n  const screenAudioContextRef = useRef<AudioContext | null>(null);\n  const screenMixedTrackRef = useRef<MediaStreamTrack | null>(null);''',
    1,
)

helper_anchor = '  const rebalanceScreenQuality = useCallback(async () => {'
if voice.count(helper_anchor) != 1:
    raise SystemExit(f'app/voice-room.tsx: rebalance helper anchor expected once, found {voice.count(helper_anchor)}')
audio_helpers = r'''  const replaceOutboundAudioForPeers = useCallback(async (track: MediaStreamTrack | null) => {
    const updates = [...pcs.current.values()].map(async (pc) => {
      const audioTransceiver = pc.getTransceivers().find((transceiver) => transceiver.receiver.track?.kind === "audio");
      const sender = audioTransceiver?.sender ?? pc.getSenders().find((candidate) => candidate.track?.kind === "audio");
      if (!sender) return;
      await sender.replaceTrack(track);
      try {
        const parameters = sender.getParameters();
        if (parameters.encodings?.length) {
          parameters.encodings[0].maxBitrate = 192_000;
          await sender.setParameters(parameters);
        }
      } catch {
        // Audio bitrate hints are optional across browsers.
      }
    });
    await Promise.allSettled(updates);
  }, []);

  const stopScreenAudioMix = useCallback(async (restoreMic = true) => {
    const mixedTrack = screenMixedTrackRef.current;
    screenMixedTrackRef.current = null;
    if (restoreMic) {
      const micTrack = mic.current?.getAudioTracks().find((track) => track.readyState === "live") ?? null;
      await replaceOutboundAudioForPeers(micTrack);
    }
    if (mixedTrack && mixedTrack.readyState !== "ended") mixedTrack.stop();
    const context = screenAudioContextRef.current;
    screenAudioContextRef.current = null;
    if (context && context.state !== "closed") await context.close().catch(() => undefined);
  }, [replaceOutboundAudioForPeers]);

  const startScreenAudioMix = useCallback(async (stream: MediaStream) => {
    await stopScreenAudioMix(true);
    const sharedAudioTrack = stream.getAudioTracks().find((track) => track.readyState === "live") ?? null;
    if (!sharedAudioTrack) return false;

    try {
      const context = new AudioContext({ latencyHint: "interactive" });
      if (context.state === "suspended") await context.resume().catch(() => undefined);
      const destination = context.createMediaStreamDestination();

      const sharedSource = context.createMediaStreamSource(new MediaStream([sharedAudioTrack]));
      const sharedGain = context.createGain();
      sharedGain.gain.value = 0.9;
      sharedSource.connect(sharedGain).connect(destination);

      const micTrack = mic.current?.getAudioTracks().find((track) => track.readyState === "live") ?? null;
      if (micTrack) {
        const micSource = context.createMediaStreamSource(new MediaStream([micTrack]));
        micSource.connect(destination);
      }

      const mixedTrack = destination.stream.getAudioTracks()[0] ?? null;
      if (!mixedTrack) {
        await context.close().catch(() => undefined);
        return false;
      }
      mixedTrack.enabled = true;
      screenAudioContextRef.current = context;
      screenMixedTrackRef.current = mixedTrack;
      await replaceOutboundAudioForPeers(mixedTrack);
      return true;
    } catch (error) {
      console.warn("Klyvro could not mix captured screen audio", error);
      await stopScreenAudioMix(true);
      return false;
    }
  }, [replaceOutboundAudioForPeers, stopScreenAudioMix]);

'''
voice = voice.replace(helper_anchor, audio_helpers + helper_anchor, 1)

# If the mic was blocked at join, keep an outbound-capable audio m-line so a
# later screen-audio track (or recovered mic) can be attached without a brand
# new SDP shape.
peer_audio_old = '''        const tracks = mic.current?.getTracks() ?? [];
        if (tracks.length) tracks.forEach((track) => pc.addTrack(track, mic.current!));
        else pc.addTransceiver("audio", { direction: "recvonly" });'''
peer_audio_new = '''        const tracks = mic.current?.getTracks() ?? [];
        if (tracks.length) tracks.forEach((track) => pc.addTrack(track, mic.current!));
        else pc.addTransceiver("audio", { direction: "sendrecv" });
        const sharedAudioTrack = screenMixedTrackRef.current;
        if (sharedAudioTrack) {
          const audioSender = pc.getTransceivers().find((transceiver) => transceiver.receiver.track?.kind === "audio")?.sender;
          if (audioSender) void audioSender.replaceTrack(sharedAudioTrack).catch(() => undefined);
        }'''
if voice.count(peer_audio_old) != 1:
    raise SystemExit(f'app/voice-room.tsx: peer audio transceiver block expected once, found {voice.count(peer_audio_old)}')
voice = voice.replace(peer_audio_old, peer_audio_new, 1)

# Start the audio mix as soon as the browser returns the captured stream.
start_anchor = '      screenRef.current = stream;'
if voice.count(start_anchor) != 1:
    raise SystemExit(f'app/voice-room.tsx: screenRef start assignment expected once, found {voice.count(start_anchor)}')
voice = voice.replace(
    start_anchor,
    start_anchor + '''\n      const sharedAudioActive = await startScreenAudioMix(stream);\n      if (!sharedAudioActive) onToast("Tela aberta sem áudio. Para enviar som, marque Compartilhar áudio no seletor do navegador.");''',
    1,
)

# Restore the microphone before removing the screen track from peers.
stop_anchor = '''    setScreenBusy(false);
    void replaceScreenTrackForPeers(null);'''
if voice.count(stop_anchor) != 1:
    raise SystemExit(f'app/voice-room.tsx: stop-screen reset expected once, found {voice.count(stop_anchor)}')
voice = voice.replace(
    stop_anchor,
    '''    setScreenBusy(false);
    void stopScreenAudioMix(true);
    void replaceScreenTrackForPeers(null);''',
    1,
)

# Full room cleanup closes the Web Audio graph as well. No restore is needed
# because every peer connection is being closed at the same time.
cleanup_anchor = '    screenSenders.current.clear();'
if voice.count(cleanup_anchor) != 1:
    raise SystemExit(f'app/voice-room.tsx: cleanup screenSenders clear expected once, found {voice.count(cleanup_anchor)}')
voice = voice.replace(
    cleanup_anchor,
    cleanup_anchor + '''\n    screenMixedTrackRef.current?.stop();\n    screenMixedTrackRef.current = null;\n    const screenAudioContext = screenAudioContextRef.current;\n    screenAudioContextRef.current = null;\n    if (screenAudioContext && screenAudioContext.state !== "closed") void screenAudioContext.close().catch(() => undefined);''',
    1,
)

# If microphone permission is recovered while sharing, rebuild the audio mix so
# the newly acquired mic joins the already-active screen sound.
mic_recovery_old = '''          mic.current = stream;
          setMuted(false);'''
mic_recovery_new = '''          mic.current = stream;
          setMuted(false);
          if (screenRef.current) await startScreenAudioMix(screenRef.current);'''
if voice.count(mic_recovery_old) != 1:
    raise SystemExit(f'app/voice-room.tsx: mic recovery assignment expected once, found {voice.count(mic_recovery_old)}')
voice = voice.replace(mic_recovery_old, mic_recovery_new, 1)

# Make the success toast truthful about whether the browser actually returned an
# audio track. Keep the historical sentence prefix because the workflow validates
# it as a screen-share invariant.
old_toast = 'onToast("Sua tela agora está sendo transmitida para a call • qualidade automática: máximo com 1 espectador, upload equilibrado com vários");'
new_toast = 'onToast(`Sua tela agora está sendo transmitida para a call • ${sharedAudioActive ? "som incluído" : "sem som"} • qualidade automática para máxima fluidez`);'
if voice.count(old_toast) != 1:
    raise SystemExit(f'app/voice-room.tsx: screen success toast expected once, found {voice.count(old_toast)}')
voice = voice.replace(old_toast, new_toast, 1)

voice_path.write_text(voice, encoding='utf-8')
print('Klyvro screen audio mix + 1440p60 smooth adaptive sharing patch applied')
