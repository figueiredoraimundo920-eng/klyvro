from pathlib import Path
import re

ROOT = Path('.')


def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.19 expected one target, found {count}: {old[:220]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


def regex_once(path: str, pattern: str, replacement: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    next_text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.19 regex expected one target, found {count}: {pattern[:220]!r}')
    p.write_text(next_text, encoding='utf-8')


# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.18";', 'const KLYVRO_BUILD = "0.4.19";')
once('package.json', '"version": "0.4.18"', '"version": "0.4.19"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.18', 'VOZ • CORE v0.4.19')

# Parent only promotes a room to the active call after the user presses Enter.
# Merely selecting another voice channel must never tear down the current call.
once(
    'app/voice-room.tsx',
    '''  visible?: boolean;
  profile: UserProfile;''',
    '''  visible?: boolean;
  onJoinedChange?: (joined: boolean) => void;
  profile: UserProfile;'''
)
once(
    'app/voice-room.tsx',
    '''export default function VoiceRoom({ roomName, roomId, visible = true, profile, audio, onAudioChange, onToast }: Props) {''',
    '''export default function VoiceRoom({ roomName, roomId, visible = true, onJoinedChange, profile, audio, onAudioChange, onToast }: Props) {'''
)

# Pressing Enter is the explicit room-switch action. Promote before the new
# heartbeat so the old room unmounts/leaves first and cannot clear the new room.
once(
    'app/voice-room.tsx',
    '''  const join = async () => {
    if (joined) return;
    setJoined(true);''',
    '''  const join = async () => {
    if (joined) return;
    onJoinedChange?.(true);
    setJoined(true);'''
)

# If joining fails, release the parent session again. A normal Leave does the
# same. This keeps the selected room visible as a preview without a fake call.
once(
    'app/voice-room.tsx',
    '''      cleanup();
      setJoined(false);
      setState("error");''',
    '''      cleanup();
      setJoined(false);
      onJoinedChange?.(false);
      setState("error");'''
)
once(
    'app/voice-room.tsx',
    '''    cleanup();
    setJoined(false);
    setPeers({});''',
    '''    cleanup();
    setJoined(false);
    onJoinedChange?.(false);
    setPeers({});'''
)

# Track the live presence rows in the shell so the channel list can show the
# actual members of each call, not generic online users.
once(
    'app/nexora-app.tsx',
    '''  const [voiceSession, setVoiceSession] = useState<{ serverId: ServerId; channelId: string; roomName: string } | null>(null);
  const composerRef = useRef<HTMLTextAreaElement>(null);''',
    '''  const [voiceSession, setVoiceSession] = useState<{ serverId: ServerId; channelId: string; roomName: string } | null>(null);
  const [voicePresence, setVoicePresence] = useState<KlyvroPresenceRow[]>([]);
  const composerRef = useRef<HTMLTextAreaElement>(null);'''
)

# Remove v0.4.8's auto-switch effect. Selecting a voice channel now only opens
# that room's preview. The current call survives until Enter is pressed.
once(
    'app/nexora-app.tsx',
    '''  useEffect(() => { selectedRef.current = selected; }, [selected]);
  useEffect(() => { activeServerRef.current = activeServer; }, [activeServer]);
  useEffect(() => {
    const selectedChannel = servers[activeServer].channels.find((item) => item.id === selected);
    if (selectedChannel?.type !== "voice") return;
    setVoiceSession((current) => {
      if (current?.serverId === activeServer && current.channelId === selected) return current;
      return { serverId: activeServer, channelId: selected, roomName: selectedChannel.label };
    });
  }, [activeServer, selected]);''',
    '''  useEffect(() => { selectedRef.current = selected; }, [selected]);
  useEffect(() => { activeServerRef.current = activeServer; }, [activeServer]);'''
)

# Keep a current snapshot of presence rows. voice_seen is checked again in the
# renderer so stale/crashed voice sessions disappear from the sidebar quickly.
once(
    'app/nexora-app.tsx',
    '''      const slots = Array.from(new Set(((presence ?? []) as KlyvroPresenceRow[]).map((item) => Number(item.slot)).filter((slot) => slot >= 1 && slot <= 5)));
      setOnlineSlots(slots);''',
    '''      const livePresence = (presence ?? []) as KlyvroPresenceRow[];
      const slots = Array.from(new Set(livePresence.map((item) => Number(item.slot)).filter((slot) => slot >= 1 && slot <= 5)));
      setOnlineSlots(slots);
      setVoicePresence(livePresence);'''
)

# Derive real room occupancy from voice_room + voice_seen and keep the selected
# room as a preview alongside the active room when they differ.
once(
    'app/nexora-app.tsx',
    '''  const channel = server.channels.find((item) => item.id === selected) ?? server.channels[0];''',
    '''  const channel = server.channels.find((item) => item.id === selected) ?? server.channels[0];
  const selectedVoiceRoom: { serverId: ServerId; channelId: string; roomName: string } | null = channel.type === "voice"
    ? { serverId: activeServer, channelId: channel.id, roomName: channel.label }
    : null;
  const voiceRoomPanels = voiceSession
    ? selectedVoiceRoom && (voiceSession.serverId !== selectedVoiceRoom.serverId || voiceSession.channelId !== selectedVoiceRoom.channelId)
      ? [voiceSession, selectedVoiceRoom]
      : [voiceSession]
    : selectedVoiceRoom ? [selectedVoiceRoom] : [];'''
)
once(
    'app/nexora-app.tsx',
    '''  const visibleMembers = realtimeMembers.filter((member) => `${member.name} ${member.game}`.toLowerCase().includes(normalizedMemberQuery));''',
    '''  const voiceMembersFor = (channelId: string) => {
    const roomId = `${activeServer}:${channelId}`;
    const voiceCutoff = Date.now() - 15_000;
    const slots = new Set(voicePresence
      .filter((entry) => entry.voice_room === roomId && Boolean(entry.voice_seen) && Date.parse(String(entry.voice_seen)) >= voiceCutoff)
      .map((entry) => Number(entry.slot)));
    return profileRows.filter((row) => slots.has(Number(row.slot)));
  };
  const visibleMembers = realtimeMembers.filter((member) => `${member.name} ${member.game}`.toLowerCase().includes(normalizedMemberQuery));'''
)

# Replace the old fake voice-mini (generic online users in only the first room)
# with the actual live occupants under every voice channel.
regex_once(
    'app/nexora-app.tsx',
    r'''        <section className="channel-group"><h2><span>CANAIS DE VOZ</span><Icon name="plus" size=\{15\} /></h2>.*?</section>''',
    '''        <section className="channel-group"><h2><span>CANAIS DE VOZ</span><Icon name="plus" size={15} /></h2>{server.channels.filter((item) => item.type === "voice").map((item) => {
          const callMembers = voiceMembersFor(item.id);
          return <div key={item.id} className="voice-channel-entry">
            <ChannelRow channel={item} active={selected === item.id} unread={readChannels[item.id] === false} onClick={() => selectChannel(item.id)} />
            {callMembers.length > 0 ? <div className="voice-mini voice-live-members" aria-label={`${callMembers.length} ${callMembers.length === 1 ? "pessoa" : "pessoas"} na call ${item.label}`}>
              {callMembers.slice(0, 5).map((member) => <span key={member.slot} title={member.display_name}><Avatar label={(member.display_name[0] || "J").toUpperCase()} image={member.avatar_data} color={member.avatar_color} small /><b>{member.display_name}</b></span>)}
              {callMembers.length > 5 ? <em>+{callMembers.length - 5}</em> : null}
            </div> : null}
          </div>;
        })}</section>'''
)

# Render both the active room and (when different) the selected preview as a
# keyed list. React preserves the preview instance when it becomes active, so
# pressing Enter does not tear down the newly-created WebRTC session.
once(
    'app/nexora-app.tsx',
    '''          {voiceSession && <VoiceRoom
            key={`${voiceSession.serverId}:${voiceSession.channelId}`}
            roomName={voiceSession.roomName}
            roomId={`${voiceSession.serverId}:${voiceSession.channelId}`}
            visible={activeServer === voiceSession.serverId && selected === voiceSession.channelId && channel.type === "voice"}
            profile={profile}
            audio={audio}
            onAudioChange={saveAudio}
            onToast={setToast}
          />}''',
    '''          {voiceRoomPanels.map((room) => <VoiceRoom
            key={`${room.serverId}:${room.channelId}`}
            roomName={room.roomName}
            roomId={`${room.serverId}:${room.channelId}`}
            visible={activeServer === room.serverId && selected === room.channelId && channel.type === "voice"}
            onJoinedChange={(joined) => {
              if (joined) {
                setVoiceSession({ serverId: room.serverId, channelId: room.channelId, roomName: room.roomName });
                return;
              }
              setVoiceSession((current) => current?.serverId === room.serverId && current.channelId === room.channelId ? null : current);
            }}
            profile={profile}
            audio={audio}
            onAudioChange={saveAudio}
            onToast={setToast}
          />)}'''
)

# The compact call dock used to cover the full-width chat composer. Keep it
# above the composer, compact, and pointer-transparent except for its controls.
css = ROOT / 'app/globals.css'
css_text = css.read_text(encoding='utf-8')
marker = '/* Klyvro v0.4.19 voice navigation + live room presence */'
if marker not in css_text:
    css_text += r'''

/* Klyvro v0.4.19 voice navigation + live room presence */
.voice-call-dock{left:14px;right:auto;bottom:86px;width:min(390px,calc(100% - 28px));pointer-events:none}
.voice-call-dock .voice-call-dock-actions,.voice-call-dock button{pointer-events:auto}
.voice-channel-entry{min-width:0}
.voice-live-members{display:flex;flex-direction:column;align-items:stretch;gap:4px;padding:3px 8px 7px 34px}
.voice-live-members span{display:flex;align-items:center;gap:7px;min-width:0;color:var(--muted);font-size:11px;line-height:1.2}
.voice-live-members span b{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:650}
.voice-live-members .avatar{flex:0 0 auto}
.voice-live-members em{padding-left:30px;color:var(--muted);font-size:10px;font-style:normal;font-weight:800}
@media(max-width:650px){.voice-call-dock{left:8px;right:8px;bottom:78px;width:auto}.voice-live-members{padding-left:30px}}
'''
    css.write_text(css_text, encoding='utf-8')

print('Klyvro v0.4.19 voice navigation/chat composer/live call presence patch applied')
