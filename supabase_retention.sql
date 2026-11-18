-- Install after supabase_security.sql. Run once in Supabase SQL Editor.
-- The named job runs each day at 03:17 UTC. Verify its status in Cron.
create extension if not exists pg_cron with schema pg_catalog;

create or replace function public.prune_koreropal_expired_ratings()
returns integer
language plpgsql security invoker set search_path = ''
as $$
declare
    first_count integer;
    second_count integer;
begin
    delete from public.daily_checkins where created_at < pg_catalog.now() - interval '365 days';
    get diagnostics first_count = row_count;
    delete from public.evaluation_sessions where created_at < pg_catalog.now() - interval '365 days';
    get diagnostics second_count = row_count;
    return first_count + second_count;
end;
$$;
revoke execute on function public.prune_koreropal_expired_ratings() from public, anon, authenticated;
grant execute on function public.prune_koreropal_expired_ratings() to postgres, service_role;

select cron.schedule(
    'koreropal-retention-daily',
    '17 3 * * *',
    $$select public.prune_koreropal_expired_ratings()$$
);
