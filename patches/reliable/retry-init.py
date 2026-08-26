from pathlib import Path

path = Path('app/nexora-app.tsx')
text = path.read_text(encoding='utf-8')

text = text.replace('const KLYVRO_BUILD = "0.4.1";', 'const KLYVRO_BUILD = "0.4.2";')

old = '''        await heartbeat();
        await Promise.all([refreshMessages(), refreshProfilesAndPresence()]);
        if (cancelled) return;
        messageTimer = window.setInterval(() => { void refreshMessages().catch(() => setNetworkState("offline")); }, 1800);
        presenceTimer = window.setInterval(() => { void refreshProfilesAndPresence().catch(() => setNetworkState("offline")); }, 2500);
        heartbeatTimer = window.setInterval(() => { void heartbeat().catch(() => setNetworkState("offline")); }, 5000);'''

new = '''        try {
          await heartbeat();
        } catch (heartbeatError) {
          console.warn("Klyvro heartbeat inicial falhou; mantendo chat ativo e tentando reconectar", heartbeatError);
          if (!cancelled) setNetworkState("offline");
        }

        await Promise.all([refreshMessages(), refreshProfilesAndPresence()]);
        if (cancelled) return;

        messageTimer = window.setInterval(() => {
          void refreshMessages().then(() => {
            if (!cancelled) setNetworkState((current) => current === "connecting" ? "online" : current);
          }).catch(() => setNetworkState("offline"));
        }, 1800);

        presenceTimer = window.setInterval(() => {
          void refreshProfilesAndPresence().catch(() => setNetworkState("offline"));
        }, 2500);

        heartbeatTimer = window.setInterval(() => {
          void heartbeat().catch(() => setNetworkState("offline"));
        }, 5000);'''

if old not in text:
    raise SystemExit('expected Klyvro initialization block not found')

text = text.replace(old, new)
path.write_text(text, encoding='utf-8')
