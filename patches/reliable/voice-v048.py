from pathlib import Path

path = Path('app/voice-room.tsx')
text = path.read_text(encoding='utf-8')

def once(old: str, new: str):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'voice v0.4.8 target expected once, found {count}: {old[:150]!r}')
    text = text.replace(old, new, 1)

once(
'''  roomName: string;
  roomId: string;
  profile: UserProfile;''',
'''  roomName: string;
  roomId: string;
  visible?: boolean;
  profile: UserProfile;'''
)
once(
'''type Peer = { slot: number; name: string; avatar: string; color: string; connected: boolean };
type ProfileRow = { slot: number; display_name: string; avatar_color: string };''',
'''type Peer = { slot: number; name: string; avatar: string; image?: string | null; color: string; connected: boolean };
type ProfileRow = { slot: number; display_name: string; avatar_color: string; avatar_data?: string | null };'''
)
once(
'''const colorFor = (slot: number) => ["#ff304f", "#63d6ff", "#f58bd8"][Math.max(0, Math.min(2, slot - 1))] ?? "#ff304f";

export default function VoiceRoom({ roomName, roomId, profile, audio, onAudioChange, onToast }: Props) {''',
'''const PROFILE_COLORS = ["#ff304f", "#63d6ff", "#f58bd8", "#a9ff68", "#ffb15c"] as const;
const colorFor = (slot: number) => PROFILE_COLORS[Math.max(0, Math.min(PROFILE_COLORS.length - 1, slot - 1))] ?? "#ff304f";

function playCatMeow(kind: "join" | "leave") {
  try {
    const AudioContextClass = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioContextClass) return;
    const context = new AudioContextClass();
    const now = context.currentTime;
    const duration = 0.46;
    const gain = context.createGain();
    const filter = context.createBiquadFilter();
    filter.type = "bandpass";
    filter.Q.value = 3.2;
    filter.frequency.setValueAtTime(kind === "join" ? 900 : 760, now);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.075, now + 0.035);
    gain.gain.exponentialRampToValueAtTime(0.042, now + 0.22);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
    filter.connect(gain);
    gain.connect(context.destination);

    const lead = context.createOscillator();
    lead.type = "triangle";
    const start = kind === "join" ? 520 : 760;
    const peak = kind === "join" ? 860 : 540;
    const end = kind === "join" ? 610 : 410;
    lead.frequency.setValueAtTime(start, now);
    lead.frequency.exponentialRampToValueAtTime(peak, now + 0.16);
    lead.frequency.exponentialRampToValueAtTime(end, now + duration);
    lead.connect(filter);

    const body = context.createOscillator();
    body.type = "sine";
    body.frequency.setValueAtTime(start * 0.52, now);
    body.frequency.exponentialRampToValueAtTime(peak * 0.52, now + 0.16);
    body.frequency.exponentialRampToValueAtTime(end * 0.52, now + duration);
    const bodyGain = context.createGain();
    bodyGain.gain.value = 0.22;
    body.connect(bodyGain);
    bodyGain.connect(filter);

    lead.start(now);
    body.start(now);
    lead.stop(now + duration);
    body.stop(now + duration);
    window.setTimeout(() => { void context.close(); }, 700);
  } catch {
    // Audio cues are optional; voice must keep working if Web Audio is unavailable.
  }
}

export default function VoiceRoom({ roomName, roomId, visible = true, profile, audio, onAudioChange, onToast }: Props) {'''
)
once(
'''  const joinedAtRef = useRef(0);
  const lastVoiceNoticeRef = useRef(0);''',
'''  const joinedAtRef = useRef(0);
  const lastVoiceNoticeRef = useRef(0);
  const peerSlotsRef = useRef<Set<number>>(new Set());
  const peersPrimedRef = useRef(false);'''
)
once(
'''    setRemoteScreens({});
    setScreenBusy(false);
  }, []);''',
'''    setRemoteScreens({});
    setScreenBusy(false);
    peerSlotsRef.current = new Set();
    peersPrimedRef.current = false;
  }, []);'''
)

old_query = 'supabase.from("klyvro_profiles").select("slot,display_name,avatar_color").order("slot")'
if text.count(old_query) != 2:
    raise SystemExit(f'voice v0.4.8 expected two profile queries, found {text.count(old_query)}')
text = text.replace(old_query, 'supabase.from("klyvro_profiles").select("slot,display_name,avatar_color,avatar_data").order("slot")')

once(
'''          next[slot] = { slot, name, avatar: (name[0] || "J").toUpperCase(), color: row?.avatar_color || colorFor(slot), connected: pc?.connectionState === "connected" };
          void maybeOffer(slot, name).catch(() => notify(`Não consegui iniciar a conexão com ${name}.`));
        }
        setPeers(next);''',
'''          next[slot] = { slot, name, avatar: (name[0] || "J").toUpperCase(), image: row?.avatar_data ?? null, color: row?.avatar_color || colorFor(slot), connected: pc?.connectionState === "connected" };
          void maybeOffer(slot, name).catch(() => notify(`Não consegui iniciar a conexão com ${name}.`));
        }

        const nextSlots = new Set(Object.keys(next).map(Number));
        if (peersPrimedRef.current) {
          const previousSlots = peerSlotsRef.current;
          const joinedSomeone = [...nextSlots].some((slot) => !previousSlots.has(slot));
          const leftSomeone = [...previousSlots].some((slot) => !nextSlots.has(slot));
          if (joinedSomeone) playCatMeow("join");
          else if (leftSomeone) playCatMeow("leave");
        } else {
          peersPrimedRef.current = true;
        }
        peerSlotsRef.current = nextSlots;

        setPeers(next);'''
)
once(
'''      timers.current.push(window.setInterval(() => { void pollSignals().catch(() => setState("error")); }, 500));
      onToast(`Você entrou em ${roomName}`);''',
'''      timers.current.push(window.setInterval(() => { void pollSignals().catch(() => setState("error")); }, 500));
      playCatMeow("join");
      onToast(`Você entrou em ${roomName}`);'''
)
once(
'''onToast("Os 3 perfis estão em uso. O Klyvro tenta liberar sessões antigas automaticamente.");''',
'''onToast("Os 5 perfis estão em uso. O Klyvro tenta liberar sessões antigas automaticamente.");'''
)
once(
'''  const leave = () => {
    cleanup();''',
'''  const leave = () => {
    playCatMeow("leave");
    cleanup();'''
)
once(
'''  const roomStatus = !secureAudio ? "HTTPS NECESSÁRIO" : !joined ? "PRONTO" : state === "error" ? "RECONECTANDO" : `${list.length + 1} NA SALA`;

  return <div className="voice-room">''',
'''  const roomStatus = !secureAudio ? "HTTPS NECESSÁRIO" : !joined ? "PRONTO" : state === "error" ? "RECONECTANDO" : `${list.length + 1} NA SALA`;

  if (!visible) {
    if (!joined) return null;
    return <aside className="voice-call-dock" aria-label={`Call ativa em ${roomName}`}>
      <div className="voice-call-dock-copy"><span><i /> CALL ATIVA</span><strong>{roomName}</strong><small>{screen ? "Você está compartilhando a tela" : remoteScreenEntries.length ? `${remoteScreenEntries.length} compartilhamento${remoteScreenEntries.length > 1 ? "s" : ""} ativo${remoteScreenEntries.length > 1 ? "s" : ""}` : `${list.length + 1} na sala`}</small></div>
      <div className="voice-call-dock-actions">
        <button className={`round-control ${muted ? "danger" : ""}`} onClick={() => setMuted((value) => !value)} aria-label={muted ? "Ativar microfone" : "Silenciar microfone"} aria-pressed={muted}><Icon name="mic" size={16} /></button>
        <button className={`round-control ${deafened ? "danger" : ""}`} onClick={() => setDeafened((value) => !value)} aria-label={deafened ? "Ativar áudio recebido" : "Desativar áudio recebido"} aria-pressed={deafened}><Icon name="headphones" size={16} /></button>
        <button className="leave-voice" onClick={leave} aria-label="Sair da call"><Icon name="x" size={16} /></button>
      </div>
    </aside>;
  }

  return <div className="voice-room">'''
)
once('VOZ • CORE v0.4.7', 'VOZ • CORE v0.4.8')
once(
'''{list.map((peer) => <VoicePerson key={peer.slot} name={peer.name} detail={remoteScreens[peer.slot] ? "Compartilhando tela" : peer.connected ? "Áudio conectado" : "Na sala • conectando"} avatar={peer.avatar} color={peer.color} />)}''',
'''{list.map((peer) => <VoicePerson key={peer.slot} name={peer.name} detail={remoteScreens[peer.slot] ? "Compartilhando tela" : peer.connected ? "Áudio conectado" : "Na sala • conectando"} avatar={peer.avatar} image={peer.image} color={peer.color} />)}'''
)

old_screen = '''function ScreenView({ stream, label, local = false, onStop }: { stream: MediaStream; label: string; local?: boolean; onStop?: () => void }) {
  const ref = useRef<HTMLVideoElement | null>(null);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    element.srcObject = stream;
    void element.play().catch(() => undefined);
    return () => { if (element.srcObject === stream) element.srcObject = null; };
  }, [stream]);
  return <div className={`screen-card ${local ? "local" : "remote"}`}>
    <video ref={ref} autoPlay muted playsInline aria-label={label} />
    <div className="screen-label"><Icon name="monitor" size={16} /><span>{label}{local ? " • transmitindo" : " • ao vivo"}</span>{onStop && <button onClick={onStop}>Encerrar</button>}</div>
  </div>;
}'''

new_screen = '''function ScreenView({ stream, label, local = false, onStop }: { stream: MediaStream; label: string; local?: boolean; onStop?: () => void }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    const element = videoRef.current;
    if (!element) return;
    element.srcObject = stream;
    void element.play().catch(() => undefined);
    return () => { if (element.srcObject === stream) element.srcObject = null; };
  }, [stream]);

  useEffect(() => {
    const sync = () => setFullscreen(document.fullscreenElement === cardRef.current);
    document.addEventListener("fullscreenchange", sync);
    return () => document.removeEventListener("fullscreenchange", sync);
  }, []);

  const toggleFullscreen = async () => {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
        return;
      }
      const card = cardRef.current;
      if (card?.requestFullscreen) {
        await card.requestFullscreen();
        return;
      }
      const safariVideo = videoRef.current as (HTMLVideoElement & { webkitEnterFullscreen?: () => void }) | null;
      safariVideo?.webkitEnterFullscreen?.();
    } catch {
      // Fullscreen is optional; browser permissions can deny it.
    }
  };

  return <div ref={cardRef} className={`screen-card ${local ? "local" : "remote"}`}>
    <video ref={videoRef} autoPlay muted playsInline aria-label={label} />
    <div className="screen-label"><Icon name="monitor" size={16} /><span>{label}{local ? " • transmitindo" : " • ao vivo"}</span><div className="screen-label-actions"><button type="button" className="screen-fullscreen-button" onClick={toggleFullscreen} aria-label={fullscreen ? `Sair da tela cheia de ${label}` : `Abrir ${label} em tela cheia`}>{fullscreen ? "Sair da tela cheia" : "Tela cheia"}</button>{onStop && <button onClick={onStop}>Encerrar</button>}</div></div>
  </div>;
}'''

once(old_screen, new_screen)

path.write_text(text, encoding='utf-8')
print('Klyvro v0.4.8 voice persistence/meow/fullscreen patch applied')
