"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Avatar, Icon } from "./nexora-app";
import type { AudioPreferences, UserProfile } from "./settings-panel";

type Props = {
  roomName: string;
  roomId: string;
  profile: UserProfile;
  audio: AudioPreferences;
  onAudioChange: (audio: AudioPreferences) => void;
  onToast: (message: string) => void;
};
type Peer = { name: string; avatar: string; color: string };
const CONFIG = { appId: "klyvro-public-p2p-v2" };
const colorFor = (id: string) => ["#63d6ff", "#f58bd8", "#ffb15c", "#ad94ff", "#83e58e"][Array.from(id).reduce((n,c)=>n+c.charCodeAt(0),0)%5];

export default function VoiceRoom({ roomName, roomId, profile, audio, onAudioChange, onToast }: Props) {
  const [joined, setJoined] = useState(false);
  const [muted, setMuted] = useState(false);
  const [deafened, setDeafened] = useState(false);
  const [talking, setTalking] = useState(false);
  const [state, setState] = useState<"idle"|"connecting"|"online"|"error">("idle");
  const [peers, setPeers] = useState<Record<string, Peer>>({});
  const [screen, setScreen] = useState<MediaStream|null>(null);
  const mic = useRef<MediaStream|null>(null);
  const roomLeave = useRef<(()=>void)|null>(null);
  const remote = useRef(new Map<string, HTMLAudioElement>());
  const video = useRef<HTMLVideoElement|null>(null);

  const cleanup = useCallback(() => {
    roomLeave.current?.(); roomLeave.current = null;
    mic.current?.getTracks().forEach(t=>t.stop()); mic.current=null;
    screen?.getTracks().forEach(t=>t.stop());
    remote.current.forEach(a=>{a.pause();a.srcObject=null;}); remote.current.clear();
  }, [screen]);
  useEffect(()=>()=>cleanup(),[cleanup]);
  useEffect(()=>{ const track=mic.current?.getAudioTracks()[0]; if(track) track.enabled=!muted && (audio.inputMode==="voice" || talking); },[muted,audio.inputMode,talking]);
  useEffect(()=>{ remote.current.forEach(a=>a.muted=deafened); },[deafened]);
  useEffect(()=>{ if(video.current) video.current.srcObject=screen; },[screen]);
  useEffect(()=>{
    if(!joined || audio.inputMode!=="ptt") return;
    const down=(e:KeyboardEvent)=>{const t=e.target as HTMLElement;if(e.code==="KeyV"&&!e.repeat&&!t.matches("input,textarea")&&!t.isContentEditable){e.preventDefault();setTalking(true)}};
    const up=(e:KeyboardEvent)=>{if(e.code==="KeyV")setTalking(false)};
    addEventListener("keydown",down);addEventListener("keyup",up);return()=>{removeEventListener("keydown",down);removeEventListener("keyup",up)};
  },[joined,audio.inputMode]);

  const join = async () => {
    if(joined) return;
    setJoined(true); setState("connecting"); setPeers({});
    try {
      mic.current=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:audio.echoCancellation,noiseSuppression:audio.noiseSuppression,autoGainControl:audio.autoGainControl}});
    } catch { setMuted(true); onToast("Microfone bloqueado. Você entrou apenas para ouvir."); }
    try {
      const { joinRoom } = await import("trystero");
      const room=joinRoom(CONFIG,`voice:${roomId}`,{onJoinError:()=>onToast("Um navegador não conseguiu fechar a conexão P2P. Tente outra rede.")});
      roomLeave.current=()=>room.leave();
      const names=room.makeAction<Peer>("profile-v2");
      const me:Peer={name:profile.name.trim().slice(0,24)||"Jogador",avatar:(profile.name[0]||"J").toUpperCase(),color:"#ff304f"};
      names.onMessage=(value,{peerId})=>{if(value&&typeof value.name==="string")setPeers(p=>({...p,[peerId]:{name:value.name.slice(0,24),avatar:value.avatar||"J",color:value.color||colorFor(peerId)}}))};
      room.onPeerJoin=(peerId)=>{
        setPeers(p=>({...p,[peerId]:p[peerId]??{name:`Jogador ${peerId.slice(0,4)}`,avatar:"J",color:colorFor(peerId)}}));
        void names.send(me,{target:peerId});
        if(mic.current) room.addStream(mic.current,{target:peerId,metadata:{kind:"audio"}});
      };
      room.onPeerLeave=(peerId)=>{setPeers(p=>{const n={...p};delete n[peerId];return n});const a=remote.current.get(peerId);if(a){a.pause();a.srcObject=null;remote.current.delete(peerId)}};
      room.onPeerStream=(stream,peerId,metadata)=>{
        if(metadata&&typeof metadata==="object"&&"kind" in metadata&&metadata.kind!=="audio")return;
        let a=remote.current.get(peerId);if(!a){a=new Audio();a.autoplay=true;remote.current.set(peerId,a)}
        a.muted=deafened;a.srcObject=stream;void a.play().catch(()=>onToast("Clique na página para liberar o áudio da call."));
      };
      setState("online"); onToast(`Conectado em ${roomName}.`);
    } catch { cleanup(); setJoined(false); setState("error"); onToast("Falha ao entrar na rede P2P da call."); }
  };
  const leave=()=>{cleanup();setJoined(false);setPeers({});setState("idle");setScreen(null);onToast("Você saiu da sala de voz")};
  const share=async()=>{if(!joined)return;try{const s=await navigator.mediaDevices.getDisplayMedia({video:true,audio:false});s.getVideoTracks()[0].onended=()=>setScreen(null);setScreen(s);onToast("Prévia local da tela iniciada.")}catch{onToast("Compartilhamento cancelado")}};
  const stopShare=()=>{screen?.getTracks().forEach(t=>t.stop());setScreen(null)};
  const list=Object.entries(peers);

  return <div className="voice-room">
    <div className="voice-hero"><div><span className="eyebrow"><Icon name="radio" size={14}/> VOZ • P2P</span><h1>{roomName}</h1><p>Entre no mesmo canal para conectar áudio diretamente entre os navegadores.</p></div><div className="latency-pill"><i/> {state==="online"?`${list.length+1} NA SALA`:state==="connecting"?"CONECTANDO":state==="error"?"ERRO":"PRONTO"}</div></div>
    <div className={`voice-stage ${screen?"sharing":""}`}>
      {screen&&<div className="screen-card"><video ref={video} autoPlay muted playsInline/><div className="screen-label"><Icon name="monitor" size={16}/><span>Sua tela • prévia local</span><button onClick={stopShare}>Encerrar</button></div></div>}
      <div className="voice-people">
        {list.map(([id,p])=><VoicePerson key={id} name={p.name} detail="Conectado via P2P" avatar={p.avatar} color={p.color}/>)}
        {joined&&<VoicePerson name={profile.name||"Você"} detail={muted?"Silenciado":audio.inputMode==="ptt"?"Segure V para falar":"Você"} avatar={(profile.name[0]||"J").toUpperCase()} image={profile.photo} color="#ff304f"/>}
        {!joined&&<button className="empty-voice-slot" onClick={join}><Icon name="plus"/><span>Entrar na sala</span></button>}
        {joined&&list.length===0&&<div className="voice-empty-live"><Icon name="radio" size={18}/><strong>Só você por enquanto</strong><span>Quando outro navegador conectar neste canal, ele aparece aqui.</span></div>}
      </div>
    </div>
    <div className="voice-controls">
      {!joined?<button className="join-voice" onClick={join}><Icon name="volume"/> Entrar na voz</button>:<>
        <button className={`round-control ${muted?"danger":""}`} onClick={()=>setMuted(v=>!v)} aria-label="Alternar microfone"><Icon name="mic"/></button>
        <button className={`round-control ${deafened?"danger":""}`} onClick={()=>setDeafened(v=>!v)} aria-label="Alternar áudio"><Icon name="headphones"/></button>
        <div className="input-mode"><button className={audio.inputMode==="voice"?"active":""} onClick={()=>onAudioChange({...audio,inputMode:"voice"})}>Detecção de voz</button><button className={audio.inputMode==="ptt"?"active":""} onClick={()=>onAudioChange({...audio,inputMode:"ptt"})}>Push-to-talk <kbd>V</kbd></button></div>
        <button className="screen-control" onClick={screen?stopShare:share}><Icon name="monitor"/> {screen?"Parar tela":"Compartilhar tela"}</button>
        <button className="leave-voice" onClick={leave} aria-label="Sair da sala"><Icon name="x"/></button>
      </>}
    </div>
    <div className="voice-footer"><span><Icon name="shield" size={14}/> WebRTC entre navegadores</span><span>{list.length} outro{list.length===1?"":"s"} conectado{list.length===1?"":"s"}</span></div>
  </div>;
}

function VoicePerson({name,detail,avatar,image,color}:{name:string;detail:string;avatar:string;image?:string|null;color:string}){
  return <div className="voice-person"><div className="voice-avatar-wrap"><Avatar label={avatar} image={image} color={color}/></div><strong>{name}</strong><span>{detail}</span></div>;
}
