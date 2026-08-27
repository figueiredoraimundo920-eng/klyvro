from pathlib import Path

ROOT = Path('.')

def replace_once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one target, found {count}: {old[:120]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

replace_once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.4";', 'const KLYVRO_BUILD = "0.4.5";')
replace_once(
    'app/nexora-app.tsx',
    'const mergeMessages = (items: Message[], incoming: Message) => items.some((item) => item.id === incoming.id) ? items : [...items, incoming].slice(-150);',
    '''const mergeMessages = (items: Message[], incoming: Message) => {
  const index = items.findIndex((item) => item.id === incoming.id);
  if (index < 0) return [...items, incoming].slice(-150);
  const updated = [...items];
  updated[index] = { ...updated[index], ...incoming };
  return updated.slice(-150);
};'''
)
replace_once(
    'app/nexora-app.tsx',
    '  const activeServerRef = useRef<ServerId>(activeServer);',
    '  const activeServerRef = useRef<ServerId>(activeServer);\n  const pendingProfileNameRef = useRef<string | null>(null);'
)
replace_once(
    'app/nexora-app.tsx',
    '''      setProfile({ ...DEFAULT_PROFILE, ...readLocal<UserProfile>(STORAGE_KEYS.profile, DEFAULT_PROFILE, "nexora-profile", isLocalRecord) });''',
    '''      const storedProfile = { ...DEFAULT_PROFILE, ...readLocal<UserProfile>(STORAGE_KEYS.profile, DEFAULT_PROFILE, "nexora-profile", isLocalRecord) };
      setProfile(storedProfile);
      const storedName = storedProfile.name.trim().slice(0, 24);
      if (storedName && storedName !== DEFAULT_PROFILE.name) pendingProfileNameRef.current = storedName;'''
)
replace_once(
    'app/nexora-app.tsx',
    '''    const heartbeat = async () => {
      const token = deviceTokenRef.current;
      if (!token) return;
      const { error } = await supabase.rpc("klyvro_heartbeat", { p_token: token, p_server_id: activeServerRef.current, p_channel_id: selectedRef.current });
      if (error) throw error;
      if (!cancelled) setNetworkState("online");
    };''',
    '''    const heartbeat = async () => {
      const token = deviceTokenRef.current;
      if (!token) return;
      const { error } = await supabase.rpc("klyvro_heartbeat", { p_token: token, p_server_id: activeServerRef.current, p_channel_id: selectedRef.current });
      if (error) throw error;

      const pendingName = pendingProfileNameRef.current;
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
      }

      if (!cancelled) setNetworkState("online");
    };'''
)
replace_once(
    'app/nexora-app.tsx',
    '''  const saveProfile = (next: UserProfile) => {
    setProfile(next); writeLocal(STORAGE_KEYS.profile, next);
    const token = deviceTokenRef.current;
    if (token && profileSlot) void supabase.rpc("klyvro_update_profile", { p_token: token, p_display_name: next.name.trim().slice(0, 24) || "Jogador" }).then(({ data, error }) => {
      if (error) { setToast("Não foi possível sincronizar o nome agora"); return; }
      const updated = Array.isArray(data) ? data[0] : null;
      if (updated) setProfileRows((rows) => rows.map((row) => row.slot === profileSlot ? { ...row, display_name: String(updated.display_name) } : row));
    });
  };''',
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
  };'''
)

replace_once('app/voice-room.tsx', 'VOZ • CORE v0.4.4', 'VOZ • CORE v0.4.5')
replace_once(
    'app/voice-room.tsx',
    '''      const refreshPeers = async () => {
        const cutoff = new Date(Date.now() - 12_000).toISOString();
        const { data, error } = await supabase.from("klyvro_presence").select("slot,voice_room,voice_seen").eq("voice_room", roomId).gte("voice_seen", cutoff);
        if (error) throw error;
        const next: Record<number, Peer> = {};''',
    '''      const refreshPeers = async () => {
        const cutoff = new Date(Date.now() - 12_000).toISOString();
        const [{ data, error }, { data: liveProfiles, error: liveProfilesError }] = await Promise.all([
          supabase.from("klyvro_presence").select("slot,voice_room,voice_seen").eq("voice_room", roomId).gte("voice_seen", cutoff),
          supabase.from("klyvro_profiles").select("slot,display_name,avatar_color").order("slot"),
        ]);
        if (error) throw error;
        if (liveProfilesError) throw liveProfilesError;
        profilesRef.current = Object.fromEntries(((liveProfiles ?? []) as ProfileRow[]).map((row) => [Number(row.slot), row]));
        const next: Record<number, Peer> = {};'''
)
replace_once(
    'app/voice-room.tsx',
    '''        {joined && <VoicePerson name={localNameRef.current || profile.name} detail={muted ? "Silenciado" : audio.inputMode === "ptt" ? "Segure V para falar" : "Você"} avatar={(localNameRef.current[0] || profile.name[0] || "J").toUpperCase()} image={profile.photo} color={colorFor(localSlotRef.current ?? 1)} />}''',
    '''        {joined && <VoicePerson name={profile.name || localNameRef.current} detail={muted ? "Silenciado" : audio.inputMode === "ptt" ? "Segure V para falar" : "Você"} avatar={(profile.name[0] || localNameRef.current[0] || "J").toUpperCase()} image={profile.photo} color={colorFor(localSlotRef.current ?? 1)} />}'''
)

print('Klyvro v0.4.5 profile sync patch applied successfully')
