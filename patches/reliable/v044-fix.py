from pathlib import Path

def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one target, found {count}: {old[:100]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

replace_once('app/nexora-app.tsx', '''        setDraft((current) => current ? current : text);
        if (replyTarget) setReplying((current) => current ?? replyTarget);''', '''        if (selectedRef.current === selected) {
          setDrafts((current) => current[selected] ? current : { ...current, [selected]: text });
          if (replyTarget) setReplying((current) => current ?? replyTarget);
        }''')
replace_once('app/nexora-app.tsx', ' • demonstração local</footer>', ' • armazenamento local</footer>')
replace_once('app/settings-panel.tsx', '<span>Online • perfil local</span>', '<span>Perfil Klyvro</span>')
print('Klyvro v0.4.4 TypeScript/polish fix applied')
