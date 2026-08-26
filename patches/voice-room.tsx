"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Avatar, Icon } from "./nexora-app";
import { getDeviceToken, supabase } from "./supabase-client";
import type { AudioPreferences, UserProfile } from "./settings-panel";

type Props = {
  roomName: string;
  roomId: string;
  profile: UserProfile;
  audio: AudioPreferences;
  onAudioChange: (audio: AudioPreferences) => void;
  onToast: (message: string) => void;
};
type Peer = { slot: number; name: string; avatar: string; color: string };
type Signal = { from: number; to: number; name: string; description?: RTCSessionDescriptionInit; candidate?: RTCIceCandidateInit };
type PresenceMeta = { slot: number; name: string; color?: string; online_at?: string };

const ICE_SERVERS: RTCIceServer[] = [
  { urls: "stun:stun.l.google.com:19302" },
  { urls: "stun:stun1.l.google.com:19302" },
];
const colorFor = (slot: number) => ["#ff304f", "#63d6ff", "#f58bd8"][Math.max(0, Math.min(2, slot - 1))];

export default function VoiceRoom({ roomName, roomId, profile, audio, onAudioChange, onToast }: Props) {
  const [joined, setJoined] = useState(false);
  const [muted, setMuted] = useState(false);
  const [deafened, setDeafened] = useState(false);
  const [talking, setTalking] = useState(false);
  const [state, setState] = useState<"idle" | "connecting" | "online" | "error">("idle");
  const [peers, setPeers] = useState<Record<number, Peer>>({});
  const [screen, setScreen] = useState<MediaStream | null>(null);
  const mic = useRef<MediaStream | null>(null);
  const channelRef = useRef<ReturnType<typeof supabase.channel> | null>(null);
  const pcs = useRef(new Map<number, RTCPeerConnection>());
  const remote = useRef(new Map<number, HTMLAudioElement>());
  const video = useRef<HTMLVideoElement | null>(null);
  const localSlotRef = useRef<number | null>(null);
  const localNameRef = useRef(profile.name);

  const cleanup = useCallback(() => {
    const channel = channelRef.current;
    channelRef.current = null;
    if (channel) void supabase.removeChannel(channel);
    pcs.current.forEach((pc) => pc.close());
    pcs.current.clear();
    mic.current?.getTracks().forEach((track) => track.stop());
    mic.current = null;
    remote.current.forEach((element) => { element.pause(); element.srcObject = null; });
    remote.current.clear();
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);
  useEffect(() => { const track = mic.current?.getAudioTracks()[0]; if (track) track.enabled = !muted && (audio.inputMode === "voice" || talking); }, [muted, audio.inputMode, talking]);
  useEffect(() => { remote.current.forEach((element) => { element.muted = deafened; }); }, [deafened]);
  useEffect(() => { if (video.current) video.current.srcObject = screen; }, [screen]);
  useEffect(() => {
    if (!joined || audio.inputMode !== "ptt") return;
    const down = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (target.matches("input, textarea") || target.isContentEditable) return;
      if (event.code === "KeyV" && !event.repeat) { event.preventDefault(); setTalking(true); }
    };
    const up = (event: KeyboardEvent) => { if (event.code === "KeyV") setTalking(false); };
    window.addEventListener("keydown", down); window.addEventListener("keyup", up);
    return () => { window.removeEventListener("keydown", down); window.removeEventListener("keyup", up); };
  }, [joined, audio.inputMode]);

  const join = async () => {
    if (joined) return;
    setJoined(true); setState("connecting"); setPeers({});
    try {
      const token = getDeviceToken();
      const { data: claimed, error: claimError } = await supabase.rpc("klyvro_claim_profile", { p_token: token });
      if (claimError) throw claimError;
      const identity = Array.isArray(claimed) ? claimed[0] : null;
      if (!identity) throw new Error("Perfil indisponível");
      const localSlot = Number(identity.slot);
      const localName = String(identity.display_name || profile.name || `Jogador ${localSlot}`);
      localSlotRef.current = localSlot;
      localNameRef.current = localName;

      try {
        const constraints: MediaTrackConstraints = {
          ...(audio.inputDeviceId !== "default" ? { deviceId: { exact: audio.inputDeviceId } } : {}),
          echoCancellation: audio.echoCancellation,
          noiseSuppression: audio.noiseSuppression,
          autoGainControl: audio.autoGainControl,
        };
        mic.current = await navigator.mediaDevices.getUserMedia({ audio: constraints });
      } catch {
        setMuted(true);
        onToast("Microfone bloqueado. Você entrou apenas para ouvir.");
      }

      const channel = supabase.channel(`klyvro-voice-${roomId}`, { config: { presence: { key: `slot-${localSlot}` }, broadcast: { ack: true, self: false } } });
      channelRef.current = channel;

      const sendSignal = async (signal: Signal) => {
        const result = await channel.send({ type: "broadcast", event: "webrtc-signal", payload: signal });
        if (result !== "ok") throw new Error("Falha na sinalização");
      };

      const ensurePeer = (remoteSlot: number, remoteName: string) => {
        const existing = pcs.current.get(remoteSlot);
        if (existing) return existing;
        const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
        pcs.current.set(remoteSlot, pc);
        mic.current?.getTracks().forEach((track) => pc.addTrack(track, mic.current!));
        pc.onicecandidate = (event) => {
          if (event.candidate) void sendSignal({ from: localSlot, to: remoteSlot, name: localName, candidate: event.candidate.toJSON() }).catch(() => onToast("Falha ao trocar dados da call."));
        };
        pc.ontrack = (event) => {
          const stream = event.streams[0] ?? new MediaStream([event.track]);
          let element = remote.current.get(remoteSlot);
          if (!element) { element = new Audio(); element.autoplay = true; remote.current.set(remoteSlot, element); }
          element.muted = deafened;
          element.srcObject = stream;
          void element.play().catch(() => onToast("Clique na página para liberar o áudio da call."));
        };
        pc.onconnectionstatechange = () => {
          if (pc.connectionState === "connected") setState("online");
          if (pc.connectionState === "failed") onToast(`A conexão de voz com ${remoteName} falhou. A rede pode exigir TURN.`);
        };
        return pc;
      };

      const maybeOffer = async (remoteSlot: number, remoteName: string) => {
        if (remoteSlot === localSlot || localSlot > remoteSlot) return;
        const pc = ensurePeer(remoteSlot, remoteName);
        if (pc.signalingState !== "stable" || pc.localDescription) return;
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        await sendSignal({ from: localSlot, to: remoteSlot, name: localName, description: offer });
      };

      const syncPresence = () => {
        const stateMap = channel.presenceState<PresenceMeta>();
        const next: Record<number, Peer> = {};
        for (const entries of Object.values(stateMap)) {
          for (const entry of entries) {
            const slot = Number(entry.slot);
            if (!slot || slot === localSlot) continue;
            const name = String(entry.name || `Jogador ${slot}`).slice(0, 24);
            next[slot] = { slot, name, avatar: (name[0] || "J").toUpperCase(), color: entry.color || colorFor(slot) };
            void maybeOffer(slot, name).catch(() => onToast(`Falha ao iniciar áudio com ${name}.`));
          }
        }
        setPeers(next);
        for (const [slot, pc] of pcs.current) if (!next[slot]) { pc.close(); pcs.current.delete(slot); const element = remote.current.get(slot); if (element) { element.pause(); element.srcObject = null; remote.current.delete(slot); } }
      };

      channel
        .on("presence", { event: "sync" }, syncPresence)
        .on("presence", { event: "join" }, syncPresence)
        .on("presence", { event: "leave" }, syncPresence)
        .on("broadcast", { event: "webrtc-signal" }, async ({ payload }) => {
          const signal = payload as Signal;
          if (!signal || Number(signal.to) !== localSlot || Number(signal.from) === localSlot) return;
          const remoteSlot = Number(signal.from);
          const remoteName = String(signal.name || `Jogador ${remoteSlot}`).slice(0, 24);
          const pc = ensurePeer(remoteSlot, remoteName);
          try {
            if (signal.description) {
              await pc.setRemoteDescription(signal.description);
              if (signal.description.type === "offer") {
                const answer = await pc.createAnswer();
                await pc.setLocalDescription(answer);
                await sendSignal({ from: localSlot, to: remoteSlot, name: localName, description: answer });
              }
            } else if (signal.candidate) await pc.addIceCandidate(signal.candidate);
          } catch { onToast(`Erro ao negociar a call com ${remoteName}.`); }
        })
        .subscribe(async (status) => {
          if (status === "SUBSCRIBED") {
            await channel.track({ slot: localSlot, name: localName, color: colorFor(localSlot), online_at: new Date().toISOString() });
            setState("online"); syncPresence(); onToast(`Conectado à sala ${roomName}`);
          } else if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") { setState("error"); onToast("Falha ao conectar à sala de voz."); }
        });
    } catch (error) {
      console.error("Klyvro voice join failed", error);
      cleanup(); setJoined(false); setState("error"); onToast("Falha ao entrar na call.");
    }
  };

  const leave = () => { cleanup(); setJoined(false); setPeers({}); setState("idle"); screen?.getTracks().forEach((track) => track.stop()); setScreen(null); onToast("Você saiu da sala de voz"); };
  const shareScreen = async () => { if (!joined) return; try { const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false }); stream.getVideoTracks()[0].onended = () => setScreen(null); setScreen(stream); onToast("Prévia local da tela iniciada"); } catch { onToast("Compartilhamento cancelado"); } };
  const stopScreen = () => { screen?.getTracks().forEach((track) => track.stop()); setScreen(null); };
  const list = Object.values(peers);

  return <div className="voice-room">
    <div className="voice-hero"><div><span className="eyebrow"><Icon name="radio" size={14} /> VOZ • SUPABASE + WEBRTC</span><h1>{roomName}</h1><p>O Supabase encontra os jogadores no canal; o áudio usa WebRTC.</p></div><div className="latency-pill"><i /> {joined ? `${list.length + 1} NA SALA` : "PRONTO"}</div></div>
    <div className={`voice-stage ${screen ? "sharing" : ""}`}>
      {screen ? <div className="screen-card"><video ref={video} autoPlay muted playsInline /><div className="screen-label"><Icon name="monitor" size={16} /><span>Sua tela • prévia local</span><button onClick={stopScreen}>Encerrar</button></div></div> : null}
      <div className="voice-people">
        {list.map((peer) => <VoicePerson key={peer.slot} name={peer.name} detail="Conectado" avatar={peer.avatar} color={peer.color} />)}
        {joined && <VoicePerson name={localNameRef.current || profile.name} detail={muted ? "Silenciado" : audio.inputMode === "ptt" ? "Segure V para falar" : "Você"} avatar={(localNameRef.current[0] || profile.name[0] || "J").toUpperCase()} image={profile.photo} color={colorFor(localSlotRef.current ?? 1)} />}
        {!joined && <button className="empty-voice-slot" onClick={join}><Icon name="plus" /><span>Entrar na sala</span></button>}
        {joined && list.length === 0 && <div className="voice-empty-live"><Icon name="radio" size={18}/><strong>Só você por enquanto</strong><span>Quando outro dos 3 entrar neste canal, aparece aqui automaticamente.</span></div>}
      </div>
    </div>
    <div className="voice-controls">
      {!joined ? <button className="join-voice" onClick={join}><Icon name="volume" /> Entrar na voz</button> : <>
        <button className={`round-control ${muted ? "danger" : ""}`} onClick={() => setMuted((value) => !value)} aria-label="Alternar microfone"><Icon name="mic" /></button>
        <button className={`round-control ${deafened ? "danger" : ""}`} onClick={() => setDeafened((value) => !value)} aria-label="Alternar áudio"><Icon name="headphones" /></button>
        <div className="input-mode"><button className={audio.inputMode === "voice" ? "active" : ""} onClick={() => onAudioChange({ ...audio, inputMode: "voice" })}>Detecção de voz</button><button className={audio.inputMode === "ptt" ? "active" : ""} onClick={() => onAudioChange({ ...audio, inputMode: "ptt" })}>Push-to-talk <kbd>V</kbd></button></div>
        <button className="screen-control" onClick={screen ? stopScreen : shareScreen}><Icon name="monitor" /> {screen ? "Parar tela" : "Compartilhar tela"}</button>
        <button className="leave-voice" onClick={leave} aria-label="Sair da sala"><Icon name="x" /></button>
      </>}
    </div>
    <div className="voice-footer"><span><Icon name="shield" size={14} /> Sinalização central pelo Supabase</span><span>{state === "error" ? "Erro de conexão" : `${list.length} outro${list.length === 1 ? "" : "s"} conectado${list.length === 1 ? "" : "s"}`}</span></div>
  </div>;
}

function VoicePerson({ name, detail, avatar, image, color }: { name: string; detail: string; avatar: string; image?: string | null; color: string }) {
  return <div className="voice-person"><div className="voice-avatar-wrap"><Avatar label={avatar} image={image} color={color} /></div><strong>{name}</strong><span>{detail}</span></div>;
}
