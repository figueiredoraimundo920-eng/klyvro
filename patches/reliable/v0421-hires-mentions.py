from pathlib import Path
import re

ROOT = Path('.')


def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.21 expected one target, found {count}: {old[:220]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


# Release metadata. The v0.4.20 visual pass was CSS-only, so the executable
# source arriving here still carries 0.4.19 metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.19";', 'const KLYVRO_BUILD = "0.4.21";')
once('package.json', '"version": "0.4.19"', '"version": "0.4.21"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.19', 'VOZ • CORE v0.4.21')

# ---------------------------------------------------------------------------
# Screen sharing: request the highest practical browser capture profile and
# give every negotiated sender a generous bitrate ceiling. WebRTC congestion
# control remains in charge, so slower links can still adapt down instead of
# being forced to sustain 4K/60.
# ---------------------------------------------------------------------------
voice = ROOT / 'app/voice-room.tsx'
voice_text = voice.read_text(encoding='utf-8')

old_fps = 'frameRate: { ideal: 30, max: 30 }'
if voice_text.count(old_fps) != 1:
    raise SystemExit(f'app/voice-room.tsx: expected one 30 FPS capture target, found {voice_text.count(old_fps)}')
voice_text = voice_text.replace(
    old_fps,
    'width: { ideal: 3840, max: 3840 }, height: { ideal: 2160, max: 2160 }, frameRate: { ideal: 60, max: 60 }',
    1,
)

voice_anchor = 'export default function VoiceRoom('
if voice_text.count(voice_anchor) != 1:
    raise SystemExit('app/voice-room.tsx: VoiceRoom export anchor missing')
quality_helper = r'''const SCREEN_MAX_BITRATE = 24_000_000;
const SCREEN_MAX_FPS = 60;

async function tuneScreenSender(sender: RTCRtpSender) {
  try {
    const parameters = sender.getParameters();
    if (!parameters.encodings || parameters.encodings.length === 0) parameters.encodings = [{}];
    for (const encoding of parameters.encodings) {
      encoding.maxBitrate = SCREEN_MAX_BITRATE;
      encoding.maxFramerate = SCREEN_MAX_FPS;
      encoding.scaleResolutionDownBy = 1;
    }
    const tuned = parameters as RTCRtpSendParameters & { degradationPreference?: "maintain-resolution" };
    tuned.degradationPreference = "maintain-resolution";
    await sender.setParameters(tuned);
  } catch (error) {
    console.warn("Klyvro could not apply the full screen quality ceiling", error);
  }
}

'''
voice_text = voice_text.replace(voice_anchor, quality_helper + voice_anchor, 1)

track_anchor = 'const track = stream.getVideoTracks()[0];'
if voice_text.count(track_anchor) != 1:
    raise SystemExit(f'app/voice-room.tsx: expected one captured screen track, found {voice_text.count(track_anchor)}')
voice_text = voice_text.replace(
    track_anchor,
    '''const track = stream.getVideoTracks()[0];
      const capturedSettings = track.getSettings();
      if ("contentHint" in track) track.contentHint = (capturedSettings.frameRate ?? 0) >= 50 ? "motion" : "detail";''',
    1,
)

replace_anchor = 'await replaceScreenTrackForPeers(track);'
if voice_text.count(replace_anchor) != 1:
    raise SystemExit(f'app/voice-room.tsx: expected one screen sender fanout, found {voice_text.count(replace_anchor)}')
voice_text = voice_text.replace(
    replace_anchor,
    '''await replaceScreenTrackForPeers(track);
      await Promise.allSettled([...screenSenders.current.values()].map((sender) => tuneScreenSender(sender)));''',
    1,
)

late_peer_anchor = 'if (activeTrack) void negotiated.sender.replaceTrack(activeTrack).catch(() => undefined);'
if voice_text.count(late_peer_anchor) != 1:
    raise SystemExit(f'app/voice-room.tsx: expected one late-peer screen sender bind, found {voice_text.count(late_peer_anchor)}')
voice_text = voice_text.replace(
    late_peer_anchor,
    'if (activeTrack) void negotiated.sender.replaceTrack(activeTrack).then(() => tuneScreenSender(negotiated.sender)).catch(() => undefined);',
    1,
)

old_toast = 'onToast("Sua tela agora está sendo transmitida para a call");'
if voice_text.count(old_toast) == 1:
    voice_text = voice_text.replace(old_toast, 'onToast("Sua tela agora está sendo transmitida para a call • até 4K/60 FPS quando a rede permitir");', 1)

voice.write_text(voice_text, encoding='utf-8')

# ---------------------------------------------------------------------------
# Mentions: @everyone + live profile display names. No backend schema change is
# required; mentions remain normal message text, while the client adds
# autocomplete, rendering, and personal highlighting.
# ---------------------------------------------------------------------------
app = ROOT / 'app/nexora-app.tsx'
app_text = app.read_text(encoding='utf-8')

avatar_anchor = 'export function Avatar('
if app_text.count(avatar_anchor) != 1:
    raise SystemExit('app/nexora-app.tsx: Avatar anchor missing')
mention_helpers = r'''const escapeMentionRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const mentionTargets = (names: string[]) => [...new Set(["everyone", ...names.map((name) => name.trim()).filter(Boolean)])].sort((a, b) => b.length - a.length);
const messageMentions = (text: string, name: string) => {
  const targets = mentionTargets(name.trim() ? [name] : []);
  const pattern = new RegExp(`(^|\\s)@(?:${targets.map(escapeMentionRegExp).join("|")})(?=$|[\\s.,!?;:])`, "i");
  return pattern.test(text);
};

function MentionText({ text, names }: { text: string; names: string[] }) {
  const targets = mentionTargets(names);
  const lookup = new Set(targets.map((name) => name.toLocaleLowerCase("pt-BR")));
  if (!targets.length) return <>{text}</>;
  const pattern = new RegExp(`(@(?:${targets.map(escapeMentionRegExp).join("|")}))(?=$|[\\s.,!?;:])`, "gi");
  return <>{text.split(pattern).map((part, index) => {
    if (!part.startsWith("@") || !lookup.has(part.slice(1).toLocaleLowerCase("pt-BR"))) return part;
    const everyone = part.slice(1).toLocaleLowerCase("pt-BR") === "everyone";
    return <mark key={`${part}-${index}`} className={`message-mention ${everyone ? "everyone" : "person"}`}>{part}</mark>;
  })}</>;
}

'''
app_text = app_text.replace(avatar_anchor, mention_helpers + avatar_anchor, 1)

old_message_signature = 'function MessageItem({ message, onReply, onReact }: { message: Message; onReply: () => void; onReact: (emoji: string) => void }) {'
new_message_signature = 'function MessageItem({ message, onReply, onReact, mentionNames, highlighted }: { message: Message; onReply: () => void; onReact: (emoji: string) => void; mentionNames: string[]; highlighted?: boolean }) {'
if app_text.count(old_message_signature) != 1:
    raise SystemExit(f'app/nexora-app.tsx: expected one MessageItem signature, found {app_text.count(old_message_signature)}')
app_text = app_text.replace(old_message_signature, new_message_signature, 1)

article_anchor = 'return <article className="message-row">'
if app_text.count(article_anchor) != 1:
    raise SystemExit(f'app/nexora-app.tsx: expected one MessageItem article, found {app_text.count(article_anchor)}')
app_text = app_text.replace(article_anchor, 'return <article className={`message-row ${highlighted ? "message-mentioned" : ""}`}>', 1)

text_anchor = '<p>{message.text}</p>'
if app_text.count(text_anchor) != 1:
    raise SystemExit(f'app/nexora-app.tsx: expected one raw message paragraph, found {app_text.count(text_anchor)}')
app_text = app_text.replace(text_anchor, '<p><MentionText text={message.text} names={mentionNames} /></p>', 1)

set_draft_anchor = '  const setDraft = (value: string) => setDrafts((current) => ({ ...current, [selected]: value.slice(0, MAX_MESSAGE_LENGTH) }));'
if app_text.count(set_draft_anchor) != 1:
    raise SystemExit('app/nexora-app.tsx: setDraft anchor missing')
mention_state = r'''  const setDraft = (value: string) => setDrafts((current) => ({ ...current, [selected]: value.slice(0, MAX_MESSAGE_LENGTH) }));
  const mentionNames = profileRows.map((row) => row.display_name.trim()).filter(Boolean);
  const mentionMatch = draft.match(/(?:^|\s)@([^\s@]*)$/);
  const mentionQuery = (mentionMatch?.[1] ?? "").toLocaleLowerCase("pt-BR");
  const mentionOptions = mentionMatch ? [
    { slot: 0, display_name: "everyone", avatar_color: "#ff3d63", avatar_data: null as string | null, everyone: true },
    ...profileRows.filter((row) => row.display_name.toLocaleLowerCase("pt-BR") !== "everyone").map((row) => ({ ...row, everyone: false })),
  ].filter((row) => row.display_name.toLocaleLowerCase("pt-BR").startsWith(mentionQuery)).slice(0, 6) : [];
  const insertMention = (name: string) => {
    setDraft(draft.replace(/@([^\s@]*)$/, `@${name} `));
    window.setTimeout(() => {
      const field = composerRef.current;
      if (!field) return;
      field.focus();
      field.setSelectionRange(field.value.length, field.value.length);
    }, 0);
  };'''
app_text = app_text.replace(set_draft_anchor, mention_state, 1)

message_map_pattern = re.compile(r'<MessageItem key=\{message\.id\} message=\{message\} onReply=\{\(\) => setReplying\(message\.author\)\} onReact=\{\(emoji\) => react\(message\.id, emoji\)\} />')
app_text, map_count = message_map_pattern.subn('<MessageItem key={message.id} message={message} mentionNames={mentionNames} highlighted={messageMentions(message.text, profile.name)} onReply={() => setReplying(message.author)} onReact={(emoji) => react(message.id, emoji)} />', app_text, count=1)
if map_count != 1:
    raise SystemExit(f'app/nexora-app.tsx: expected one current message map, found {map_count}')

form_anchor = '              <form className="composer" onSubmit={sendMessage}>'
if app_text.count(form_anchor) != 1:
    raise SystemExit(f'app/nexora-app.tsx: expected one composer form, found {app_text.count(form_anchor)}')
mention_popover = r'''              {mentionOptions.length > 0 && <div className="mention-popover" role="listbox" aria-label="Sugestões de menção">{mentionOptions.map((option) => <button type="button" role="option" key={option.slot || "everyone"} onMouseDown={(event) => event.preventDefault()} onClick={() => insertMention(option.display_name)}>{option.everyone ? <span className="mention-everyone-icon"><Icon name="users" size={16} /></span> : <Avatar label={(option.display_name[0] || "J").toUpperCase()} image={option.avatar_data} color={option.avatar_color} small />}<span><strong>@{option.display_name}</strong><small>{option.everyone ? "Mencionar todos" : "Mencionar pessoa"}</small></span></button>)}</div>}
              <form className="composer" onSubmit={sendMessage}>'''
app_text = app_text.replace(form_anchor, mention_popover, 1)

help_anchor = 'Enter para enviar • Shift+Enter para nova linha • rascunho local'
if app_text.count(help_anchor) == 1:
    app_text = app_text.replace(help_anchor, 'Enter para enviar • Shift+Enter para nova linha • @ para mencionar', 1)

app.write_text(app_text, encoding='utf-8')

# Mention styling extends the premium v0.4.20 visual system.
css = ROOT / 'app/globals.css'
css_text = css.read_text(encoding='utf-8')
marker = '/* Klyvro v0.4.21 mentions + hi-res share */'
if marker not in css_text:
    css_text += r'''

/* Klyvro v0.4.21 mentions + hi-res share */
.composer-wrap{position:relative}
.mention-popover{position:absolute;z-index:40;left:14px;right:14px;bottom:calc(100% - 2px);max-height:280px;overflow:auto;padding:7px;border:1px solid rgba(255,255,255,.1);border-radius:14px;background:#0d1118;box-shadow:0 20px 54px rgba(0,0,0,.42)}
.mention-popover button{width:100%;min-height:48px;padding:7px 9px;border:0;border-radius:10px;background:transparent;color:#dfe4eb;display:flex;align-items:center;gap:10px;text-align:left}
.mention-popover button:hover,.mention-popover button:focus-visible{background:rgba(255,61,99,.09);outline:none}
.mention-popover button>span:last-child{min-width:0;display:flex;flex-direction:column;gap:2px}.mention-popover strong{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.mention-popover small{font-size:9px;color:#788496}
.mention-everyone-icon{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;background:rgba(255,61,99,.13);color:#ff6681;border:1px solid rgba(255,61,99,.18)}
.message-mention{padding:1px 4px;border-radius:5px;background:rgba(105,217,255,.11);color:#8ee4ff;font-weight:750}
.message-mention.everyone{background:rgba(255,61,99,.13);color:#ff7890}
.message-mentioned{background:linear-gradient(90deg,rgba(255,61,99,.075),rgba(255,61,99,.018) 60%,transparent);border-color:rgba(255,61,99,.1)}
.message-mentioned:hover{background:linear-gradient(90deg,rgba(255,61,99,.095),rgba(255,61,99,.028) 65%,rgba(255,255,255,.015));border-color:rgba(255,61,99,.15)}
@media(max-width:650px){.mention-popover{left:8px;right:8px}}
'''
    css.write_text(css_text, encoding='utf-8')

print('Klyvro v0.4.21 hi-res screen share + @everyone/@person mentions patch applied')
