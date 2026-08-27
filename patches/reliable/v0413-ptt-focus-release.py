from pathlib import Path

ROOT = Path('.')


def once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: v0.4.13 expected one target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


# Version metadata.
once('app/nexora-app.tsx', 'const KLYVRO_BUILD = "0.4.12";', 'const KLYVRO_BUILD = "0.4.13";')
once('package.json', '"version": "0.4.12"', '"version": "0.4.13"')
once('app/voice-room.tsx', 'VOZ • CORE v0.4.12', 'VOZ • CORE v0.4.13')

# Push-to-talk must fail closed. Browsers can miss the KeyV keyup when the tab or
# window loses focus (Alt+Tab, app switch, tab hidden), which could otherwise
# leave talking=true and keep the microphone enabled until another KeyV release.
old_ptt = '''  useEffect(() => {
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
  }, [joined, audio.inputMode]);'''

new_ptt = '''  useEffect(() => {
    if (!joined || audio.inputMode !== "ptt") return;
    const down = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (target.matches("input, textarea") || target.isContentEditable) return;
      if (event.code === "KeyV" && !event.repeat) { event.preventDefault(); setTalking(true); }
    };
    const release = () => setTalking(false);
    const up = (event: KeyboardEvent) => { if (event.code === "KeyV") release(); };
    const visibility = () => { if (document.hidden) release(); };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    window.addEventListener("blur", release);
    document.addEventListener("visibilitychange", visibility);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
      window.removeEventListener("blur", release);
      document.removeEventListener("visibilitychange", visibility);
      release();
    };
  }, [joined, audio.inputMode]);'''

once('app/voice-room.tsx', old_ptt, new_ptt)

print('Klyvro v0.4.13 PTT focus-loss fail-closed patch applied')
