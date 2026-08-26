from pathlib import Path

path = Path('app/nexora-app.tsx')
text = path.read_text(encoding='utf-8')

text = text.replace('const KLYVRO_BUILD = "0.4.1";', 'const KLYVRO_BUILD = "0.4.3";')
text = text.replace('const KLYVRO_BUILD = "0.4.2";', 'const KLYVRO_BUILD = "0.4.3";')

old = '''        await heartbeat();
        await Promise.all([refreshMessages(), refreshProfilesAndPresence()]);
        if (cancelled) return;
        messageTimer = window.setInterval(() => { void refreshMessages().catch(() => setNetworkState("offline")); }, 1800);
        presenceTimer = window.setInterval(() => { void refreshProfilesAndPresence().catch(() => setNetworkState("offline")); }, 2500);
        heartbeatTimer = window.setInterval(() => { void heartbeat().catch(() => setNetworkState("offline")); }, 5000);'''

mid = '''        try {
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

new = mid

if old in text:
    text = text.replace(old, new)
elif mid not in text:
    raise SystemExit('expected Klyvro initialization block not found')

old_catch = '''      } catch (error) {
        console.error("Klyvro Supabase init failed", error);
        if (!cancelled) setNetworkState("offline");
      }
    })();'''

new_catch = '''      } catch (error) {
        console.error("Klyvro Supabase init failed", error);
        const reason = error instanceof Error ? error.message : String(error);
        if (!cancelled) {
          setNetworkState("offline");
          if (reason.includes("currently active") || reason.includes("already claimed")) {
            setToast("Os 3 perfis estão ativos. Feche uma sessão antiga e aguarde até 20 segundos.");
          }
        }

        // Mesmo sem identidade disponível, manter histórico e presença visíveis em modo leitura.
        try {
          await Promise.all([refreshMessages(), refreshProfilesAndPresence()]);
          if (!cancelled && messageTimer === null) {
            messageTimer = window.setInterval(() => { void refreshMessages().catch(() => undefined); }, 1800);
            presenceTimer = window.setInterval(() => { void refreshProfilesAndPresence().catch(() => undefined); }, 2500);
          }
        } catch (readOnlyError) {
          console.warn("Klyvro read-only fallback failed", readOnlyError);
        }
      }
    })();'''

if old_catch not in text:
    raise SystemExit('expected Klyvro catch block not found')
text = text.replace(old_catch, new_catch)

path.write_text(text, encoding='utf-8')
