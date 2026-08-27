from pathlib import Path

ROOT = Path('.')


def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.20 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


# Visual-only release metadata. No call/chat data flow is changed here.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.19";', 'const KLYVRO_BUILD = "0.4.20";')
once('package.json', '"version": "0.4.19"', '"version": "0.4.20"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.19', 'VOZ • CORE v0.4.20')

css = ROOT / 'app/globals.css'
text = css.read_text(encoding='utf-8')
marker = '/* Klyvro v0.4.20 premium visual refresh */'
if marker in text:
    raise SystemExit('Klyvro v0.4.20 visual marker already present')

text += r'''

/* Klyvro v0.4.20 premium visual refresh */
:root{
  --bg:#06080c;
  --rail:#06070a;
  --sidebar:#0b0e14;
  --panel:#0e1219;
  --panel-2:#121720;
  --panel-3:#161c26;
  --line:rgba(255,255,255,.075);
  --accent:#ff3d63;
  --accent-soft:rgba(255,61,99,.11);
  --cyan:#69d9ff;
  --danger:#ff647a;
  --text:#f7f8fb;
  --muted:#9aa4b4;
  --muted-2:#707b8d;
  --k-surface:#10151d;
  --k-surface-2:#141a24;
  --k-surface-3:#1a212d;
  --k-border:rgba(255,255,255,.085);
  --k-border-strong:rgba(255,255,255,.13);
  --k-shadow:0 20px 55px rgba(0,0,0,.28);
  --k-accent-shadow:0 14px 34px rgba(255,61,99,.14);
}

html,body{background:#06080c}
body{
  background:
    radial-gradient(circle at 58% -12%,rgba(255,61,99,.075),transparent 34%),
    radial-gradient(circle at 92% 82%,rgba(105,217,255,.035),transparent 28%),
    #06080c;
  color:#f7f8fb;
  font-family:Inter,"Segoe UI Variable","Segoe UI",system-ui,-apple-system,BlinkMacSystemFont,sans-serif;
  text-rendering:optimizeLegibility;
}
::selection{background:rgba(255,61,99,.3);color:#fff}
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-thumb{background:#2a313e;border:2px solid transparent;background-clip:padding-box;border-radius:999px}
::-webkit-scrollbar-thumb:hover{background:#3a4352;border:2px solid transparent;background-clip:padding-box}

.app-shell{
  grid-template-columns:76px 286px minmax(0,1fr);
  background:linear-gradient(145deg,#06080c,#090c12 52%,#07090e);
}
.server-rail{
  padding:15px 11px;
  gap:11px;
  background:linear-gradient(180deg,#06070a 0%,#080a0f 100%);
  border-right:1px solid rgba(255,255,255,.065);
}
.brand-mark{
  width:48px;height:48px;border-radius:16px;
  background:linear-gradient(145deg,#ff5576 0%,#ff315b 46%,#b70e34 100%);
  color:white;
  border:1px solid rgba(255,255,255,.18);
  box-shadow:0 14px 32px rgba(255,48,79,.2),inset 0 1px rgba(255,255,255,.18);
}
.brand-mark span{transform:skew(-7deg) rotate(-2deg);text-shadow:0 2px 14px rgba(0,0,0,.25)}
.rail-divider{width:32px;background:rgba(255,255,255,.075)}
.server-orb{
  width:44px;height:44px;border-radius:15px;
  background:#121720;color:#8f99a8;
  border:1px solid rgba(255,255,255,.055);
  box-shadow:inset 0 1px rgba(255,255,255,.025);
}
.server-orb:hover{background:#191f2a;color:#fff;border-color:rgba(255,255,255,.1)}
.server-orb.active{
  color:#fff;border-radius:13px;
  background:linear-gradient(145deg,#ff466b,#d61b45);
  border-color:rgba(255,255,255,.12);
  box-shadow:0 10px 24px rgba(255,48,79,.16);
}
.server-orb.active:before{left:-13px;width:3px;height:25px;background:#ff4a6c;box-shadow:0 0 14px rgba(255,61,99,.35)}
.server-orb.add{color:#ff6480;border-color:rgba(255,61,99,.24);background:rgba(255,61,99,.035)}
.rail-performance{
  width:48px;border-radius:14px;
  border-color:rgba(255,61,99,.16);
  color:#ff6c86;background:rgba(255,61,99,.065);
}

.channel-sidebar{
  background:linear-gradient(180deg,#0b0e14,#0a0d13 70%,#080b10);
  border-right:1px solid rgba(255,255,255,.07);
}
.workspace-header{
  height:70px;padding:0 18px;
  border-bottom:1px solid rgba(255,255,255,.07);
  background:linear-gradient(180deg,rgba(255,255,255,.015),transparent);
}
.workspace-header span{color:#ff6681;letter-spacing:.18em}
.workspace-header strong{font-size:15.5px;letter-spacing:-.015em}
.workspace-header>button,.top-actions>button,.user-dock>button,.member-panel-title button{
  border:1px solid transparent;
  border-radius:10px;
}
.workspace-header>button:hover,.top-actions>button:hover,.user-dock>button:hover,.member-panel-title button:hover{
  border-color:rgba(255,255,255,.07);
  background:rgba(255,255,255,.05);
}
.quick-panel{
  margin:14px 13px 7px;padding:13px;
  border:1px solid rgba(255,61,99,.12);
  border-radius:14px;
  background:linear-gradient(135deg,rgba(255,61,99,.075),rgba(105,217,255,.022) 70%,rgba(255,255,255,.015));
  box-shadow:inset 0 1px rgba(255,255,255,.025);
}
.quick-copy span{color:#ff6681}.quick-copy strong{font-size:11.5px;color:#e6e9ef}
.switch{background:#262d39;border:1px solid rgba(255,255,255,.06)}
.switch.on{background:linear-gradient(90deg,#b8173b,#ff3d63);border-color:rgba(255,61,99,.28)}
.switch.on i{background:white;box-shadow:0 2px 8px rgba(0,0,0,.25)}
.channel-scroll{padding:10px 10px 12px}
.channel-group{margin-bottom:21px}
.channel-group h2{padding:0 8px 5px;color:#697487;font-size:8.5px;letter-spacing:.13em}
.channel{
  height:38px;padding:0 10px;border-radius:10px;
  color:#939dac;
  transition:background-color .14s ease,color .14s ease,border-color .14s ease,transform .14s ease;
}
.channel:hover{background:rgba(255,255,255,.04);color:#e4e7ec;transform:translateX(1px)}
.channel.active{
  color:#fff;
  background:linear-gradient(90deg,rgba(255,61,99,.14),rgba(255,61,99,.055) 72%,transparent);
  box-shadow:inset 0 0 0 1px rgba(255,61,99,.075);
}
.channel.active:before{left:0;width:3px;height:20px;background:#ff486b;box-shadow:0 0 12px rgba(255,61,99,.25)}
.channel-badge{background:#ff3d63;color:white;box-shadow:0 4px 12px rgba(255,61,99,.2)}
.voice-live-members{gap:5px;padding-top:5px;padding-bottom:9px}
.voice-live-members span{padding:3px 5px;border-radius:8px;color:#9da7b6}
.voice-live-members span:hover{background:rgba(255,255,255,.035);color:#dfe3e9}
.invite-card{
  border-color:rgba(255,255,255,.09);border-radius:13px;
  background:linear-gradient(135deg,rgba(255,255,255,.025),rgba(255,61,99,.02));
}
.invite-card:hover{border-color:rgba(255,61,99,.22);background:rgba(255,61,99,.055)}
.user-dock{
  min-height:64px;height:64px;padding:9px 11px;
  background:linear-gradient(180deg,#0b0e14,#080b10);
  border-top:1px solid rgba(255,255,255,.075);
}
.user-dock .avatar{box-shadow:0 0 0 2px #0b0e14,0 0 0 3px rgba(255,255,255,.07)}
.user-dock strong{font-size:11.5px}.user-dock span{color:#7f8999}

.content-area{background:#0e1219}
.topbar{
  height:70px;padding:0 19px;
  background:rgba(12,16,22,.965);
  border-bottom:1px solid rgba(255,255,255,.075);
  box-shadow:0 1px 0 rgba(0,0,0,.22);
}
.channel-title{gap:10px}.channel-title svg{color:#ff6681}.channel-title strong{font-size:14.5px;letter-spacing:-.01em}.channel-title span{color:#818b9b}
.top-actions{gap:6px}.top-actions>button{position:relative;color:#8f99a8}
.search-trigger{
  width:196px;height:36px!important;padding:0 10px!important;
  border:1px solid rgba(255,255,255,.07)!important;
  border-radius:11px!important;
  background:#090c11!important;
  color:#7c8798!important;
}
.search-trigger:hover{border-color:rgba(255,61,99,.14)!important;background:#0d1118!important}
.search-popover,.floating-panel,.notifications-popover,.pinned-drawer{
  border-color:rgba(255,255,255,.1);
  background:#0d1118;
  box-shadow:0 24px 70px rgba(0,0,0,.42),inset 0 1px rgba(255,255,255,.025);
}
.workspace-grid{grid-template-columns:minmax(0,1fr) 238px;background:#0c1016}
.chat-panel{
  background:
    radial-gradient(circle at 50% -20%,rgba(255,61,99,.035),transparent 36%),
    linear-gradient(180deg,#0e1219,#0c1016);
}
.performance-banner{
  min-height:38px;height:38px;padding:0 18px;
  border-bottom:1px solid rgba(255,255,255,.055);
  background:linear-gradient(90deg,rgba(255,61,99,.055),rgba(255,61,99,.012) 48%,transparent);
}
.performance-banner span{color:#ff6781}.performance-banner small{color:#7d8797}
.performance-banner>button{
  min-width:54px;height:25px;border-radius:8px;
  border:1px solid rgba(255,61,99,.13);
  background:rgba(255,61,99,.06);
  color:#ff7189;text-decoration:none;
}
.pulse-badges b{border-color:rgba(255,255,255,.07);background:rgba(255,255,255,.025);border-radius:7px}
.message-scroll{padding:16px 0 14px;scrollbar-gutter:stable}
.channel-welcome{
  margin:4px 18px 14px;padding:22px 23px;
  border:1px solid rgba(255,255,255,.07);
  border-radius:20px;
  background:
    linear-gradient(125deg,rgba(255,61,99,.085),rgba(255,61,99,.018) 43%,rgba(105,217,255,.018) 100%),
    #10151d;
  box-shadow:inset 0 1px rgba(255,255,255,.025),0 14px 36px rgba(0,0,0,.12);
}
.channel-welcome>div{
  width:50px;height:50px;border-radius:16px;
  color:white;background:linear-gradient(145deg,#ff5575,#d31945);
  box-shadow:0 12px 28px rgba(255,61,99,.16),inset 0 1px rgba(255,255,255,.14);
}
.channel-welcome h1{margin-top:14px;color:#fafbfc;font-size:clamp(23px,2.4vw,30px);letter-spacing:-.045em}
.channel-welcome p{max-width:640px;color:#9ca6b5;line-height:1.55}
.welcome-chips{gap:7px}.welcome-chips span{border-color:rgba(255,255,255,.07);background:rgba(255,255,255,.025);border-radius:8px;color:#9aa4b4}
.welcome-chips svg{color:#ff6681}
.date-divider{margin:8px 22px 6px;border-color:rgba(255,255,255,.065)}
.date-divider span{background:#0d1118;color:#717c8d;padding:0 11px;border-radius:999px}
.message-row{
  margin:1px 10px;padding:9px 13px;gap:12px;
  border:1px solid transparent;border-radius:12px;
  transition:background-color .12s ease,border-color .12s ease;
}
.message-row:hover{
  background:rgba(255,255,255,.026);
  border-color:rgba(255,255,255,.04);
}
.message-row>.avatar{margin-top:1px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.13),0 5px 14px rgba(0,0,0,.16)}
.message-body{min-width:0;flex:1}.message-meta strong{font-size:12.5px;color:#f0f2f5}.message-meta time{color:#737d8d;font-size:8.5px}
.message-body p{margin-top:4px;color:#d7dbe2;font-size:12.5px;line-height:1.62}
.reply-line{color:#818b9a}.reply-line b{color:#c8ced7}
.message-actions{right:12px;top:-14px;border-color:rgba(255,255,255,.09);border-radius:9px;background:#171c25;box-shadow:0 10px 24px rgba(0,0,0,.28)}
.message-actions button:hover{color:#ff6982;background:rgba(255,61,99,.07)}
.reactions button{border-color:rgba(255,255,255,.075);background:rgba(255,255,255,.025);border-radius:8px}.reactions button:hover{border-color:rgba(255,61,99,.16);background:rgba(255,61,99,.055)}
.composer-wrap{padding:9px 18px 16px}
.composer{
  min-height:50px;padding:5px 7px 5px 10px;gap:8px;
  border:1px solid rgba(255,255,255,.09);
  border-radius:16px;
  background:#141a23;
  box-shadow:0 12px 30px rgba(0,0,0,.18),inset 0 1px rgba(255,255,255,.025);
}
.composer:focus-within{border-color:rgba(255,61,99,.34);box-shadow:0 0 0 3px rgba(255,61,99,.055),0 12px 30px rgba(0,0,0,.18)}
.composer input,.composer textarea{color:#f1f3f6;font-size:12px;line-height:1.45}.composer input::placeholder,.composer textarea::placeholder{color:#727d8e}
.composer button{border-radius:9px}.composer button:hover{background:rgba(255,255,255,.045);color:#cdd3dc}
.composer .send-button{
  width:34px;height:34px;border-radius:10px;color:white;
  background:linear-gradient(145deg,#ff5172,#d91a46);
  box-shadow:0 8px 18px rgba(255,61,99,.18);
}
.composer .send-button:hover{background:linear-gradient(145deg,#ff6884,#e52751);transform:translateY(-1px)}
.composer-wrap>small{margin-left:5px;color:#687384}
.replying{border:1px solid rgba(255,255,255,.06);border-bottom:0;background:#10151d;color:#838d9c}.replying strong{color:#ff6a83}

.member-panel{
  padding:12px 10px;
  background:linear-gradient(180deg,#0b0f15,#090c11);
  border-left:1px solid rgba(255,255,255,.07);
}
.member-panel-title{padding:0 7px 10px;border-color:rgba(255,255,255,.065)}
.member-panel-title strong{font-size:12.5px;letter-spacing:-.01em}
.member-heading{height:31px;color:#707b8b;letter-spacing:.11em}
.member-row{padding:7px;border-radius:11px;gap:10px}
.member-row:hover{background:rgba(255,255,255,.04)}
.member-row strong{font-size:11px;color:#dce0e6}.member-row small{font-size:8.5px;color:#778292}
.member-row .avatar{box-shadow:inset 0 0 0 1px rgba(255,255,255,.12),0 4px 12px rgba(0,0,0,.12)}
.connection-card{
  margin-top:18px;padding:11px 12px;border-radius:12px;
  border-color:rgba(255,61,99,.11);
  background:linear-gradient(135deg,rgba(255,61,99,.055),rgba(255,255,255,.014));
}
.connection-card>div:first-child{color:#ff6681}

.voice-room{padding:clamp(20px,3vw,34px);background:radial-gradient(circle at 50% -10%,rgba(255,61,99,.04),transparent 34%)}
.voice-hero{align-items:center}.voice-hero h1{font-size:clamp(28px,4vw,44px);letter-spacing:-.055em}.voice-hero p{color:#929dad;font-size:11.5px;line-height:1.55}
.eyebrow{color:#ff6882}
.latency-pill{border-color:rgba(102,217,144,.17);background:rgba(102,217,144,.07);color:#d9e9df;border-radius:11px}.latency-pill span{color:#78dda0}
.voice-stage{
  margin:22px 0 18px;min-height:285px;border-radius:22px;
  border-color:rgba(255,255,255,.075);
  background:
    radial-gradient(circle at 50% 45%,rgba(255,61,99,.055),transparent 38%),
    linear-gradient(145deg,#0e131a,#0a0e14);
  box-shadow:inset 0 1px rgba(255,255,255,.02),0 18px 50px rgba(0,0,0,.13);
}
.voice-person{gap:8px}.voice-avatar-wrap{width:76px;height:76px;border-radius:25px;background:rgba(255,255,255,.022);border:1px solid rgba(255,255,255,.06)}
.voice-person.speaking .voice-avatar-wrap{border-color:rgba(255,61,99,.62);box-shadow:0 0 0 4px rgba(255,61,99,.07),0 0 28px rgba(255,61,99,.12)}
.voice-person .avatar{width:59px;height:59px;border-radius:19px}.voice-person strong{font-size:11.5px}.voice-person>span{color:#7f8998}
.voice-wave i{background:#ff5f7c}
.empty-voice-slot{border-radius:18px;border-color:rgba(255,255,255,.09);background:rgba(255,255,255,.012)}
.empty-voice-slot:hover{color:#ff6882;border-color:rgba(255,61,99,.24);background:rgba(255,61,99,.035)}
.voice-controls{gap:9px}
.join-voice{
  min-height:40px;border-radius:11px;color:white;
  background:linear-gradient(145deg,#ff5172,#d51a44);
  box-shadow:0 9px 20px rgba(255,61,99,.16);
}
.round-control,.leave-voice,.screen-control{height:40px;border-radius:11px;background:#171d27;border-color:rgba(255,255,255,.08)}
.round-control:hover,.screen-control:hover{background:#1d2531;border-color:rgba(255,255,255,.12);color:#fff}
.screen-control{color:#ff6b84;background:rgba(255,61,99,.055);border-color:rgba(255,61,99,.12)}
.input-mode{height:40px;border-radius:11px;background:#0d1218;border-color:rgba(255,255,255,.07)}.input-mode button{border-radius:8px}.input-mode button.active{background:#202734;color:#fff}
.voice-footer{border-color:rgba(255,255,255,.065);color:#707b8b}
.screen-card{margin:13px;border-radius:17px;border:1px solid rgba(255,255,255,.075);box-shadow:0 18px 46px rgba(0,0,0,.28)}
.screen-label{left:11px;right:11px;bottom:11px;padding:8px 10px;border-radius:11px;border-color:rgba(255,255,255,.1);background:rgba(8,11,16,.9)}
.screen-fullscreen-button{border-radius:8px!important;background:rgba(255,255,255,.07)!important;color:#e9edf2!important}
.voice-call-dock{
  border-color:rgba(255,61,99,.16);
  border-radius:16px;
  background:rgba(11,15,21,.97);
  box-shadow:0 18px 48px rgba(0,0,0,.34),inset 0 1px rgba(255,255,255,.025);
}
.voice-call-dock-copy span{color:#ff6681}.voice-call-dock-copy span i{background:#68dc95;box-shadow:0 0 9px rgba(104,220,149,.4)}
.voice-channel-preview{
  min-height:330px;border-radius:22px;
  border-color:rgba(255,255,255,.075);
  background:
    radial-gradient(circle at 12% 30%,rgba(255,61,99,.07),transparent 27%),
    linear-gradient(145deg,#11161f,#0c1016);
  box-shadow:inset 0 1px rgba(255,255,255,.025),0 18px 46px rgba(0,0,0,.14);
}
.voice-channel-preview-icon{width:58px;height:58px;border-radius:18px;color:#ff6a83;background:rgba(255,61,99,.07);border-color:rgba(255,61,99,.14)}
.voice-channel-preview-copy h1{font-size:29px;letter-spacing:-.04em}.voice-channel-preview-copy p{color:#929cac}
.voice-preview-members span{border-color:rgba(255,255,255,.075);background:rgba(255,255,255,.027);border-radius:999px}
.voice-preview-join{height:44px;border:0;border-radius:12px;color:white;background:linear-gradient(145deg,#ff5172,#d51a44);box-shadow:0 9px 20px rgba(255,61,99,.15)}

.lfg-board{background:radial-gradient(circle at 50% -10%,rgba(255,61,99,.035),transparent 32%)}
.lfg-header h1{letter-spacing:-.05em}.lfg-header p{color:#929cac}
.lfg-header>button,.create-submit,.party-card footer button,.primary-button{
  color:white;background:linear-gradient(145deg,#ff5172,#d51a44);box-shadow:0 8px 18px rgba(255,61,99,.12)
}
.lfg-filters{border-color:rgba(255,255,255,.065)}.lfg-filters button{border-radius:9px;background:#111720;border-color:rgba(255,255,255,.07)}.lfg-filters button.active{border-color:rgba(255,61,99,.18);background:rgba(255,61,99,.07);color:#ff6c85}
.party-grid{gap:12px}.party-card{border-radius:15px;border-color:rgba(255,255,255,.07);background:linear-gradient(145deg,#11161e,#0d1118)}.party-card:hover{border-color:rgba(255,61,99,.15);background:#131922;transform:translateY(-1px)}
.game-chip{background:rgba(255,61,99,.08);color:#ff6c85}.slots i.filled{background:#ff4a6b}.lfg-tip{border-color:rgba(255,61,99,.09);background:rgba(255,61,99,.035);color:#ff6681}

.preferences-backdrop,.modal-backdrop{background:rgba(2,4,7,.78)}
.preferences-modal,.settings-modal,.create-party{
  border-color:rgba(255,255,255,.095);border-radius:20px;
  background:#0e131a;box-shadow:0 34px 100px rgba(0,0,0,.55),inset 0 1px rgba(255,255,255,.025);
}
.preferences-nav,.settings-sidebar{background:#090d12;border-color:rgba(255,255,255,.065)}
.preferences-nav>button{border-radius:10px}.preferences-nav>button:hover{background:rgba(255,255,255,.04)}.preferences-nav>button.active{background:linear-gradient(90deg,rgba(255,61,99,.12),rgba(255,61,99,.04));color:#fff}
.settings-card{border-radius:15px;border-color:rgba(255,255,255,.075);background:#111720;box-shadow:inset 0 1px rgba(255,255,255,.02)}
.settings-card input[type=text],.settings-card>input,.settings-card select,.sample-player,.create-party input,.create-party select{border-radius:10px;background:#090d12;border-color:rgba(255,255,255,.075)}
.settings-card input:focus,.settings-card select:focus,.create-party input:focus,.create-party select:focus{border-color:rgba(255,61,99,.32);box-shadow:0 0 0 3px rgba(255,61,99,.045)}
.profile-preview{border-radius:16px;border-color:rgba(255,61,99,.13);background:linear-gradient(135deg,rgba(255,61,99,.065),rgba(255,255,255,.015))}
.secondary-button,.ghost-button{border-radius:10px;border-color:rgba(255,255,255,.09);background:rgba(255,255,255,.025)}
.secondary-button:hover,.ghost-button:hover{border-color:rgba(255,61,99,.16);background:rgba(255,61,99,.045)}
.privacy-note{border-radius:12px;background:rgba(255,61,99,.045);color:#ff6a83}
.toast{
  bottom:26px;padding:11px 15px;border-radius:12px;
  border-color:rgba(255,61,99,.18);background:#151017;color:#f3e9ec;
  box-shadow:0 18px 48px rgba(0,0,0,.38),inset 0 1px rgba(255,255,255,.03);
}

.avatar{overflow:visible}.avatar-picture{border-radius:inherit;box-shadow:inset 0 0 0 1px rgba(255,255,255,.1)}
.presence{border-color:#0d1219;box-shadow:0 0 0 1px rgba(0,0,0,.18)}

@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{scroll-behavior:auto!important;animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}
}

.performance-mode .topbar,
.performance-mode .screen-label,
.performance-mode .voice-call-dock,
.performance-mode .floating-panel,
.performance-mode .notifications-popover,
.performance-mode .pinned-drawer{backdrop-filter:none!important}
.performance-mode .brand-mark,
.performance-mode .server-orb.active,
.performance-mode .channel-welcome,
.performance-mode .voice-stage,
.performance-mode .voice-call-dock,
.performance-mode .screen-card,
.performance-mode .composer,
.performance-mode .toast{box-shadow:none}
.performance-mode .channel:hover,
.performance-mode .party-card:hover,
.performance-mode .composer .send-button:hover{transform:none}

@media(max-width:1180px){
  .app-shell{grid-template-columns:72px 270px minmax(0,1fr)}
  .workspace-grid{grid-template-columns:minmax(0,1fr) 220px}
}
@media(max-width:900px){
  .app-shell{grid-template-columns:68px 255px minmax(0,1fr)}
  .search-trigger{width:150px}
  .channel-welcome{margin-left:13px;margin-right:13px}
}
@media(max-width:760px){
  .app-shell{display:flex}
  .topbar{height:64px;padding-inline:12px}
  .channel-welcome{margin:4px 10px 12px;padding:18px;border-radius:17px}
  .message-row{margin-inline:4px;padding-inline:10px}
  .composer-wrap{padding:8px 10px 12px}
  .composer{border-radius:14px}
  .voice-room{padding:17px 12px}
  .voice-stage{border-radius:18px}
  .voice-channel-preview{margin:10px;padding:18px;border-radius:18px}
  .member-panel{box-shadow:-18px 0 45px rgba(0,0,0,.32)}
}
@media(max-width:520px){
  .brand-mark{width:44px;height:44px}
  .server-orb{width:41px;height:41px}
  .performance-banner{padding-inline:10px}
  .channel-welcome h1{font-size:22px}
  .channel-welcome>div{width:45px;height:45px;border-radius:14px}
  .message-body p{font-size:12px}
  .voice-hero h1{font-size:30px}
  .voice-channel-preview-copy h1{font-size:25px}
}
'''

css.write_text(text, encoding='utf-8')
print('Klyvro v0.4.20 premium visual refresh applied without changing call/chat data flow')
