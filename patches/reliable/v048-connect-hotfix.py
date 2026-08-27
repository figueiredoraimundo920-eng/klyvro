from pathlib import Path

ROOT = Path('.')

def replace_once(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one hotfix target, found {count}: {old[:180]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

# A profile-photo permission/read failure must never prevent joining voice.
replace_once(
    'app/voice-room.tsx',
    '''      const { data: profileRows, error: profileError } = await supabase.from("klyvro_profiles").select("slot,display_name,avatar_color,avatar_data").order("slot");
      if (profileError) throw profileError;
      profilesRef.current = Object.fromEntries(((profileRows ?? []) as ProfileRow[]).map((row) => [Number(row.slot), row]));''',
    '''      let profileRows: ProfileRow[] = [];
      const { data: richProfileRows, error: richProfileError } = await supabase.from("klyvro_profiles").select("slot,display_name,avatar_color,avatar_data").order("slot");
      if (!richProfileError) profileRows = (richProfileRows ?? []) as ProfileRow[];
      else {
        console.warn("Klyvro avatar profile read failed; continuing voice without remote photos", richProfileError);
        const { data: basicProfileRows, error: basicProfileError } = await supabase.from("klyvro_profiles").select("slot,display_name,avatar_color").order("slot");
        if (basicProfileError) throw basicProfileError;
        profileRows = ((basicProfileRows ?? []) as Array<{ slot: number; display_name: string; avatar_color: string }>).map((row) => ({ ...row, avatar_data: null }));
      }
      profilesRef.current = Object.fromEntries(profileRows.map((row) => [Number(row.slot), row]));'''
)

replace_once(
    'app/voice-room.tsx',
    '''        if (error) throw error;
        if (liveProfilesError) throw liveProfilesError;
        profilesRef.current = Object.fromEntries(((liveProfiles ?? []) as ProfileRow[]).map((row) => [Number(row.slot), row]));''',
    '''        if (error) throw error;
        if (liveProfilesError) {
          console.warn("Klyvro live avatar refresh failed; keeping voice alive without remote photos", liveProfilesError);
          const { data: basicLiveProfiles, error: basicLiveProfilesError } = await supabase.from("klyvro_profiles").select("slot,display_name,avatar_color").order("slot");
          if (basicLiveProfilesError) throw basicLiveProfilesError;
          profilesRef.current = Object.fromEntries(((basicLiveProfiles ?? []) as Array<{ slot: number; display_name: string; avatar_color: string }>).map((row) => [Number(row.slot), { ...row, avatar_data: null }]));
        } else {
          profilesRef.current = Object.fromEntries(((liveProfiles ?? []) as ProfileRow[]).map((row) => [Number(row.slot), row]));
        }'''
)

# The same rule applies to the app-wide member/profile refresh: avatar failure is cosmetic, not connectivity.
replace_once(
    'app/nexora-app.tsx',
    '''      if (profilesError) throw profilesError;
      if (presenceError) throw presenceError;
      if (cancelled) return;
      if (profiles) {
        const typedProfiles = profiles as KlyvroProfileRow[];''',
    '''      if (presenceError) throw presenceError;
      let usableProfiles = profiles as KlyvroProfileRow[] | null;
      if (profilesError) {
        console.warn("Klyvro avatar refresh failed; continuing core connection without profile photos", profilesError);
        const { data: basicProfiles, error: basicProfilesError } = await supabase.from("klyvro_profiles").select("slot,display_name,avatar_color,claimed").order("slot");
        if (basicProfilesError) throw basicProfilesError;
        usableProfiles = ((basicProfiles ?? []) as Array<{ slot: number; display_name: string; avatar_color: string; claimed: boolean }>).map((row) => ({ ...row, avatar_data: null }));
      }
      if (cancelled) return;
      if (usableProfiles) {
        const typedProfiles = usableProfiles as KlyvroProfileRow[];'''
)

print('Klyvro v0.4.8 connectivity hotfix applied: avatar reads are non-blocking')
