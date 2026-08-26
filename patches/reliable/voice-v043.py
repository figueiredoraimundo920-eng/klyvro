from pathlib import Path

path = Path('app/voice-room.tsx')
text = path.read_text(encoding='utf-8')

replacements = [
    (
        '  const [screen, setScreen] = useState<MediaStream | null>(null);',
        '  const [screen, setScreen] = useState<MediaStream | null>(null);\n  const [secureAudio, setSecureAudio] = useState(true);'
    ),
    (
        '  useEffect(() => () => cleanup(), [cleanup]);\n  useEffect(() => {\n    const track = mic.current?.getAudioTracks()[0];',
        '  useEffect(() => () => cleanup(), [cleanup]);\n  useEffect(() => {\n    setSecureAudio(window.isSecureContext && !!navigator.mediaDevices?.getUserMedia && typeof RTCPeerConnection !== "undefined");\n  }, []);\n  useEffect(() => {\n    const track = mic.current?.getAudioTracks()[0];'
    ),
    (
        '  const join = async () => {\n    if (joined) return;\n    setJoined(true);',
        '  const join = async () => {\n    if (joined) return;\n    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia || typeof RTCPeerConnection === "undefined") {\n      setSecureAudio(false);\n      setState("error");\n      onToast("A call precisa de HTTPS para liberar microfone e WebRTC neste navegador.");\n      return;\n    }\n    setJoined(true);'
    ),
    (
        '      onToast("Falha ao entrar na call.");',
        '      const reason = error instanceof Error ? error.message : String(error);\n      if (reason.includes("currently active") || reason.includes("already claimed")) onToast("Os 3 perfis estão em uso. Feche uma sessão antiga e aguarde até 20 segundos.");\n      else onToast("Falha ao entrar na call.");'
    ),
    (
        '  const roomStatus = !joined ? "PRONTO" : state === "error" ? "RECONECTANDO" : `${list.length + 1} NA SALA`;',
        '  const roomStatus = !secureAudio ? "HTTPS NECESSÁRIO" : !joined ? "PRONTO" : state === "error" ? "RECONECTANDO" : `${list.length + 1} NA SALA`;'
    ),
    ('VOZ • CORE v0.4.1', 'VOZ • CORE v0.4.3'),
    (
        '  return <div className="voice-room">\n    <div className="voice-hero">',
        '  return <div className="voice-room">\n    {!secureAudio && <div className="voice-beta-note" role="status"><strong>HTTPS necessário para voz</strong><span>O chat continua funcionando, mas o navegador bloqueia microfone/WebRTC em uma página HTTP.</span></div>}\n    <div className="voice-hero">'
    ),
    (
        '<button className="join-voice" onClick={join}><Icon name="volume" /> Entrar na voz</button>',
        '<button className="join-voice" onClick={join} disabled={!secureAudio} aria-disabled={!secureAudio}><Icon name="volume" /> {secureAudio ? "Entrar na voz" : "Abra por HTTPS"}</button>'
    ),
    (
        '<span>{state === "online" ? "Áudio conectado" : state === "error" ? "Reconectando" : joined ? "Aguardando áudio" : "Fora da sala"}</span>',
        '<span>{!secureAudio ? "Voz bloqueada pelo HTTP" : state === "online" ? "Áudio conectado" : state === "error" ? "Reconectando" : joined ? "Aguardando áudio" : "Fora da sala"}</span>'
    ),
]

for old, new in replacements:
    if old not in text:
        raise SystemExit(f'voice v0.4.3 patch target not found: {old[:80]}')
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
