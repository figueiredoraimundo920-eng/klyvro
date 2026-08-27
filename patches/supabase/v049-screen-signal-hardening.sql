-- Klyvro v0.4.9: keep the database contract aligned with the WebRTC client.
-- Applied to production Supabase on 2026-08-27.

alter table public.klyvro_voice_signals
  drop constraint if exists klyvro_voice_signals_kind_check;

alter table public.klyvro_voice_signals
  add constraint klyvro_voice_signals_kind_check
  check (kind in ('description','candidate','screen'));

-- Browser clients only need direct reads. Writes are token-validated RPCs.
revoke all privileges on table public.klyvro_servers from anon, authenticated;
revoke all privileges on table public.klyvro_channels from anon, authenticated;
revoke all privileges on table public.klyvro_messages from anon, authenticated;
revoke all privileges on table public.klyvro_presence from anon, authenticated;
revoke all privileges on table public.klyvro_profiles from anon, authenticated;
revoke all privileges on table public.klyvro_voice_signals from anon, authenticated;

grant select on table public.klyvro_servers to anon, authenticated;
grant select on table public.klyvro_channels to anon, authenticated;
grant select on table public.klyvro_messages to anon, authenticated;
grant select on table public.klyvro_presence to anon, authenticated;
grant select (slot, display_name, avatar_color, avatar_data, claimed)
  on table public.klyvro_profiles to anon, authenticated;

-- SECURITY DEFINER RPCs are intentional public API endpoints for the current
-- token-based five-profile architecture. Avoid implicit EXECUTE via PUBLIC.
revoke execute on function public.klyvro_claim_profile(text) from public;
revoke execute on function public.klyvro_heartbeat(text,text,text) from public;
revoke execute on function public.klyvro_leave_voice(text) from public;
revoke execute on function public.klyvro_poll_voice_signals(text,text,bigint) from public;
revoke execute on function public.klyvro_send_message(text,text,text,text) from public;
revoke execute on function public.klyvro_send_voice_signal(text,text,smallint,text,jsonb) from public;
revoke execute on function public.klyvro_update_profile(text,text) from public;
revoke execute on function public.klyvro_update_profile_v2(text,text,text,boolean) from public;
revoke execute on function public.klyvro_voice_heartbeat(text,text) from public;

grant execute on function public.klyvro_claim_profile(text) to anon, authenticated;
grant execute on function public.klyvro_heartbeat(text,text,text) to anon, authenticated;
grant execute on function public.klyvro_leave_voice(text) to anon, authenticated;
grant execute on function public.klyvro_poll_voice_signals(text,text,bigint) to anon, authenticated;
grant execute on function public.klyvro_send_message(text,text,text,text) to anon, authenticated;
grant execute on function public.klyvro_send_voice_signal(text,text,smallint,text,jsonb) to anon, authenticated;
grant execute on function public.klyvro_update_profile(text,text) to anon, authenticated;
grant execute on function public.klyvro_update_profile_v2(text,text,text,boolean) to anon, authenticated;
grant execute on function public.klyvro_voice_heartbeat(text,text) to anon, authenticated;

-- Pin privileged name resolution away from the exposed public schema.
alter function public.klyvro_claim_profile(text) set search_path = pg_catalog, extensions;
alter function public.klyvro_heartbeat(text,text,text) set search_path = pg_catalog, extensions;
alter function public.klyvro_leave_voice(text) set search_path = pg_catalog, extensions;
alter function public.klyvro_poll_voice_signals(text,text,bigint) set search_path = pg_catalog, extensions;
alter function public.klyvro_send_message(text,text,text,text) set search_path = pg_catalog, extensions;
alter function public.klyvro_send_voice_signal(text,text,smallint,text,jsonb) set search_path = pg_catalog, extensions;
alter function public.klyvro_update_profile(text,text) set search_path = pg_catalog, extensions;
alter function public.klyvro_update_profile_v2(text,text,text,boolean) set search_path = pg_catalog, extensions;
alter function public.klyvro_voice_heartbeat(text,text) set search_path = pg_catalog, extensions;
