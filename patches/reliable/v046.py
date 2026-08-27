from pathlib import Path

ROOT = Path('.')

def replace_once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one target, found {count}: {old[:140]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

# Build metadata and generic pre-claim identity.
replace_once('app/nexora-app.tsx', 'type Member = { name: string; game: string; avatar: string; color: string; status: "online" | "away" | "offline"; bot?: boolean };', 'type Member = { slot?: number; name: string; game: string; avatar: string; color: string; status: "online" | "away" | "offline"; bot?: boolean };')
replace_once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.5";', 'const KLYVRO_BUILD = "0.4.6";')
replace_once('app/settings-panel.tsx', 'export const DEFAULT_PROFILE: UserProfile = { name: "Luccas", photo: null };', 'export const DEFAULT_PROFILE: UserProfile = { name: "Jogador", photo: null };')
replace_once('package.json', '"version": "0.3.0"', '"version": "0.4.6"')

# Correct human-friendly timestamps for older messages.
replace_once(
    'app/nexora-app.tsx',
    '''const createLocalId = (prefix: string) => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
const mergeMessages = (items: Message[], incoming: Message) => {''',
    '''const createLocalId = (prefix: string) => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
const formatMessageTime = (value: string | Date) => {
  const created = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(created.getTime())) return "Horário indisponível";
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const clock = created.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  if (created >= today) return `Hoje, ${clock}`;
  if (created >= yesterday) return `Ontem, ${clock}`;
  const date = created.toLocaleDateString("pt-BR", created.getFullYear() === now.getFullYear()
    ? { day: "2-digit", month: "2-digit" }
    : { day: "2-digit", month: "2-digit", year: "numeric" });
  return `${date}, ${clock}`;
};
const mergeMessages = (items: Message[], incoming: Message) => {'''
)
replace_once(
    'app/nexora-app.tsx',
    '''  const [storageReady, setStorageReady] = useState(false);
  const [networkState, setNetworkState] = useState<"connecting" | "online" | "offline">("connecting");''',
    '''  const [storageReady, setStorageReady] = useState(false);
  const [connectAttempt, setConnectAttempt] = useState(0);
  const [networkState, setNetworkState] = useState<"connecting" | "online" | "offline">("connecting");'''
)
replace_once(
    'app/nexora-app.tsx',
    '''  const [profileRows, setProfileRows] = useState<KlyvroProfileRow[]>([
    { slot: 1, display_name: "Luccas", avatar_color: "#ff304f", claimed: false },
    { slot: 2, display_name: "Jogador 2", avatar_color: "#63d6ff", claimed: false },
    { slot: 3, display_name: "Jogador 3", avatar_color: "#f58bd8", claimed: false },
  ]);''',
    '''  const [profileRows, setProfileRows] = useState<KlyvroProfileRow[]>([
    { slot: 1, display_name: "Jogador 1", avatar_color: "#ff304f", claimed: false },
    { slot: 2, display_name: "Jogador 2", avatar_color: "#63d6ff", claimed: false },
    { slot: 3, display_name: "Jogador 3", avatar_color: "#f58bd8", claimed: false },
  ]);'''
)
replace_once(
    'app/nexora-app.tsx',
    '''  const activeServerRef = useRef<ServerId>(activeServer);
  const pendingProfileNameRef = useRef<string | null>(null);''',
    '''  const activeServerRef = useRef<ServerId>(activeServer);
  const pendingProfileNameRef = useRef<string | null>(null);
  const seenServerMessageIdsRef = useRef<Set<string>>(new Set());
  const messagesPrimedRef = useRef(false);'''
)
replace_once(
    'app/nexora-app.tsx',
    '''  const realtimeMembers: Member[] = profileRows.map((item) => ({
    name: item.display_name,''',
    '''  const realtimeMembers: Member[] = profileRows.map((item) => ({
    slot: item.slot,
    name: item.display_name,'''
)

# Keep composer height correct when switching channels, clearing, or restoring a failed send.
replace_once(
    'app/nexora-app.tsx',
    '''  useEffect(() => {
    const area = messageScrollRef.current;
    if (!area || !stickToBottomRef.current) return;
    requestAnimationFrame(() => { area.scrollTop = area.scrollHeight; });
  }, [currentMessages.length, selected]);''',
    '''  useEffect(() => {
    const area = messageScrollRef.current;
    if (!area || !stickToBottomRef.current) return;
    requestAnimationFrame(() => { area.scrollTop = area.scrollHeight; });
  }, [currentMessages.length, selected]);
  useEffect(() => {
    const field = composerRef.current;
    if (!field) return;
    const frame = requestAnimationFrame(() => {
      field.style.height = "0px";
      field.style.height = `${Math.min(field.scrollHeight, 160)}px`;
      field.style.overflowY = field.scrollHeight > 160 ? "auto" : "hidden";
    });
    return () => cancelAnimationFrame(frame);
  }, [draft, selected]);'''
)

# Robust identity recovery + real unread state + proper timestamps.
replace_once(
    'app/nexora-app.tsx',
    '''    let messageTimer: number | null = null;
    let presenceTimer: number | null = null;
    let heartbeatTimer: number | null = null;
    setNetworkState("connecting");''',
    '''    let messageTimer: number | null = null;
    let presenceTimer: number | null = null;
    let heartbeatTimer: number | null = null;
    let identityRetryTimer: number | null = null;
    setProfileSlot(null);
    setNetworkState("connecting");

    const scheduleIdentityRetry = (delay = 15_000) => {
      if (cancelled || identityRetryTimer !== null) return;
      identityRetryTimer = window.setTimeout(() => {
        identityRetryTimer = null;
        if (!cancelled) setConnectAttempt((attempt) => attempt + 1);
      }, delay);
    };'''
)
replace_once(
    'app/nexora-app.tsx',
    '''      const created = new Date(row.created_at);
      return { id: String(row.id), author: String(row.author_name), avatar: (String(row.author_name)[0] || "J").toUpperCase(), color, time: `Hoje, ${created.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`, text: String(row.body), channelId: String(row.channel_id) };''',
    '''      return { id: String(row.id), author: String(row.author_name), avatar: (String(row.author_name)[0] || "J").toUpperCase(), color, time: formatMessageTime(row.created_at), text: String(row.body), channelId: String(row.channel_id) };'''
)
replace_once(
    'app/nexora-app.tsx',
    '''      if (error) throw error;
      if (cancelled || !data) return;
      setMessages((current) => {
        const updated = { ...current };
        for (const row of [...data].reverse()) {
          const message = rowToMessage(row as never);
          const channelId = message.channelId ?? "geral";
          updated[channelId] = mergeMessages(updated[channelId] ?? [], message);
        }
        return updated;
      });''',
    '''      if (error) throw error;
      if (cancelled || !data) return;
      const previousSeen = seenServerMessageIdsRef.current;
      const nextSeen = new Set<string>();
      const unreadChannels = new Set<string>();
      for (const row of data) {
        const id = String(row.id);
        const channelId = String(row.channel_id);
        nextSeen.add(id);
        if (messagesPrimedRef.current && !previousSeen.has(id) && channelId !== selectedRef.current) unreadChannels.add(channelId);
      }
      seenServerMessageIdsRef.current = nextSeen;
      messagesPrimedRef.current = true;
      setMessages((current) => {
        const updated = { ...current };
        for (const row of [...data].reverse()) {
          const message = rowToMessage(row as never);
          const channelId = message.channelId ?? "geral";
          updated[channelId] = mergeMessages(updated[channelId] ?? [], message);
        }
        return updated;
      });
      if (unreadChannels.size) setReadChannels((current) => {
        const next = { ...current };
        unreadChannels.forEach((channelId) => { next[channelId] = false; });
        return next;
      });'''
)
replace_once(
    'app/nexora-app.tsx',
    '''        } catch (heartbeatError) {
          console.warn("Klyvro heartbeat inicial falhou; mantendo chat ativo e tentando reconectar", heartbeatError);
          if (!cancelled) setNetworkState("offline");
        }''',
    '''        } catch (heartbeatError) {
          console.warn("Klyvro heartbeat inicial falhou; mantendo chat ativo e tentando reconectar", heartbeatError);
          const reason = heartbeatError instanceof Error ? heartbeatError.message : String(heartbeatError);
          if (!cancelled) setNetworkState("offline");
          if (reason.includes("profile not claimed")) scheduleIdentityRetry(1_000);
        }'''
)
replace_once(
    'app/nexora-app.tsx',
    '''        heartbeatTimer = window.setInterval(() => {
          void heartbeat().catch(() => setNetworkState("offline"));
        }, 5000);''',
    '''        heartbeatTimer = window.setInterval(() => {
          void heartbeat().catch((heartbeatError) => {
            const reason = heartbeatError instanceof Error ? heartbeatError.message : String(heartbeatError);
            if (!cancelled) setNetworkState("offline");
            if (reason.includes("profile not claimed")) scheduleIdentityRetry(1_000);
          });
        }, 5000);'''
)
replace_once(
    'app/nexora-app.tsx',
    '''          if (reason.includes("currently active") || reason.includes("already claimed")) {
            setToast("Os 3 perfis estão ativos. Feche uma sessão antiga e aguarde até 60 segundos.");
          }''',
    '''          if (reason.includes("currently active") || reason.includes("already claimed")) {
            setToast("Os 3 perfis estão ativos. O Klyvro vai tentar entrar novamente sozinho.");
            scheduleIdentityRetry(15_000);
          } else if (reason.includes("profile not claimed")) {
            scheduleIdentityRetry(1_000);
          }'''
)
replace_once(
    'app/nexora-app.tsx',
    '''      if (heartbeatTimer !== null) window.clearInterval(heartbeatTimer);
    };
  }, [storageReady]);''',
    '''      if (heartbeatTimer !== null) window.clearInterval(heartbeatTimer);
      if (identityRetryTimer !== null) window.clearTimeout(identityRetryTimer);
    };
  }, [storageReady, connectAttempt]);'''
)

# Synchronously keep heartbeat routing refs in step with navigation state.
replace_once('app/nexora-app.tsx', '''    setActiveServer(id);
    setSelected(remembered);''', '''    activeServerRef.current = id;
    selectedRef.current = remembered;
    setActiveServer(id);
    setSelected(remembered);''')
replace_once('app/nexora-app.tsx', '''  const selectChannel = (id: string) => {
    setSelected(id);''', '''  const selectChannel = (id: string) => {
    selectedRef.current = id;
    setSelected(id);''')
replace_once('app/nexora-app.tsx', '''    setActiveServer(destination);
    setSelected(id);''', '''    activeServerRef.current = destination;
    selectedRef.current = id;
    setActiveServer(destination);
    setSelected(id);''')
replace_once('app/nexora-app.tsx', '''  const goHome = () => {
    setActiveServer("kv");
    setSelected("geral");''', '''  const goHome = () => {
    activeServerRef.current = "kv";
    selectedRef.current = "geral";
    setActiveServer("kv");
    setSelected("geral");''')

# Use the same timestamp formatter on optimistic -> server replacement.
replace_once(
    'app/nexora-app.tsx',
    '''        const created = new Date(row.created_at);
        const synced: Message = { id: String(row.id), author: String(row.author_name), avatar: (String(row.author_name)[0] || "J").toUpperCase(), color: ["#ff304f", "#63d6ff", "#f58bd8"][Math.max(0, Math.min(2, Number(row.author_slot) - 1))] ?? "#ff304f", time: `Hoje, ${created.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`, text: String(row.body), channelId: String(row.channel_id), reply: replyTarget };''',
    '''        const synced: Message = { id: String(row.id), author: String(row.author_name), avatar: (String(row.author_name)[0] || "J").toUpperCase(), color: ["#ff304f", "#63d6ff", "#f58bd8"][Math.max(0, Math.min(2, Number(row.author_slot) - 1))] ?? "#ff304f", time: formatMessageTime(row.created_at), text: String(row.body), channelId: String(row.channel_id), reply: replyTarget };'''
)

# Real unread badge, stable member keys, and accurate offline label.
p = ROOT / 'app/nexora-app.tsx'
text = p.read_text(encoding='utf-8')
old = '<MemberRow key={member.name} member={member}'
if text.count(old) != 2:
    raise SystemExit(f'app/nexora-app.tsx: expected two member keys, found {text.count(old)}')
p.write_text(text.replace(old, '<MemberRow key={member.slot ?? member.name} member={member}'), encoding='utf-8')
replace_once('app/nexora-app.tsx', 'unread={readChannels[item.id] ? undefined : item.badge}', 'unread={readChannels[item.id] === false ? 1 : undefined}')
replace_once('app/nexora-app.tsx', '<span>AUSENTE — {awayMembers.length}</span>', '<span>OFFLINE — {awayMembers.length}</span>')

# Settings copy must not contradict server-backed profile sync.
replace_once('app/settings-panel.tsx', '''    onProfileChange({ name: cleanName, photo });
    setName(cleanName);
    onToast("Perfil salvo neste dispositivo");''', '''    onProfileChange({ name: cleanName, photo });
    setName(cleanName);''')
replace_once('app/settings-panel.tsx', '<span id="preferences-local-note">PREFERÊNCIAS LOCAIS</span>', '<span id="preferences-local-note">PERFIL E PREFERÊNCIAS</span>')

# Local LFG groups are all owned by this browser in the current implementation; keep host identity current after renames.
replace_once('app/lfg-board.tsx', 'type Party = { id: string; game: string; title: string; mode: string; rank: string; members: number; capacity: number; host: string; hostAvatar: string; hostPhoto?: string | null; color: string; time: string; joined?: boolean };', 'type Party = { id: string; game: string; title: string; mode: string; rank: string; members: number; capacity: number; host: string; hostAvatar: string; hostPhoto?: string | null; color: string; time: string; joined?: boolean; owned?: boolean };')
replace_once('app/lfg-board.tsx', '''  const [attempted, setAttempted] = useState(false);
  const createButtonRef = useRef<HTMLButtonElement>(null);''', '''  const [attempted, setAttempted] = useState(false);
  const [partiesLoaded, setPartiesLoaded] = useState(false);
  const createButtonRef = useRef<HTMLButtonElement>(null);''')
replace_once('app/lfg-board.tsx', '''      const cleaned = stored.filter((party) => !["p1", "p2", "p3"].includes(party.id));
      setParties(cleaned);
      if (cleaned.length !== stored.length) writeLocal(STORAGE_KEYS.parties, cleaned);''', '''      const cleaned = stored.filter((party) => !["p1", "p2", "p3"].includes(party.id)).map((party) => ({ ...party, owned: party.owned ?? true }));
      setParties(cleaned);
      setPartiesLoaded(true);
      writeLocal(STORAGE_KEYS.parties, cleaned);''')
replace_once('app/lfg-board.tsx', '''  useEffect(() => {
    if (!creating) return;''', '''  useEffect(() => {
    if (!partiesLoaded) return;
    setParties((current) => {
      let changed = false;
      const next = current.map((party) => {
        if (!party.owned) return party;
        const nextHost = profile.name.trim().slice(0, 24) || "Jogador";
        const nextAvatar = (nextHost[0] || "J").toUpperCase();
        if (party.host === nextHost && party.hostAvatar === nextAvatar && party.hostPhoto === profile.photo) return party;
        changed = true;
        return { ...party, host: nextHost, hostAvatar: nextAvatar, hostPhoto: profile.photo };
      });
      if (changed) writeLocal(STORAGE_KEYS.parties, next);
      return changed ? next : current;
    });
  }, [partiesLoaded, profile.name, profile.photo]);

  useEffect(() => {
    if (!creating) return;''')
replace_once('app/lfg-board.tsx', 'color: "#ff304f", joined: true };', 'color: "#ff304f", joined: true, owned: true };')

replace_once('app/voice-room.tsx', 'VOZ • CORE v0.4.5', 'VOZ • CORE v0.4.6')

print('Klyvro v0.4.6 stability patch applied successfully')
