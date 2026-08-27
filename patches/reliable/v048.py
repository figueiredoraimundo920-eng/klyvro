from pathlib import Path

ROOT = Path('.')

def replace_once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

# v0.4.8 metadata.
replace_once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.7";', 'const KLYVRO_BUILD = "0.4.8";')
replace_once('package.json', '"version": "0.4.7"', '"version": "0.4.8"')

# Five real profile slots + synchronized avatar data.
replace_once(
    'app/nexora-app.tsx',
    'type Member = { slot?: number; name: string; game: string; avatar: string; color: string; status: "online" | "away" | "offline"; bot?: boolean };',
    'type Member = { slot?: number; name: string; game: string; avatar: string; image?: string | null; color: string; status: "online" | "away" | "offline"; bot?: boolean };'
)
replace_once(
    'app/nexora-app.tsx',
    'type KlyvroProfileRow = { slot: number; display_name: string; avatar_color: string; claimed: boolean };',
    'type KlyvroProfileRow = { slot: number; display_name: string; avatar_color: string; avatar_data: string | null; claimed: boolean };'
)
replace_once(
    'app/nexora-app.tsx',
    '''const COUNTER_START = 1800;
const KLYVRO_BUILD = "0.4.8";''',
    '''const COUNTER_START = 1800;
const PROFILE_COLORS = ["#ff304f", "#63d6ff", "#f58bd8", "#a9ff68", "#ffb15c"] as const;
const KLYVRO_BUILD = "0.4.8";'''
)
replace_once(
    'app/nexora-app.tsx',
    '''  const [profileRows, setProfileRows] = useState<KlyvroProfileRow[]>([
    { slot: 1, display_name: "Jogador 1", avatar_color: "#ff304f", claimed: false },
    { slot: 2, display_name: "Jogador 2", avatar_color: "#63d6ff", claimed: false },
    { slot: 3, display_name: "Jogador 3", avatar_color: "#f58bd8", claimed: false },
  ]);''',
    '''  const [profileRows, setProfileRows] = useState<KlyvroProfileRow[]>([
    { slot: 1, display_name: "Jogador 1", avatar_color: "#ff304f", avatar_data: null, claimed: false },
    { slot: 2, display_name: "Jogador 2", avatar_color: "#63d6ff", avatar_data: null, claimed: false },
    { slot: 3, display_name: "Jogador 3", avatar_color: "#f58bd8", avatar_data: null, claimed: false },
    { slot: 4, display_name: "Souzza", avatar_color: "#a9ff68", avatar_data: null, claimed: false },
    { slot: 5, display_name: "randola", avatar_color: "#ffb15c", avatar_data: null, claimed: false },
  ]);'''
)
replace_once(
    'app/nexora-app.tsx',
    '''  const [readChannels, setReadChannels] = useState<Record<string, boolean>>({});
  const composerRef = useRef<HTMLTextAreaElement>(null);''',
    '''  const [readChannels, setReadChannels] = useState<Record<string, boolean>>({});
  const [voiceSession, setVoiceSession] = useState<{ serverId: ServerId; channelId: string; roomName: string } | null>(null);
  const composerRef = useRef<HTMLTextAreaElement>(null);'''
)
replace_once(
    'app/nexora-app.tsx',
    '''  const activeServerRef = useRef<ServerId>(activeServer);
  const pendingProfileNameRef = useRef<string | null>(null);
  const seenServerMessageIdsRef = useRef<Set<string>>(new Set());''',
    '''  const activeServerRef = useRef<ServerId>(activeServer);
  const pendingProfileNameRef = useRef<string | null>(null);
  const pendingProfilePhotoRef = useRef<string | null | undefined>(undefined);
  const profileRowsRef = useRef<Record<number, KlyvroProfileRow>>({});
  const seenServerMessageIdsRef = useRef<Set<string>>(new Set());'''
)
replace_once(
    'app/nexora-app.tsx',
    '''    avatar: (item.display_name[0] || "J").toUpperCase(),
    color: item.avatar_color,''',
    '''    avatar: (item.display_name[0] || "J").toUpperCase(),
    image: item.avatar_data,
    color: item.avatar_color,'''
)
replace_once(
    'app/nexora-app.tsx',
    '''function MemberRow({ member, onOpen }: { member: Member; onOpen: () => void }) {
  return <button type="button" className={`member-row ${member.status !== "online" ? "offline" : ""}`} data-member-trigger onClick={onOpen}><Avatar label={member.avatar} color={member.color} small status={member.status} /><span><strong>{member.name}{member.bot && <b className="bot-tag">BOT</b>}</strong><small>{member.game}</small></span></button>;
}''',
    '''function MemberRow({ member, onOpen }: { member: Member; onOpen: () => void }) {
  return <button type="button" className={`member-row ${member.status !== "online" ? "offline" : ""}`} data-member-trigger onClick={onOpen}><Avatar label={member.avatar} image={member.image} color={member.color} small status={member.status} /><span><strong>{member.name}{member.bot && <b className="bot-tag">BOT</b>}</strong><small>{member.game}</small></span></button>;
}'''
)

# Preserve the voice component while navigating around text/LFG screens.
replace_once(
    'app/nexora-app.tsx',
    '''  useEffect(() => { selectedRef.current = selected; }, [selected]);
  useEffect(() => { activeServerRef.current = activeServer; }, [activeServer]);''',
    '''  useEffect(() => { selectedRef.current = selected; }, [selected]);
  useEffect(() => { activeServerRef.current = activeServer; }, [activeServer]);
  useEffect(() => {
    const selectedChannel = servers[activeServer].channels.find((item) => item.id === selected);
    if (selectedChannel?.type !== "voice") return;
    setVoiceSession((current) => {
      if (current?.serverId === activeServer && current.channelId === selected) return current;
      return { serverId: activeServer, channelId: selected, roomName: selectedChannel.label };
    });
  }, [activeServer, selected]);'''
)

# Local cache load can retry both display name and a previously chosen photo.
replace_once(
    'app/nexora-app.tsx',
    '''      const storedName = storedProfile.name.trim().slice(0, 24);
      if (storedName && storedName !== DEFAULT_PROFILE.name) pendingProfileNameRef.current = storedName;''',
    '''      const storedName = storedProfile.name.trim().slice(0, 24);
      if (storedName && storedName !== DEFAULT_PROFILE.name) pendingProfileNameRef.current = storedName;
      if (typeof storedProfile.photo === "string" && storedProfile.photo.startsWith("data:image/webp")) pendingProfilePhotoRef.current = storedProfile.photo;'''
)

# When there is no pending local edit, adopt server name/photo for this slot.
replace_once(
    'app/nexora-app.tsx',
    '''  useEffect(() => {
    if (!profileSlot || pendingProfileNameRef.current) return;
    const serverProfile = profileRows.find((row) => row.slot === profileSlot);
    if (!serverProfile || serverProfile.display_name === profile.name) return;
    const next = { ...profile, name: serverProfile.display_name };
    setProfile(next);
    writeLocal(STORAGE_KEYS.profile, next);
  }, [profile.name, profile.photo, profileRows, profileSlot]);''',
    '''  useEffect(() => {
    if (!profileSlot || pendingProfileNameRef.current || pendingProfilePhotoRef.current !== undefined) return;
    const serverProfile = profileRows.find((row) => row.slot === profileSlot);
    if (!serverProfile) return;
    const serverPhoto = serverProfile.avatar_data ?? null;
    if (serverProfile.display_name === profile.name && serverPhoto === profile.photo) return;
    const next = { ...profile, name: serverProfile.display_name, photo: serverPhoto };
    setProfile(next);
    writeLocal(STORAGE_KEYS.profile, next);
  }, [profile.name, profile.photo, profileRows, profileSlot]);'''
)
replace_once(
    'app/nexora-app.tsx',
    '''        avatar: (row.display_name[0] || "J").toUpperCase(),
        color: row.avatar_color,''',
    '''        avatar: (row.display_name[0] || "J").toUpperCase(),
        image: row.avatar_data,
        color: row.avatar_color,'''
)
replace_once(
    'app/nexora-app.tsx',
    '''      return next.name === current.name && next.avatar === current.avatar && next.color === current.color && next.status === current.status ? current : next;''',
    '''      return next.name === current.name && next.avatar === current.avatar && next.image === current.image && next.color === current.color && next.status === current.status ? current : next;'''
)

# Message history receives the author's current profile photo/color instead of dropping it after server sync.
replace_once(
    'app/nexora-app.tsx',
    '''    const rowToMessage = (row: { id: string; author_name: string; author_slot: number; body: string; channel_id: string; created_at: string }): Message => {
      const color = ["#ff304f", "#63d6ff", "#f58bd8"][Math.max(0, Math.min(2, Number(row.author_slot) - 1))] ?? "#ff304f";
      return { id: String(row.id), author: String(row.author_name), avatar: (String(row.author_name)[0] || "J").toUpperCase(), color, time: formatMessageTime(row.created_at), text: String(row.body), channelId: String(row.channel_id) };
    };''',
    '''    const rowToMessage = (row: { id: string; author_name: string; author_slot: number; body: string; channel_id: string; created_at: string }): Message => {
      const authorSlot = Number(row.author_slot);
      const authorProfile = profileRowsRef.current[authorSlot];
      const color = authorProfile?.avatar_color ?? PROFILE_COLORS[Math.max(0, Math.min(4, authorSlot - 1))] ?? "#ff304f";
      return { id: String(row.id), author: String(row.author_name), avatar: (String(row.author_name)[0] || "J").toUpperCase(), avatarUrl: authorProfile?.avatar_data ?? null, color, time: formatMessageTime(row.created_at), text: String(row.body), channelId: String(row.channel_id) };
    };'''
)
replace_once(
    'app/nexora-app.tsx',
    '''        supabase.from("klyvro_profiles").select("slot,display_name,avatar_color,claimed").order("slot"),''',
    '''        supabase.from("klyvro_profiles").select("slot,display_name,avatar_color,avatar_data,claimed").order("slot"),'''
)
replace_once(
    'app/nexora-app.tsx',
    '''      if (profiles) setProfileRows(profiles as KlyvroProfileRow[]);
      const slots = Array.from(new Set(((presence ?? []) as KlyvroPresenceRow[]).map((item) => Number(item.slot)).filter((slot) => slot >= 1 && slot <= 3)));''',
    '''      if (profiles) {
        const typedProfiles = profiles as KlyvroProfileRow[];
        profileRowsRef.current = Object.fromEntries(typedProfiles.map((row) => [Number(row.slot), row]));
        setProfileRows(typedProfiles);
      }
      const slots = Array.from(new Set(((presence ?? []) as KlyvroPresenceRow[]).map((item) => Number(item.slot)).filter((slot) => slot >= 1 && slot <= 5)));'''
)

# Retry server-backed name/photo updates from the heartbeat.
replace_once(
    'app/nexora-app.tsx',
    '''      const pendingName = pendingProfileNameRef.current;
      if (pendingName) {
        const { data: updatedData, error: nameError } = await supabase.rpc("klyvro_update_profile", { p_token: token, p_display_name: pendingName });
        if (!nameError) {
          const updated = Array.isArray(updatedData) ? updatedData[0] : null;
          const syncedName = String(updated?.display_name || pendingName).slice(0, 24);
          if (pendingProfileNameRef.current === pendingName) pendingProfileNameRef.current = null;
          if (!cancelled) {
            setProfile((current) => ({ ...current, name: syncedName }));
            setProfileRows((rows) => rows.map((row) => Number(row.slot) === Number(updated?.slot) ? { ...row, display_name: syncedName } : row));
          }
        }
      }''',
    '''      const pendingName = pendingProfileNameRef.current;
      const pendingPhoto = pendingProfilePhotoRef.current;
      if (pendingName || pendingPhoto !== undefined) {
        const { data: updatedData, error: profileError } = await supabase.rpc("klyvro_update_profile_v2", {
          p_token: token,
          p_display_name: pendingName,
          p_avatar_data: pendingPhoto ?? null,
          p_clear_avatar: pendingPhoto === null,
        });
        if (!profileError) {
          const updated = Array.isArray(updatedData) ? updatedData[0] : null;
          const syncedName = String(updated?.display_name || pendingName || "Jogador").slice(0, 24);
          const syncedPhoto = typeof updated?.avatar_data === "string" ? updated.avatar_data : null;
          if (pendingProfileNameRef.current === pendingName) pendingProfileNameRef.current = null;
          if (pendingProfilePhotoRef.current === pendingPhoto) pendingProfilePhotoRef.current = undefined;
          if (!cancelled && updated) {
            setProfile((current) => {
              const next = { ...current, name: syncedName, photo: syncedPhoto };
              writeLocal(STORAGE_KEYS.profile, next);
              return next;
            });
            setProfileRows((rows) => {
              const nextRows = rows.map((row) => Number(row.slot) === Number(updated.slot)
                ? { ...row, display_name: syncedName, avatar_color: String(updated.avatar_color || row.avatar_color), avatar_data: syncedPhoto }
                : row);
              profileRowsRef.current = Object.fromEntries(nextRows.map((row) => [Number(row.slot), row]));
              return nextRows;
            });
          }
        }
      }'''
)

replace_once(
    'app/nexora-app.tsx',
    'setToast("Os 3 perfis estão ativos. O Klyvro vai tentar entrar novamente sozinho.");',
    'setToast("Os 5 perfis estão ativos. O Klyvro vai tentar entrar novamente sozinho.");'
)

# Keep avatar on the optimistic -> server message replacement.
replace_once(
    'app/nexora-app.tsx',
    '''        const row = raw as { id: string; author_name: string; author_slot: number; body: string; channel_id: string; created_at: string };
        const synced: Message = { id: String(row.id), author: String(row.author_name), avatar: (String(row.author_name)[0] || "J").toUpperCase(), color: ["#ff304f", "#63d6ff", "#f58bd8"][Math.max(0, Math.min(2, Number(row.author_slot) - 1))] ?? "#ff304f", time: formatMessageTime(row.created_at), text: String(row.body), channelId: String(row.channel_id), reply: replyTarget };''',
    '''        const row = raw as { id: string; author_name: string; author_slot: number; body: string; channel_id: string; created_at: string };
        const authorSlot = Number(row.author_slot);
        const authorProfile = profileRowsRef.current[authorSlot];
        const synced: Message = { id: String(row.id), author: String(row.author_name), avatar: (String(row.author_name)[0] || "J").toUpperCase(), avatarUrl: authorSlot === profileSlot ? profile.photo : authorProfile?.avatar_data ?? null, color: authorProfile?.avatar_color ?? PROFILE_COLORS[Math.max(0, Math.min(4, authorSlot - 1))] ?? "#ff304f", time: formatMessageTime(row.created_at), text: String(row.body), channelId: String(row.channel_id), reply: replyTarget };'''
)

# New profile RPC persists both name and photo and keeps retry state if the network is unavailable.
replace_once(
    'app/nexora-app.tsx',
    '''  const saveProfile = (next: UserProfile) => {
    const desiredName = next.name.trim().slice(0, 24) || "Jogador";
    const normalized = { ...next, name: desiredName };
    setProfile(normalized);
    writeLocal(STORAGE_KEYS.profile, normalized);
    pendingProfileNameRef.current = desiredName;

    const token = deviceTokenRef.current;
    if (!token || !profileSlot) {
      setToast("Nome salvo; vou sincronizar assim que sua sessão conectar.");
      return;
    }

    void supabase.rpc("klyvro_update_profile", { p_token: token, p_display_name: desiredName }).then(({ data, error }) => {
      if (error) {
        setToast("Nome salvo neste dispositivo; tentando sincronizar novamente.");
        return;
      }
      const updated = Array.isArray(data) ? data[0] : null;
      const syncedName = String(updated?.display_name || desiredName).slice(0, 24);
      if (pendingProfileNameRef.current === desiredName) pendingProfileNameRef.current = null;
      setProfile((current) => ({ ...current, name: syncedName }));
      setProfileRows((rows) => rows.map((row) => row.slot === profileSlot ? { ...row, display_name: syncedName } : row));
      setToast("Nome sincronizado para todos");
    });
  };''',
    '''  const saveProfile = (next: UserProfile) => {
    const desiredName = next.name.trim().slice(0, 24) || "Jogador";
    const normalized = { ...next, name: desiredName };
    setProfile(normalized);
    writeLocal(STORAGE_KEYS.profile, normalized);
    pendingProfileNameRef.current = desiredName;
    pendingProfilePhotoRef.current = normalized.photo;

    const token = deviceTokenRef.current;
    if (!token || !profileSlot) {
      setToast("Perfil salvo; vou sincronizar assim que sua sessão conectar.");
      return;
    }

    void supabase.rpc("klyvro_update_profile_v2", {
      p_token: token,
      p_display_name: desiredName,
      p_avatar_data: normalized.photo,
      p_clear_avatar: normalized.photo === null,
    }).then(({ data, error }) => {
      if (error) {
        setToast("Perfil salvo neste dispositivo; tentando sincronizar novamente.");
        return;
      }
      const updated = Array.isArray(data) ? data[0] : null;
      if (!updated) return;
      const syncedName = String(updated.display_name || desiredName).slice(0, 24);
      const syncedPhoto = typeof updated.avatar_data === "string" ? updated.avatar_data : null;
      if (pendingProfileNameRef.current === desiredName) pendingProfileNameRef.current = null;
      if (pendingProfilePhotoRef.current === normalized.photo) pendingProfilePhotoRef.current = undefined;
      const syncedProfile = { ...normalized, name: syncedName, photo: syncedPhoto };
      setProfile(syncedProfile);
      writeLocal(STORAGE_KEYS.profile, syncedProfile);
      setProfileRows((rows) => {
        const nextRows = rows.map((row) => row.slot === profileSlot
          ? { ...row, display_name: syncedName, avatar_color: String(updated.avatar_color || row.avatar_color), avatar_data: syncedPhoto }
          : row);
        profileRowsRef.current = Object.fromEntries(nextRows.map((row) => [Number(row.slot), row]));
        return nextRows;
      });
      setToast("Perfil sincronizado para todos");
    });
  };'''
)

# 5-profile UI counters.
p = ROOT / 'app/nexora-app.tsx'
text = p.read_text(encoding='utf-8')
for old, new in [
    ('{onlineSlots.length}/3 ONLINE', '{onlineSlots.length}/5 ONLINE'),
    ('`${onlineSlots.length}/3 online`', '`${onlineSlots.length}/5 online`'),
]:
    if old not in text:
        raise SystemExit(f'app/nexora-app.tsx: missing counter target {old!r}')
    text = text.replace(old, new)
p.write_text(text, encoding='utf-8')

# Voice room is no longer tied to the selected panel; hidden calls render a compact dock.
replace_once(
    'app/nexora-app.tsx',
    '''          </> : channel.type === "voice" ? <VoiceRoom roomName={channel.label} roomId={`${activeServer}:${channel.id}`} profile={profile} audio={audio} onAudioChange={saveAudio} onToast={setToast} /> : <LfgBoard profile={profile} onToast={setToast} />}
        </div>''',
    '''          </> : channel.type === "voice" ? null : <LfgBoard profile={profile} onToast={setToast} />}
          {voiceSession && <VoiceRoom
            key={`${voiceSession.serverId}:${voiceSession.channelId}`}
            roomName={voiceSession.roomName}
            roomId={`${voiceSession.serverId}:${voiceSession.channelId}`}
            visible={activeServer === voiceSession.serverId && selected === voiceSession.channelId && channel.type === "voice"}
            profile={profile}
            audio={audio}
            onAudioChange={saveAudio}
            onToast={setToast}
          />}
        </div>'''
)
replace_once(
    'app/nexora-app.tsx',
    '''{selectedMember && <section className="member-mini-profile floating-panel" data-floating-root aria-label={`Perfil de ${selectedMember.name}`}><header><Avatar label={selectedMember.avatar} color={selectedMember.color} status={selectedMember.status} />''',
    '''{selectedMember && <section className="member-mini-profile floating-panel" data-floating-root aria-label={`Perfil de ${selectedMember.name}`}><header><Avatar label={selectedMember.avatar} image={selectedMember.image} color={selectedMember.color} status={selectedMember.status} />'''
)

# Photo changes are committed immediately; closing Settings no longer discards them.
replace_once(
    'app/settings-panel.tsx',
    '''    try { setPhoto(await resizeProfilePhoto(file)); setPhotoMessage("Foto pronta. Salve o perfil para confirmar."); }
    catch { setPhotoMessage("O arquivo não contém uma imagem válida."); onToast("Não foi possível usar essa imagem."); }''',
    '''    try {
      const optimized = await resizeProfilePhoto(file);
      setPhoto(optimized);
      setPhotoMessage("Foto pronta e sincronizando.");
      onProfileChange({ name: profile.name, photo: optimized });
      onToast("Foto de perfil salva");
    } catch {
      setPhotoMessage("O arquivo não contém uma imagem válida.");
      onToast("Não foi possível usar essa imagem.");
    }'''
)
replace_once(
    'app/settings-panel.tsx',
    '''{photoMessage && <small className={photoMessage.includes("pronta") ? "field-success" : "field-error"} role="status">{photoMessage}</small>}''',
    '''{photoMessage && <small className={photoMessage.includes("inválid") || photoMessage.includes("máximo") || photoMessage.includes("não ") ? "field-error" : "field-success"} role="status">{photoMessage}</small>}'''
)
replace_once(
    'app/settings-panel.tsx',
    '''{photo && <button type="button" className="ghost-button" onClick={() => { setPhoto(null); setPhotoMessage("Foto removida. Salve o perfil para confirmar."); }}>Remover</button>}''',
    '''{photo && <button type="button" className="ghost-button" onClick={() => { setPhoto(null); setPhotoMessage("Foto removida e sincronizando."); onProfileChange({ name: profile.name, photo: null }); onToast("Foto de perfil removida"); }}>Remover</button>}'''
)
replace_once(
    'app/settings-panel.tsx',
    '''<div className="privacy-note"><Icon name="shield" size={16} /><p>Seu nome é sincronizado no Klyvro. A foto continua salva apenas neste dispositivo e não é enviada ao servidor.</p></div>''',
    '''<div className="privacy-note"><Icon name="shield" size={16} /><p>Seu nome e sua foto de perfil são sincronizados no Klyvro para aparecerem nos membros, mensagens e calls.</p></div>'''
)

# v0.4.8 UI for persistent-call dock + fullscreen controls.
css = ROOT / 'app/features.css'
text = css.read_text(encoding='utf-8')
marker = '/* Klyvro v0.4.8 persistent calls/fullscreen */'
if marker not in text:
    text += r'''

/* Klyvro v0.4.8 persistent calls/fullscreen */
.chat-panel{position:relative}.voice-call-dock{position:absolute;z-index:18;left:14px;right:14px;bottom:14px;min-height:64px;padding:10px 12px;border:1px solid rgba(169,255,104,.22);border-radius:14px;background:rgba(12,16,22,.96);box-shadow:0 18px 50px rgba(0,0,0,.34);backdrop-filter:blur(14px);display:flex;align-items:center;justify-content:space-between;gap:12px}.voice-call-dock>div:first-child{min-width:0;display:flex;flex-direction:column;gap:3px}.voice-call-dock strong{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.voice-call-dock small{color:var(--muted);font-size:11px}.voice-call-dock .voice-call-dock-actions{display:flex;gap:7px}.voice-call-dock button{height:38px;min-width:38px;border-radius:10px}.screen-label{display:flex;align-items:center;justify-content:space-between;gap:10px}.screen-label-actions{display:flex;align-items:center;gap:7px}.screen-fullscreen-button{height:30px;padding:0 10px;border:1px solid rgba(255,255,255,.1);border-radius:8px;background:rgba(255,255,255,.06);font-size:11px;font-weight:800}.screen-card:fullscreen{width:100vw;height:100vh;max-width:none;max-height:none;border:0;border-radius:0;background:#05070a}.screen-card:fullscreen video{width:100%;height:calc(100vh - 48px);object-fit:contain;background:#000}.screen-card:-webkit-full-screen{width:100vw;height:100vh;border-radius:0;background:#05070a}.screen-card:-webkit-full-screen video{width:100%;height:calc(100vh - 48px);object-fit:contain;background:#000}
@media(max-width:650px){.voice-call-dock{left:8px;right:8px;bottom:8px}.voice-call-dock small{display:none}.screen-fullscreen-button{padding:0 8px}}
'''
    css.write_text(text, encoding='utf-8')

print('Klyvro v0.4.8 five profiles/persistent call/fullscreen/avatar patch applied')
