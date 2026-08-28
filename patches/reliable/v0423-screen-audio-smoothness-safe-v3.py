from pathlib import Path
import re

source_path = Path('../patches/reliable/v0423-screen-audio-smoothness.py')
source = source_path.read_text(encoding='utf-8')

# 1) Rewrite getDisplayMedia without relying on object formatting.
old_display = '''pattern = re.compile(
    r'navigator\\.mediaDevices\\.getDisplayMedia\\(\\{\\s*video:\\s*\\{\\s*frameRate:\\s*\\{\\s*ideal:\\s*24,\\s*max:\\s*30\\s*\\}\\s*\\},\\s*audio:\\s*false\\s*\\}\\)'
)
voice, display_count = pattern.subn(
    'navigator.mediaDevices.getDisplayMedia({ video: { width: { ideal: 2560, max: 2560 }, height: { ideal: 1440, max: 1440 }, frameRate: { ideal: 60, max: 60 } }, audio: true })',
    voice,
    count=1,
)
if display_count != 1:
    raise SystemExit(f'app/voice-room.tsx: getDisplayMedia 30fps/no-audio target expected once, found {display_count}')
'''
new_display = '''display_start = voice.find('navigator.mediaDevices.getDisplayMedia(')
if display_start < 0:
    raise SystemExit('app/voice-room.tsx: getDisplayMedia call not found')
display_end = voice.find(');', display_start)
if display_end < 0:
    raise SystemExit('app/voice-room.tsx: getDisplayMedia call end not found')
display_end += 1
capture_call = voice[display_start:display_end]
if not re.search(r'audio\\s*:\\s*false', capture_call):
    raise SystemExit(f'app/voice-room.tsx: getDisplayMedia audio:false not found in {capture_call!r}')
capture_call = re.sub(r'audio\\s*:\\s*false', 'audio: true', capture_call, count=1)
capture_call, frame_count = re.subn(
    r'frameRate\\s*:\\s*\\{\\s*ideal\\s*:\\s*24\\s*,\\s*max\\s*:\\s*30\\s*\\}',
    'frameRate: { ideal: 60, max: 60 }',
    capture_call,
    count=1,
)
if frame_count != 1:
    raise SystemExit(f'app/voice-room.tsx: initial 24/30 FPS constraint not found in {capture_call!r}')
voice = voice[:display_start] + capture_call + voice[display_end:]
'''

# 2) The old forced-detail line is absent in some assembled TypeScript versions.
old_detail_check = '''if detail_count != 1:
    raise SystemExit(f'app/voice-room.tsx: forced detail contentHint expected once, found {detail_count}')
'''
new_detail_check = '''if detail_count > 1:
    raise SystemExit(f'app/voice-room.tsx: forced detail contentHint unexpectedly repeated {detail_count} times')
'''

# 3) Wire screen audio into the current peer audio m-line structurally. Recent
# microphone patches use getAudioTracks(), while older source used getTracks().
old_peer_section = '''peer_audio_old = \'''\'''\'''        const tracks = mic.current?.getTracks() ?? [];
        if (tracks.length) tracks.forEach((track) => pc.addTrack(track, mic.current!));
        else pc.addTransceiver("audio", { direction: "recvonly" });\'''\'''\'''
peer_audio_new = \'''\'''\'''        const tracks = mic.current?.getTracks() ?? [];
        if (tracks.length) tracks.forEach((track) => pc.addTrack(track, mic.current!));
        else pc.addTransceiver("audio", { direction: "sendrecv" });
        const sharedAudioTrack = screenMixedTrackRef.current;
        if (sharedAudioTrack) {
          const audioSender = pc.getTransceivers().find((transceiver) => transceiver.receiver.track?.kind === "audio")?.sender;
          if (audioSender) void audioSender.replaceTrack(sharedAudioTrack).catch(() => undefined);
        }\'''\'''\'''
if voice.count(peer_audio_old) != 1:
    raise SystemExit(f'app/voice-room.tsx: peer audio transceiver block expected once, found {voice.count(peer_audio_old)}')
voice = voice.replace(peer_audio_old, peer_audio_new, 1)
'''
new_peer_section = '''audio_block = re.compile(
    r'''        const tracks = mic\\.current\\?\\.(?:getAudioTracks|getTracks)\\(\\) \\?\\? \\[\\];\\n        if \\(tracks\\.length\\) tracks\\.forEach\\(\\(track\\) => pc\\.addTrack\\(track, mic\\.current!\\)\\);\\n        else pc\\.addTransceiver\\("audio", \\{ direction: "recvonly" \\}\\);'''
)
peer_audio_new = '''        const tracks = mic.current?.getAudioTracks() ?? [];
        if (tracks.length) tracks.forEach((track) => pc.addTrack(track, mic.current!));
        else pc.addTransceiver("audio", { direction: "sendrecv" });
        const sharedAudioTrack = screenMixedTrackRef.current;
        if (sharedAudioTrack) {
          const audioSender = pc.getTransceivers().find((transceiver) => transceiver.receiver.track?.kind === "audio")?.sender;
          if (audioSender) void audioSender.replaceTrack(sharedAudioTrack).catch(() => undefined);
        }'''
voice, peer_audio_count = audio_block.subn(peer_audio_new, voice, count=1)
if peer_audio_count != 1:
    # Fallback bounded rewrite for harmless formatting differences.
    transceiver_pos = voice.find('pc.addTransceiver("audio"')
    video_pos = voice.find('pc.addTransceiver("video"', transceiver_pos)
    if transceiver_pos < 0 or video_pos < 0:
        raise SystemExit('app/voice-room.tsx: current peer audio/video transceiver section not found')
    section_start = max(0, voice.rfind('        const tracks =', 0, transceiver_pos))
    if section_start <= 0:
        raise SystemExit('app/voice-room.tsx: peer audio track section start not found')
    section = voice[section_start:video_pos]
    section, direction_count = re.subn(r'direction:\\s*"recvonly"', 'direction: "sendrecv"', section, count=1)
    if direction_count != 1:
        raise SystemExit(f'app/voice-room.tsx: recvonly audio direction expected once, found {direction_count}')
    if 'screenMixedTrackRef.current' not in section:
        section += '''        const sharedAudioTrack = screenMixedTrackRef.current;
        if (sharedAudioTrack) {
          const audioSender = pc.getTransceivers().find((transceiver) => transceiver.receiver.track?.kind === "audio")?.sender;
          if (audioSender) void audioSender.replaceTrack(sharedAudioTrack).catch(() => undefined);
        }
'''
    voice = voice[:section_start] + section + voice[video_pos:]
'''

for old, new, label in [
    (old_display, new_display, 'display capture'),
    (old_detail_check, new_detail_check, 'content hint guard'),
    (old_peer_section, new_peer_section, 'peer audio wiring'),
]:
    if source.count(old) != 1:
        raise SystemExit(f'v0423 source: {label} source block expected once, found {source.count(old)}')
    source = source.replace(old, new, 1)

exec(compile(source, str(source_path), 'exec'), {'Path': Path, 're': re, '__name__': '__main__'})
