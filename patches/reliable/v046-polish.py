from pathlib import Path

ROOT = Path('.')

def replace_once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one target, found {count}: {old[:140]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

replace_once(
    'app/nexora-app.tsx',
    '''  const currentMessages = messages[selected] ?? [];
  const pinnedMessages = pinnedByChannel[selected] ?? [];''',
    '''  const currentMessages = messages[selected] ?? [];
  const currentProfileColor = profileRows.find((row) => row.slot === profileSlot)?.avatar_color ?? "#ff304f";
  const pinnedMessages = pinnedByChannel[selected] ?? [];'''
)

replace_once(
    'app/nexora-app.tsx',
    '''  useEffect(() => { selectedRef.current = selected; }, [selected]);
  useEffect(() => { activeServerRef.current = activeServer; }, [activeServer]);''',
    '''  useEffect(() => { selectedRef.current = selected; }, [selected]);
  useEffect(() => { activeServerRef.current = activeServer; }, [activeServer]);
  useEffect(() => {
    if (!profileSlot || pendingProfileNameRef.current) return;
    const serverProfile = profileRows.find((row) => row.slot === profileSlot);
    if (!serverProfile || serverProfile.display_name === profile.name) return;
    const next = { ...profile, name: serverProfile.display_name };
    setProfile(next);
    writeLocal(STORAGE_KEYS.profile, next);
  }, [profile.name, profile.photo, profileRows, profileSlot]);
  useEffect(() => {
    setSelectedMember((current) => {
      if (!current?.slot) return current;
      const row = profileRows.find((item) => item.slot === current.slot);
      if (!row) return null;
      const online = onlineSlots.includes(row.slot);
      const next: Member = {
        ...current,
        name: row.display_name,
        avatar: (row.display_name[0] || "J").toUpperCase(),
        color: row.avatar_color,
        game: online ? "Klyvro • conectado agora" : "Offline",
        status: online ? "online" : "offline",
      };
      return next.name === current.name && next.avatar === current.avatar && next.color === current.color && next.status === current.status ? current : next;
    });
  }, [onlineSlots, profileRows]);'''
)

replace_once(
    'app/nexora-app.tsx',
    '''          } else if (reason.includes("profile not claimed")) {
            scheduleIdentityRetry(1_000);
          }''',
    '''          } else if (reason.includes("profile not claimed")) {
            scheduleIdentityRetry(1_000);
          } else {
            scheduleIdentityRetry(10_000);
          }'''
)

replace_once(
    'app/nexora-app.tsx',
    '''function ChannelRow({ channel, active, unread, onClick }: { channel: Channel; active: boolean; unread?: number; onClick: () => void }) {
  return <button className={`channel ${active ? "active" : ""}`} aria-current={active ? "page" : undefined} aria-label={unread ? `${channel.label}, ${unread} mensagens não lidas` : channel.label} onClick={onClick}><Icon name={channel.type === "voice" ? "volume" : channel.type === "lfg" ? "users" : "hash"} size={17} /><span>{channel.label}</span>{unread ? <b className="channel-badge" aria-hidden="true">{unread}</b> : null}</button>;
}''',
    '''function ChannelRow({ channel, active, unread, onClick }: { channel: Channel; active: boolean; unread?: boolean; onClick: () => void }) {
  return <button className={`channel ${active ? "active" : ""}`} aria-current={active ? "page" : undefined} aria-label={unread ? `${channel.label}, novas mensagens` : channel.label} onClick={onClick}><Icon name={channel.type === "voice" ? "volume" : channel.type === "lfg" ? "users" : "hash"} size={17} /><span>{channel.label}</span>{unread ? <b className="channel-badge" aria-hidden="true">•</b> : null}</button>;
}'''
)

replace_once('app/nexora-app.tsx', 'unread={readChannels[item.id] === false ? 1 : undefined}', 'unread={readChannels[item.id] === false}')
replace_once('app/nexora-app.tsx', 'color: "#ff304f", time: "Enviando…"', 'color: currentProfileColor, time: "Enviando…"')
replace_once(
    'app/nexora-app.tsx',
    '<Avatar label={(profile.name[0] || "N").toUpperCase()} color="#ff304f" image={profile.photo} small status="online" />',
    '<Avatar label={(profile.name[0] || "N").toUpperCase()} color={currentProfileColor} image={profile.photo} small status={networkState === "online" ? "online" : "away"} />'
)

print('Klyvro v0.4.6 polish patch applied successfully')
