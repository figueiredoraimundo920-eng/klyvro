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

# A room can be asked to join automatically only after the user explicitly
# presses the preview's Enter button. Selecting a channel never triggers this.
once(
    'app/voice-room.tsx',
    '''  visible?: boolean;
  profile: UserProfile;''',
    '''  visible?: boolean;
  autoJoin?: boolean;
  profile: UserProfile;'''
)
once(
    'app/voice-room.tsx',
    '''export default function VoiceRoom({ roomName, roomId, visible = true, profile, audio, onAudioChange, onToast }: Props) {''',
    '''export default function VoiceRoom({ roomName, roomId, visible = true, autoJoin = false, profile, audio, onAudioChange, onToast }: Props) {'''
)
once(
    'app/voice-room.tsx',
    '''  const [joined, setJoined] = useState(false);
  const [muted, setMuted] = useState(false);''',
    '''  const [joined, setJoined] = useState(false);
  const autoJoinStartedRef = useRef(false);
  const [muted, setMuted] = useState(false);'''
)
once(
    'app/voice-room.tsx',
    '''  };

  const leave = () => {''',
    '''  };

  useEffect(() => {
    if (!autoJoin || joined || autoJoinStartedRef.current) return;
    autoJoinStartedRef.current = true;
    void join();
  }, [autoJoin, joined]);

  const leave = () => {'''
)

# Track real voice presence in the shell and remember the room that received an
# explicit Enter click so only that newly-mounted room auto-joins once.
once(
    'app/nexora-app.tsx',
    '''  const [voiceSession, setVoiceSession] = useState<{ serverId: ServerId; channelId: string; roomName: string } | null>(null);
  const composerRef = useRef<HTMLTextAreaElement>(null);''',
    '''  const [voiceSession, setVoiceSession] = useState<{ serverId: ServerId; channelId: string; roomName: string } | null>(null);
  const [voiceAutoJoinRoom, setVoiceAutoJoinRoom] = useState<string | null>(null);
  const [voicePresence, setVoicePresence] = useState<KlyvroPresenceRow[]>([]);
  const composerRef = useRef<HTMLTextAreaElement>(null);'''
)

# Remove v0.4.8's auto-switch effect. Clicking another voice channel is now
# navigation only; the current WebRTC room stays mounted until Enter is pressed.
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

# Store the current presence snapshot. voice_seen is checked again while
# rendering so stale/crashed room occupants disappear quickly.
once(
    'app/nexora-app.tsx',
    '''      const slots = Array.from(new Set(((presence ?? []) as KlyvroPresenceRow[]).map((item) => Number(item.slot)).filter((slot) => slot >= 1 && slot <= 5)));
      setOnlineSlots(slots);''',
    '''      const livePresence = (presence ?? []) as KlyvroPresenceRow[];
      const slots = Array.from(new Set(livePresence.map((item) => Number(item.slot)).filter((slot) => slot >= 1 && slot <= 5)));
      setOnlineSlots(slots);
      setVoicePresence(livePresence);'''
)

# Resolve the actual occupants of a voice room from voice_room + voice_seen.
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
# with the real occupants below every voice channel.
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

# When a different voice room is selected, show a lightweight preview instead
# of replacing/unmounting the active VoiceRoom. Only this button changes rooms.
once(
    'app/nexora-app.tsx',
    '''          </> : channel.type === "voice" ? null : <LfgBoard profile={profile} onToast={setToast} />}''',
    '''          </> : channel.type === "voice" ? (
            voiceSession?.serverId === activeServer && voiceSession.channelId === channel.id ? null : <div className="voice-channel-preview">
              <div className="voice-channel-preview-icon"><Icon name="volume" size={24} /></div>
              <div className="voice-channel-preview-copy">
                <span className="eyebrow"><Icon name="radio" size={13} /> CANAL DE VOZ</span>
                <h1>{channel.label}</h1>
                <p>{voiceMembersFor(channel.id).length > 0 ? `${voiceMembersFor(channel.id).length} ${voiceMembersFor(channel.id).length === 1 ? "pessoa está" : "pessoas estão"} na call agora.` : "Ninguém está na call agora."} Você só troca de sala quando clicar em Entrar.</p>
                {voiceMembersFor(channel.id).length > 0 ? <div className="voice-preview-members">{voiceMembersFor(channel.id).slice(0, 5).map((member) => <span key={member.slot}><Avatar label={(member.display_name[0] || "J").toUpperCase()} image={member.avatar_data} color={member.avatar_color} small /><b>{member.display_name}</b></span>)}</div> : null}
              </div>
              <button className="voice-preview-join" type="button" onClick={() => {
                const nextRoom = { serverId: activeServer, channelId: channel.id, roomName: channel.label };
                const nextRoomId = `${activeServer}:${channel.id}`;
                setVoiceAutoJoinRoom(nextRoomId);
                setVoiceSession(nextRoom);
              }}><Icon name="radio" size={16} /> Entrar na call</button>
            </div>
          ) : <LfgBoard profile={profile} onToast={setToast} />}'''
)

# The active VoiceRoom remains a single persistent component. autoJoin is true
# only for the room selected through the explicit preview button.
once(
    'app/nexora-app.tsx',
    '''            visible={activeServer === voiceSession.serverId && selected === voiceSession.channelId && channel.type === "voice"}
            profile={profile}''',
    '''            visible={activeServer === voiceSession.serverId && selected === voiceSession.channelId && channel.type === "voice"}
            autoJoin={voiceAutoJoinRoom === `${voiceSession.serverId}:${voiceSession.channelId}`}
            profile={profile}'''
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
.voice-channel-preview{min-height:320px;margin:18px;padding:28px;border:1px solid rgba(255,255,255,.08);border-radius:18px;background:rgba(12,16,22,.72);display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:18px}
.voice-channel-preview-icon{width:54px;height:54px;border-radius:16px;display:grid;place-items:center;background:rgba(99,214,255,.09);border:1px solid rgba(99,214,255,.16)}
.voice-channel-preview-copy{min-width:0}.voice-channel-preview-copy h1{margin:6px 0 8px;font-size:26px}.voice-channel-preview-copy p{margin:0;max-width:640px;color:var(--muted);line-height:1.55}
.voice-preview-members{display:flex;flex-wrap:wrap;gap:7px;margin-top:14px}.voice-preview-members span{display:flex;align-items:center;gap:6px;padding:5px 8px 5px 5px;border:1px solid rgba(255,255,255,.07);border-radius:999px;background:rgba(255,255,255,.035);font-size:11px}.voice-preview-members b{max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.voice-preview-join{height:42px;padding:0 15px;border-radius:11px;display:inline-flex;align-items:center;justify-content:center;gap:7px;font-weight:800;white-space:nowrap}
@media(max-width:760px){.voice-channel-preview{grid-template-columns:auto minmax(0,1fr);padding:20px}.voice-preview-join{grid-column:1/-1;width:100%}}
@media(max-width:650px){.voice-call-dock{left:8px;right:8px;bottom:78px;width:auto}.voice-live-members{padding-left:30px}.voice-channel-preview{margin:10px;min-height:260px}}
'''
    css.write_text(css_text, encoding='utf-8')

print('Klyvro v0.4.19 explicit voice switching/chat composer/live call presence patch applied')
