-- Klyvro v0.4.10: strict validation for screen-share signaling payloads.
-- The client only sends {"active": true|false}. Reject malformed values so
-- receivers never interpret strings/numbers/extra fields as a valid screen state.

create or replace function public.klyvro_send_voice_signal(
  p_token text,
  p_room_id text,
  p_to_slot smallint,
  p_kind text,
  p_payload jsonb
)
returns bigint
language plpgsql
security definer
set search_path = pg_catalog, extensions
as $function$
declare
  v_hash text := encode(digest(p_token, 'sha256'), 'hex');
  v_from smallint;
  v_id bigint;
begin
  select p.slot into v_from
  from public.klyvro_profiles p
  where p.claim_token_hash = v_hash
  limit 1;

  if v_from is null then raise exception 'profile not claimed'; end if;
  if p_to_slot not between 1 and 5 or p_to_slot = v_from then raise exception 'invalid target'; end if;
  if p_room_id is null or char_length(p_room_id) < 3 or char_length(p_room_id) > 100 then raise exception 'invalid room'; end if;
  if not exists (
    select 1 from public.klyvro_channels c
    where c.kind = 'voice' and p_room_id = c.server_id || ':' || c.id
  ) then raise exception 'invalid room'; end if;
  if p_kind not in ('description','candidate','screen') then raise exception 'invalid signal kind'; end if;
  if p_payload is null or pg_column_size(p_payload) > 32768 then raise exception 'signal too large'; end if;

  if p_kind = 'screen' and (
    jsonb_typeof(p_payload) <> 'object'
    or not (p_payload ? 'active')
    or jsonb_typeof(p_payload -> 'active') <> 'boolean'
    or p_payload - 'active' <> '{}'::jsonb
  ) then
    raise exception 'invalid screen signal';
  end if;

  if not exists (
    select 1 from public.klyvro_presence pr
    where pr.slot = v_from
      and pr.voice_room = p_room_id
      and pr.voice_seen > now() - interval '20 seconds'
  ) then raise exception 'sender not active in room'; end if;

  if not exists (
    select 1 from public.klyvro_presence pr
    where pr.slot = p_to_slot
      and pr.voice_room = p_room_id
      and pr.voice_seen > now() - interval '20 seconds'
  ) then raise exception 'target not active in room'; end if;

  delete from public.klyvro_voice_signals
  where created_at < now() - interval '5 minutes';

  insert into public.klyvro_voice_signals(room_id, from_slot, to_slot, kind, payload)
  values (p_room_id, v_from, p_to_slot, p_kind, p_payload)
  returning id into v_id;

  return v_id;
end;
$function$;

revoke execute on function public.klyvro_send_voice_signal(text,text,smallint,text,jsonb) from public;
grant execute on function public.klyvro_send_voice_signal(text,text,smallint,text,jsonb) to anon, authenticated;
