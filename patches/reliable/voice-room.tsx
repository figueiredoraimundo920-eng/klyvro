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

type Peer = { slot: number; name: string; avatar: string; color: string; connected: boolean };
type ProfileRow = { slot: number; display_name: string; avatar_color: string };
type PresenceRow = { slot: number; voice_room: string | null; voice_seen: string | null };
type SignalRow = { id: number; from_slot: number; kind: "description" | "candidate"; payload: RTCSessionDescriptionInit | RTCIceCandidateInit; created_at: string };

const ICE_SERVERS: RTCIceServer[] = [
  { urls: "stun:stun.l.google.com:19302" },
  { urls: "stun:stun1.l.google.com:19302" },
  { urls: "stun:stun.cloudflare.com:3478" },
];
const colorFor = (slot: number) => ["#ff304f", "#63d6ff", "#f58bd8"][Math.max(0, Math.min(2, slot - 1))] ?? "#ff304f";

export default function VoiceRoom({ roomName, roomId, profile, audio, onAudioChange, onToast }: Props) {
  const [joined, setJoined] = useState(false);
  const [muted, setMuted] = useState(false);
  const [deafened, setDeafened] = useState(false);
  const [talking, setTalking] = useState(false);
  const [state, setState] = useState<"idle" | "connecting" | "waiting" | "online" | "error">("idle");
  const [peers, setPeers] = useState<Record<number, Peer>>({});
  const [screen, setScreen] = useState<MediaStream | null>(null);

  const mic = useRef<MediaStream | null>(null);
  const screenRef = useRef<MediaStream | null>(null);
  const pcs = useRef(new Map<number, RTCPeerConnection>());
  const remoteAudio = useRef(new Map<number, HTMLAudioElement>());
  const pendingCandidates = useRef(new Map<number, RTCIceCandidateInit[]>());
  const offerStarted = useRef(new Set<number>());
  const timers = useRef<number[]>([]);
  const video = useRef<HTMLVideoElement | null>(null);
  const localSlotRef = useRef<number | null>(null);
  const localNameRef = useRef(profile.name);
  const tokenRef = useRef<string | null>(null);
  const lastSignalIdRef = useRef(0);
  const profilesRef = useRef<Record<number, ProfileRow>>({});
  const joinedAtRef = useRef(0);

  const clearTimers = () => {
    for (const timer of timers.current) window.clearInterval(timer);
    timers.current = [];
  };

  const cleanup = useCallback(() => {
    clearTimers();
    const token = tokenRef.current;
    if (token && localSlotRef.current) void supabase.rpc("klyvro_leave_voice", { p_token: token });
    pcs.current.forEach((pc) => pc.close());
    pcs.current.clear();
    pendingCandidates.current.clear();
    offerStarted.current.clear();
    mic.current?.getTracks().forEach((track) => track.stop());
    mic.current = null;
    screenRef.current?.getTracks().forEach((track) => track.stop());
    screenRef.current = null;
    remoteAudio.current.forEach((element) => { element.pause(); element.srcObject = null; });
    remoteAudio.current.clear();
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);
  useEffect(() => {
    const track = mic.current?.getAudioTracks()[0];
    if (track) track.enabled = !muted && (audio.inputMode === "voice" || talking);
  }, [muted, audio.inputMode, talking]);
  useEffect(() => { remoteAudio.current.forEach((element) => { element.muted = deafened; }); }, [deafened]);
  useEffect(() => { if (video.current) video.current.srcObject = screen; }, [screen]);
  useEffect(() => {
    if (!joined || audio.inputMode !== "ptt") return;
    const down = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (target.matches("input, textarea") || target.isContentEditable) return;
      if (event.code === "KeyV" && !event.repeat) { event.preventDefault(); setTalking(true); }
    };
    const up = (event: KeyboardEvent) => { if (event.code === "KeyV") setTalking(false); };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    return () => { window.removeEventListener("keydown", down); window.removeEventListener("keyup", up); };
  }, [joined, audio.inputMode]);

  const join = async () => {
    if (joined) return;
    setJoined(true);
    setState("connecting");
    setPeers({});
    lastSignalIdRef.current = 0;
    joinedAtRef.current = Date.now();

    try {
      const token = getDeviceToken();
      tokenRef.current = token;
      const { data: claimed, error: claimError } = await supabase.rpc("klyvro_claim_profile", { p_token: token });
      if (claimError) throw claimError;
      const identity = Array.isArray(claimed) ? claimed[0] : null;
      if (!identity) throw new Error("Perfil indisponível");
      const localSlot = Number(identity.slot);
      const localName = String(identity.display_name || profile.name || `Jogador ${localSlot}`).slice(0, 24);
      localSlotRef.current = localSlot;
      localNameRef.current = localName;

      const { data: profileRows, error: profileError } = await supabase.from("klyvro_profiles").select("slot,display_name,avatar_color").order("slot");
      if (profileError) throw profileError;
      profilesRef.current = Object.fromEntries(((profileRows ?? []) as ProfileRow[]).map((row) => [Number(row.slot), row]));

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
        onToast("Microfone bloqueado. Você entrou para ouvir.");
      }

      const sendSignal = async (remoteSlot: number, kind: "description" | "candidate", payload: RTCSessionDescriptionInit | RTCIceCandidateInit) => {
        const { error } = await supabase.rpc("klyvro_send_voice_signal", {
          p_token: token,
          p_room_id: roomId,
          p_to_slot: remoteSlot,
          p_kind: kind,
          p_payload: payload,
        });
        if (error) throw error;
      };

      const flushCandidates = async (remoteSlot: number, pc: RTCPeerConnection) => {
        if (!pc.remoteDescription) return;
        const queued = pendingCandidates.current.get(remoteSlot) ?? [];
        pendingCandidates.current.delete(remoteSlot);
        for (const candidate of queued) await pc.addIceCandidate(candidate).catch(() => undefined);
      };

      const ensurePeer = (remoteSlot: number, remoteName: string) => {
        const existing = pcs.current.get(remoteSlot);
        if (existing) return existing;
        const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS, iceCandidatePoolSize: 4 });
        pcs.current.set(remoteSlot, pc);
        const tracks = mic.current?.getTracks() ?? [];
        if (tracks.length) tracks.forEach((track) => pc.addTrack(track, mic.current!));
        else pc.addTransceiver("audio", { direction: "recvonly" });

        pc.onicecandidate = (event) => {
          if (event.candidate) void sendSignal(remoteSlot, "candidate", event.candidate.toJSON()).catch(() => onToast("Falha ao trocar rota de áudio."));
        };
        pc.ontrack = (event) => {
          const stream = event.streams[0] ?? new MediaStream([event.track]);
          let element = remoteAudio.current.get(remoteSlot);
          if (!element) {
            element = new Audio();
            element.autoplay = true;
            remoteAudio.current.set(remoteSlot, element);
          }
          element.muted = deafened;
          element.srcObject = stream;
          void element.play().catch(() => onToast("Clique uma vez na página para liberar o áudio."));
        };
        pc.onconnectionstatechange = () => {
          const connected = pc.connectionState === "connected";
          setPeers((current) => current[remoteSlot] ? { ...current, [remoteSlot]: { ...current[remoteSlot], connected } } : current);
          if (connected) setState("online");
          if (pc.connectionState === "failed") {
            setState("waiting");
            onToast(`Áudio com ${remoteName} não fechou. A rede pode exigir TURN.`);
          }
        };
        return pc;
      };

      const maybeOffer = async (remoteSlot: number, remoteName: string) => {
        if (localSlot >= remoteSlot || offerStarted.current.has(remoteSlot)) return;
        const pc = ensurePeer(remoteSlot, remoteName);
        if (pc.signalingState !== "stable") return;
        offerStarted.current.add(remoteSlot);
        try {
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          await sendSignal(remoteSlot, "description", offer);
        } catch (error) {
          offerStarted.current.delete(remoteSlot);
          throw error;
        }
      };

      const handleSignal = async (signal: SignalRow) => {
        if (new Date(signal.created_at).getTime() < joinedAtRef.current - 2000) return;
        const remoteSlot = Number(signal.from_slot);
        if (!remoteSlot || remoteSlot === localSlot) return;
        const row = profilesRef.current[remoteSlot];
        const remoteName = String(row?.display_name || `Jogador ${remoteSlot}`).slice(0, 24);
        const pc = ensurePeer(remoteSlot, remoteName);

        if (signal.kind === "candidate") {
          const candidate = signal.payload as RTCIceCandidateInit;
          if (pc.remoteDescription) await pc.addIceCandidate(candidate).catch(() => undefined);
          else pendingCandidates.current.set(remoteSlot, [...(pendingCandidates.current.get(remoteSlot) ?? []), candidate]);
          return;
        }

        const description = signal.payload as RTCSessionDescriptionInit;
        if (description.type === "offer") {
          if (pc.signalingState !== "stable" && pc.signalingState !== "have-remote-offer") return;
          await pc.setRemoteDescription(description);
          await flushCandidates(remoteSlot, pc);
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          await sendSignal(remoteSlot, "description", answer);
        } else if (description.type === "answer" && pc.signalingState === "have-local-offer") {
          await pc.setRemoteDescription(description);
          await flushCandidates(remoteSlot, pc);
        }
      };

      const voiceHeartbeat = async () => {
        const { error } = await supabase.rpc("klyvro_voice_heartbeat", { p_token: token, p_room_id: roomId });
        if (error) throw error;
      };

      const refreshPeers = async () => {
        const cutoff = new Date(Date.now() - 12_000).toISOString();
        const { data, error } = await supabase.from("klyvro_presence").select("slot,voice_room,voice_seen").eq("voice_room", roomId).gte("voice_seen", cutoff);
        if (error) throw error;
        const next: Record<number, Peer> = {};
        for (const entry of (data ?? []) as PresenceRow[]) {
          const slot = Number(entry.slot);
          if (!slot || slot === localSlot) continue;
          const row = profilesRef.current[slot];
          const name = String(row?.display_name || `Jogador ${slot}`).slice(0, 24);
          const pc = pcs.current.get(slot);
          next[slot] = { slot, name, avatar: (name[0] || "J").toUpperCase(), color: row?.avatar_color || colorFor(slot), connected: pc?.connectionState === "connected" };
          void maybeOffer(slot, name).catch(() => onToast(`Não consegui iniciar o áudio com ${name}.`));
        }
        setPeers(next);
        for (const [slot, pc] of pcs.current) {
          if (next[slot]) continue;
          pc.close();
          pcs.current.delete(slot);
          pendingCandidates.current.delete(slot);
          offerStarted.current.delete(slot);
          const element = remoteAudio.current.get(slot);
          if (element) { element.pause(); element.srcObject = null; remoteAudio.current.delete(slot); }
        }
        if (Object.keys(next).length === 0) setState("waiting");
      };

      const pollSignals = async () => {
        const { data, error } = await supabase.rpc("klyvro_poll_voice_signals", { p_token: token, p_room_id: roomId, p_after_id: lastSignalIdRef.current });
        if (error) throw error;
        for (const raw of (data ?? []) as SignalRow[]) {
          lastSignalIdRef.current = Math.max(lastSignalIdRef.current, Number(raw.id));
          await handleSignal(raw).catch(() => onToast("Erro ao negociar uma conexão de áudio."));
        }
      };

      await voiceHeartbeat();
      await refreshPeers();
      await pollSignals();
      setState("waiting");

      timers.current.push(window.setInterval(() => { void voiceHeartbeat().catch(() => setState("error")); }, 3000));
      timers.current.push(window.setInterval(() => { void refreshPeers().catch(() => setState("error")); }, 1000));
      timers.current.push(window.setInterval(() => { void pollSignals().catch(() => setState("error")); }, 400));
      onToast(`Você entrou em ${roomName}`);
    } catch (error) {
      console.error("Klyvro voice join failed", error);
      cleanup();
      setJoined(false);
      setState("error");
      onToast("Falha ao entrar na call.");
    }
  };

  const leave = () => {
    cleanup();
    setJoined(false);
    setPeers({});
    setState("idle");
    setScreen(null);
    onToast("Você saiu da sala de voz");
  };

  const shareScreen = async () => {
    if (!joined) return;
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
      screenRef.current = stream;
      stream.getVideoTracks()[0].onended = () => { screenRef.current = null; setScreen(null); };
      setScreen(stream);
      onToast("Prévia local da tela iniciada");
    } catch { onToast("Compartilhamento cancelado"); }
  };
  const stopScreen = () => {
    screenRef.current?.getTracks().forEach((track) => track.stop());
    screenRef.current = null;
    setScreen(null);
  };

  const list = Object.values(peers);
  const roomStatus = !joined ? "PRONTO" : state === "error" ? "RECONECTANDO" : `${list.length + 1} NA SALA`;

  return <div className="voice-room">
    <div className="voice-hero"><div><span className="eyebrow"><Icon name="radio" size={14} /> VOZ • CORE v0.4.1</span><h1>{roomName}</h1><p>O servidor mantém quem está na sala e negocia o WebRTC entre vocês.</p></div><div className="latency-pill"><i /> {roomStatus}</div></div>
    <div className={`voice-stage ${screen ? "sharing" : ""}`}>
      {screen ? <div className="screen-card"><video ref={video} autoPlay muted playsInline /><div className="screen-label"><Icon name="monitor" size={16} /><span>Sua tela • prévia local</span><button onClick={stopScreen}>Encerrar</button></div></div> : null}
      <div className="voice-people">
        {list.map((peer) => <VoicePerson key={peer.slot} name={peer.name} detail={peer.connected ? "Áudio conectado" : "Na sala • conectando áudio"} avatar={peer.avatar} color={peer.color} />)}
        {joined && <VoicePerson name={localNameRef.current || profile.name} detail={muted ? "Silenciado" : audio.inputMode === "ptt" ? "Segure V para falar" : "Você"} avatar={(localNameRef.current[0] || profile.name[0] || "J").toUpperCase()} image={profile.photo} color={colorFor(localSlotRef.current ?? 1)} />}
        {!joined && <button className="empty-voice-slot" onClick={join}><Icon name="plus" /><span>Entrar na sala</span></button>}
        {joined && list.length === 0 && <div className="voice-empty-live"><Icon name="radio" size={18}/><strong>Só você por enquanto</strong><span>Assim que outro usuário entrar neste mesmo canal ele aparece aqui, mesmo se o WebSocket estiver bloqueado.</span></div>}
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
    <div className="voice-footer"><span><Icon name="shield" size={14} /> Presença e sinalização pelo Supabase</span><span>{state === "online" ? "Áudio conectado" : state === "error" ? "Reconectando" : joined ? "Aguardando áudio" : "Fora da sala"}</span></div>
  </div>;
}

function VoicePerson({ name, detail, avatar, image, color }: { name: string; detail: string; avatar: string; image?: string | null; color: string }) {
  return <div className="voice-person"><div className="voice-avatar-wrap"><Avatar label={avatar} image={image} color={color} /></div><strong>{name}</strong><span>{detail}</span></div>;
}
