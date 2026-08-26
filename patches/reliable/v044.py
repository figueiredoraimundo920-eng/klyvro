from pathlib import Path

ROOT = Path('.')

def replace_once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one target, found {count}: {old[:120]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

replace_once('app/supabase-client.ts', '''export function getDeviceToken() {
  const key = "klyvro-device-token-v1";
  const existing = window.localStorage.getItem(key);
  if (existing && existing.length >= 20) return existing;
  const token = crypto.randomUUID() + crypto.randomUUID();
  window.localStorage.setItem(key, token);
  return token;
}
''', '''let memoryDeviceToken: string | null = null;

function createDeviceToken() {
  const cryptoApi = globalThis.crypto;
  if (typeof cryptoApi?.randomUUID === "function") return `${cryptoApi.randomUUID()}${cryptoApi.randomUUID()}`;
  if (typeof cryptoApi?.getRandomValues === "function") {
    const bytes = new Uint8Array(32);
    cryptoApi.getRandomValues(bytes);
    return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
}

export function getDeviceToken() {
  const key = "klyvro-device-token-v1";
  if (memoryDeviceToken) return memoryDeviceToken;
  try {
    const existing = window.localStorage.getItem(key);
    if (existing && existing.length >= 20) {
      memoryDeviceToken = existing;
      return existing;
    }
  } catch {
    // Storage can be blocked in privacy/restricted browsing modes; keep an in-memory session token.
  }

  const token = createDeviceToken();
  memoryDeviceToken = token;
  try { window.localStorage.setItem(key, token); } catch { /* in-memory fallback stays active */ }
  return token;
}
''')

for old, new in [
    ('{ id: "geral", label: "geral", type: "text", badge: 3 }', '{ id: "geral", label: "geral", type: "text" }'),
    ('{ id: "lfg", label: "procurando-time", type: "lfg", badge: 2 }', '{ id: "lfg", label: "procurando-time", type: "lfg" }'),
    ('{ id: "cp-geral", label: "competitivo-geral", type: "text", badge: 1 }', '{ id: "cp-geral", label: "competitivo-geral", type: "text" }'),
    ('{ id: "mc-geral", label: "minecraft-geral", type: "text", badge: 2 }', '{ id: "mc-geral", label: "minecraft-geral", type: "text" }'),
]:
    replace_once('app/nexora-app.tsx', old, new)

replace_once('app/nexora-app.tsx', '''    members: [
      { name: "Maya", game: "VALORANT • Lobby", avatar: "M", color: "#f58bd8", status: "online" },
      { name: "Caio", game: "Minecraft", avatar: "C", color: "#63d6ff", status: "online" },
      { name: "Lia", game: "EA FC 26", avatar: "L", color: "#ffb15c", status: "online" },
      { name: "KLY", game: "Assistente do servidor", avatar: "K", color: "#ff304f", status: "online", bot: true },
      { name: "Rafa", game: "Ausente há 12 min", avatar: "R", color: "#ad94ff", status: "away" },
    ],''', '    members: [],')
replace_once('app/nexora-app.tsx', '''    members: [
      { name: "Nina", game: "VALORANT • Radiante", avatar: "N", color: "#d7a7ff", status: "online" },
      { name: "Theo", game: "Rocket League", avatar: "T", color: "#77d9ff", status: "online" },
      { name: "Ivo", game: "Counter-Strike 2", avatar: "I", color: "#ffca70", status: "online" },
      { name: "Maya", game: "Montando time", avatar: "M", color: "#f58bd8", status: "away" },
    ],''', '    members: [],')
replace_once('app/nexora-app.tsx', '''    members: [
      { name: "Caio", game: "Minecraft • Survival", avatar: "C", color: "#63d6ff", status: "online" },
      { name: "Bia", game: "Construindo uma vila", avatar: "B", color: "#83e58e", status: "online" },
      { name: "Davi", game: "Explorando cavernas", avatar: "D", color: "#ffb15c", status: "online" },
      { name: "Lia", game: "Ausente há 8 min", avatar: "L", color: "#f58bd8", status: "away" },
    ],''', '    members: [],')

replace_once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.3";', 'const KLYVRO_BUILD = "0.4.4";')
replace_once('app/nexora-app.tsx', '''      setMessages({ ...initialMessages, ...readLocal<Record<string, Message[]>>(STORAGE_KEYS.messages, {}, "nexora-messages", (value) => isLocalRecord(value) && Object.values(value).every(Array.isArray)) });''', '''      setMessages(initialMessages);
      try {
        window.localStorage.removeItem(STORAGE_KEYS.messages);
        window.localStorage.removeItem("nexora-messages");
      } catch { /* storage may be unavailable */ }''')
replace_once('app/nexora-app.tsx', '''      const { data, error } = await supabase.from("klyvro_messages").select("id,server_id,channel_id,author_slot,author_name,body,created_at").order("created_at", { ascending: true }).limit(300);''', '''      const { data, error } = await supabase.from("klyvro_messages").select("id,server_id,channel_id,author_slot,author_name,body,created_at").order("created_at", { ascending: false }).limit(300);''')
replace_once('app/nexora-app.tsx', '''        for (const row of data) {''', '''        for (const row of [...data].reverse()) {''')
replace_once('app/nexora-app.tsx', 'setToast("Os 3 perfis estão ativos. Feche uma sessão antiga e aguarde até 20 segundos.");', 'setToast("Os 3 perfis estão ativos. Feche uma sessão antiga e aguarde até 60 segundos.");')

replace_once('app/nexora-app.tsx', '''  const submitMessage = () => {
    const text = draft.trim();
    if (!text || text.length > MAX_MESSAGE_LENGTH || channel.type !== "text") return;
    const tempId = createLocalId("message");
    const next: Message = { id: tempId, author: profile.name.trim().slice(0, 24) || "Jogador", avatar: (profile.name[0] || "J").toUpperCase(), avatarUrl: profile.photo, color: "#ff304f", time: "Agora", text, reply: replying ?? undefined };
    setMessages((previous) => ({ ...previous, [selected]: mergeMessages(previous[selected] ?? [], next) }));

    const token = deviceTokenRef.current;
    if (token && profileSlot) {
      void supabase.rpc("klyvro_send_message", { p_token: token, p_server_id: activeServer, p_channel_id: selected, p_body: text }).then(({ data, error }) => {
        if (error) {
          setNetworkState("offline");
          setToast("Servidor indisponível; a mensagem ficou só neste navegador.");
          return;
        }
        const raw = Array.isArray(data) ? data[0] : data;
        if (raw && typeof raw === "object" && "id" in raw) {
          const row = raw as { id: string; author_name: string; author_slot: number; body: string; channel_id: string; created_at: string };
          const created = new Date(row.created_at);
          const synced: Message = { id: String(row.id), author: String(row.author_name), avatar: (String(row.author_name)[0] || "J").toUpperCase(), color: ["#ff304f", "#63d6ff", "#f58bd8"][Math.max(0, Math.min(2, Number(row.author_slot) - 1))] ?? "#ff304f", time: `Hoje, ${created.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`, text: String(row.body), channelId: String(row.channel_id) };
          setMessages((previous) => ({ ...previous, [selected]: [...(previous[selected] ?? []).filter((message) => message.id !== tempId && message.id !== synced.id), synced].slice(-150) }));
        }
        setNetworkState("online");
        setToast("Mensagem sincronizada");
      });
    } else setToast("Identidade ainda conectando; mensagem mantida localmente.");

    setDraft("");
    setReplying(null);
    closeTransientPanels();
    stickToBottomRef.current = true;
  };''', '''  const submitMessage = () => {
    const text = draft.trim();
    if (!text || text.length > MAX_MESSAGE_LENGTH || channel.type !== "text") return;
    const token = deviceTokenRef.current;
    if (!token || !profileSlot) {
      setToast("Sua identidade ainda está conectando. Tente enviar novamente em instantes.");
      return;
    }

    const tempId = createLocalId("message");
    const replyTarget = replying ?? undefined;
    const next: Message = { id: tempId, author: profile.name.trim().slice(0, 24) || "Jogador", avatar: (profile.name[0] || "J").toUpperCase(), avatarUrl: profile.photo, color: "#ff304f", time: "Enviando…", text, reply: replyTarget };
    setMessages((previous) => ({ ...previous, [selected]: mergeMessages(previous[selected] ?? [], next) }));
    setDraft("");
    setReplying(null);
    closeTransientPanels();
    stickToBottomRef.current = true;

    void supabase.rpc("klyvro_send_message", { p_token: token, p_server_id: activeServer, p_channel_id: selected, p_body: text }).then(({ data, error }) => {
      if (error) {
        setNetworkState("offline");
        setMessages((previous) => ({ ...previous, [selected]: (previous[selected] ?? []).filter((message) => message.id !== tempId) }));
        setDraft((current) => current ? current : text);
        if (replyTarget) setReplying((current) => current ?? replyTarget);
        setToast("Falha ao enviar. A mensagem voltou para o campo para você tentar novamente.");
        return;
      }
      const raw = Array.isArray(data) ? data[0] : data;
      if (raw && typeof raw === "object" && "id" in raw) {
        const row = raw as { id: string; author_name: string; author_slot: number; body: string; channel_id: string; created_at: string };
        const created = new Date(row.created_at);
        const synced: Message = { id: String(row.id), author: String(row.author_name), avatar: (String(row.author_name)[0] || "J").toUpperCase(), color: ["#ff304f", "#63d6ff", "#f58bd8"][Math.max(0, Math.min(2, Number(row.author_slot) - 1))] ?? "#ff304f", time: `Hoje, ${created.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`, text: String(row.body), channelId: String(row.channel_id), reply: replyTarget };
        setMessages((previous) => ({ ...previous, [selected]: [...(previous[selected] ?? []).filter((message) => message.id !== tempId && message.id !== synced.id), synced].slice(-150) }));
      }
      setNetworkState("online");
    });
  };''')

replace_once('app/nexora-app.tsx', '''  const react = (id: string, emoji: string) => setMessages((previous) => {
    const updated = { ...previous, [selected]: (previous[selected] ?? []).map((message) => message.id === id ? { ...message, reactions: { ...message.reactions, [emoji]: (message.reactions?.[emoji] ?? 0) + 1 } } : message) };
    writeLocal(STORAGE_KEYS.messages, updated);
    return updated;
  });''', '''  const react = (id: string, emoji: string) => {
    setMessages((previous) => ({ ...previous, [selected]: (previous[selected] ?? []).map((message) => message.id === id ? { ...message, reactions: { ...message.reactions, [emoji]: (message.reactions?.[emoji] ?? 0) + 1 } } : message) }));
    setToast("Reação local nesta versão; mensagens continuam sincronizadas.");
  };''')

replace_once('app/nexora-app.tsx', '''  const copyInvite = async () => {
    try {
      await navigator.clipboard?.writeText(`${window.location.origin}/?invite=klyvro-lobby`);
      setToast("Convite copiado para a área de transferência");
    } catch {
      setToast("Não foi possível copiar automaticamente neste navegador");
    }
  };''', '''  const copyInvite = async () => {
    const url = new URL(window.location.pathname, window.location.origin).toString();
    try {
      if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(url);
      else {
        const field = document.createElement("textarea");
        field.value = url;
        field.setAttribute("readonly", "");
        field.style.position = "fixed";
        field.style.opacity = "0";
        document.body.appendChild(field);
        field.select();
        const copied = document.execCommand("copy");
        field.remove();
        if (!copied) throw new Error("copy unsupported");
      }
      setToast("Link do Klyvro copiado");
    } catch {
      setToast(`Copie este endereço: ${url}`);
    }
  };''')

replace_once('app/nexora-app.tsx', '<span>Online • 32 ms</span>', '<span>{networkState === "online" ? "Online • sincronizado" : networkState === "connecting" ? "Conectando…" : "Reconectando…"}</span>')
replace_once('app/nexora-app.tsx', '''{server.channels.filter((item) => item.type === "voice").map((item) => <div key={item.id}><ChannelRow channel={item} active={selected === item.id} unread={readChannels[item.id] ? undefined : item.badge} onClick={() => selectChannel(item.id)} />{item.id === server.channels.find((candidate) => candidate.type === "voice")?.id && <div className="voice-mini">{realtimeMembers.filter((member) => member.status === "online").slice(0, 2).map((member) => <span key={member.name}><Avatar label={member.avatar} color={member.color} small /> {member.name}</span>)}</div>}</div>)}''', '''{server.channels.filter((item) => item.type === "voice").map((item) => <div key={item.id}><ChannelRow channel={item} active={selected === item.id} onClick={() => selectChannel(item.id)} /></div>)}''')
replace_once('app/nexora-app.tsx', '<footer>Demonstração local</footer>', '<footer>Notificações locais</footer>')
replace_once('app/nexora-app.tsx', '<span><Icon name="radio" size={12} /> Baixa latência</span>', '<span><Icon name="radio" size={12} /> Conexão monitorada</span>')
replace_once('app/nexora-app.tsx', '<div className="date-divider"><span>24 de agosto de 2026</span></div>', '<div className="date-divider"><span>Mensagens recentes</span></div>')

replace_once('app/lfg-board.tsx', '''const initialParties: Party[] = [
  { id: "p1", game: "VALORANT", title: "Subindo pro Ouro", mode: "Competitivo", rank: "Prata 3+", members: 3, capacity: 5, host: "Maya", hostAvatar: "M", color: "#f58bd8", time: "Agora" },
  { id: "p2", game: "MINECRAFT", title: "Exploração e bosses", mode: "Java 1.20.1", rank: "Casual", members: 2, capacity: 4, host: "Caio", hostAvatar: "C", color: "#63d6ff", time: "19:30" },
  { id: "p3", game: "EA FC 26", title: "Clubs — falta atacante", mode: "Clubs", rank: "Divisão 4", members: 4, capacity: 5, host: "Lia", hostAvatar: "L", color: "#ffb15c", time: "20:00" },
];''', 'const initialParties: Party[] = [];')
replace_once('app/lfg-board.tsx', '''  useEffect(() => {
    const timer = window.setTimeout(() => setParties(readLocal<Party[]>(STORAGE_KEYS.parties, initialParties, "nexora-parties", (value) => Array.isArray(value) && value.every((item) => Boolean(item) && typeof item === "object"))), 0);
    return () => window.clearTimeout(timer);
  }, []);''', '''  useEffect(() => {
    const timer = window.setTimeout(() => {
      const stored = readLocal<Party[]>(STORAGE_KEYS.parties, initialParties, "nexora-parties", (value) => Array.isArray(value) && value.every((item) => Boolean(item) && typeof item === "object"));
      const cleaned = stored.filter((party) => !["p1", "p2", "p3"].includes(party.id));
      setParties(cleaned);
      if (cleaned.length !== stored.length) writeLocal(STORAGE_KEYS.parties, cleaned);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);''')
replace_once('app/lfg-board.tsx', 'if (!formComplete) { onToast("Revise os campos indicados antes de publicar."); return; }', 'if (!formComplete) { onToast("Revise os campos indicados antes de salvar."); return; }')
replace_once('app/lfg-board.tsx', 'Campos obrigatórios. Tudo é publicado apenas neste dispositivo.', 'Campos obrigatórios. O grupo é salvo apenas neste dispositivo.')
replace_once('app/lfg-board.tsx', '<Icon name="users" /> Publicar grupo', '<Icon name="users" /> Salvar grupo')

replace_once('app/settings-panel.tsx', 'Nome e foto ficam salvos apenas neste dispositivo. Nenhum upload é feito nesta versão.', 'Seu nome é sincronizado no Klyvro. A foto continua salva apenas neste dispositivo e não é enviada ao servidor.')

replace_once('app/layout.tsx', '''  other: {
    "codex-preview": "development",
  },
''', '')
replace_once('app/layout.tsx', '''    type: "website",
    images: [{ url: "/klyvro/og.png", width: 1200, height: 630, alt: "Klyvro — Jogue junto. Sem perder FPS." }],''', '''    type: "website",''')
replace_once('app/layout.tsx', '    card: "summary_large_image",', '    card: "summary",')
replace_once('app/layout.tsx', '''    description: "Voz, chat e grupos para jogadores, com o desempenho em primeiro lugar.",
    images: ["/klyvro/og.png"],''', '''    description: "Voz, chat e grupos para jogadores, com o desempenho em primeiro lugar.",''')

replace_once('app/voice-room.tsx', '''        pc.onconnectionstatechange = () => {
          const connected = pc.connectionState === "connected";
          setPeers((current) => current[remoteSlot] ? { ...current, [remoteSlot]: { ...current[remoteSlot], connected } } : current);
          if (connected) setState("online");
          if (pc.connectionState === "failed") {
            setState("waiting");
            onToast(`Áudio com ${remoteName} não fechou. A rede pode exigir TURN.`);
          }
        };''', '''        pc.onconnectionstatechange = () => {
          const connected = pc.connectionState === "connected";
          setPeers((current) => current[remoteSlot] ? { ...current, [remoteSlot]: { ...current[remoteSlot], connected } } : current);
          if (connected) setState("online");
          if (pc.connectionState === "disconnected") setState("waiting");
          if (pc.connectionState === "failed") {
            setState("waiting");
            offerStarted.current.delete(remoteSlot);
            onToast(`Áudio com ${remoteName} falhou; tentando uma nova rota.`);
            window.setTimeout(() => {
              if (pcs.current.get(remoteSlot) !== pc || pc.connectionState === "connected") return;
              pc.close();
              pcs.current.delete(remoteSlot);
              pendingCandidates.current.delete(remoteSlot);
              offerStarted.current.delete(remoteSlot);
              const element = remoteAudio.current.get(remoteSlot);
              if (element) { element.pause(); element.srcObject = null; remoteAudio.current.delete(remoteSlot); }
            }, 1500);
          }
        };''')
replace_once('app/voice-room.tsx', '''      const voiceHeartbeat = async () => {
        const { error } = await supabase.rpc("klyvro_voice_heartbeat", { p_token: token, p_room_id: roomId });
        if (error) throw error;
      };''', '''      const voiceHeartbeat = async () => {
        const { error } = await supabase.rpc("klyvro_voice_heartbeat", { p_token: token, p_room_id: roomId });
        if (error) throw error;
        setState((current) => current === "error" ? "waiting" : current);
      };''')
replace_once('app/voice-room.tsx', '''      const pollSignals = async () => {
        const { data, error } = await supabase.rpc("klyvro_poll_voice_signals", { p_token: token, p_room_id: roomId, p_after_id: lastSignalIdRef.current });
        if (error) throw error;
        for (const raw of (data ?? []) as SignalRow[]) {''', '''      const pollSignals = async () => {
        const { data, error } = await supabase.rpc("klyvro_poll_voice_signals", { p_token: token, p_room_id: roomId, p_after_id: lastSignalIdRef.current });
        if (error) throw error;
        setState((current) => current === "error" ? "waiting" : current);
        for (const raw of (data ?? []) as SignalRow[]) {''')
replace_once('app/voice-room.tsx', '''      timers.current.push(window.setInterval(() => { void voiceHeartbeat().catch(() => setState("error")); }, 3000));
      timers.current.push(window.setInterval(() => { void refreshPeers().catch(() => setState("error")); }, 1000));
      timers.current.push(window.setInterval(() => { void pollSignals().catch(() => setState("error")); }, 400));''', '''      timers.current.push(window.setInterval(() => { void voiceHeartbeat().catch(() => setState("error")); }, 4000));
      timers.current.push(window.setInterval(() => { void refreshPeers().catch(() => setState("error")); }, 1500));
      timers.current.push(window.setInterval(() => { void pollSignals().catch(() => setState("error")); }, 700));''')
replace_once('app/voice-room.tsx', 'aguarde até 20 segundos.', 'aguarde até 60 segundos.')
replace_once('app/voice-room.tsx', 'VOZ • CORE v0.4.3', 'VOZ • CORE v0.4.4')
replace_once('app/voice-room.tsx', '<button className="empty-voice-slot" onClick={join}><Icon name="plus" /><span>Entrar na sala</span></button>', '<button className="empty-voice-slot" onClick={join} disabled={!secureAudio} aria-disabled={!secureAudio}><Icon name="plus" /><span>{secureAudio ? "Entrar na sala" : "HTTPS necessário"}</span></button>')
replace_once('app/voice-room.tsx', 'Assim que outro usuário entrar neste mesmo canal ele aparece aqui, mesmo se o WebSocket estiver bloqueado.', 'Assim que outro usuário entrar neste mesmo canal ele aparece aqui automaticamente.')

print('Klyvro v0.4.4 patch applied successfully')
