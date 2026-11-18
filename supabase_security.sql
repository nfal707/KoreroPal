create table if not exists public.ai_request_counters (
    scope text not null,
    window_seconds integer not null,
    window_start bigint not null,
    used integer not null check (used >= 0),
    primary key (scope, window_seconds, window_start)
);
alter table public.ai_request_counters enable row level security;
revoke all on public.ai_request_counters from public, anon, authenticated;
grant select, insert, update, delete on public.ai_request_counters to service_role;

create or replace function public.consume_koreropal_ai_quota(
    p_ip_key text, p_session_key text
) returns boolean
language plpgsql security definer set search_path = ''
as $$
declare
    current_epoch bigint := floor(extract(epoch from now()))::bigint;
    scope_name text;
    seconds integer;
    max_calls integer;
    start_epoch bigint;
    existing integer;
    scope_type text;
    identifier text;
begin
    if p_ip_key !~ '^[a-f0-9]{64}$' or p_session_key !~ '^[a-f0-9]{64}$' then
        raise exception 'Invalid quota key';
    end if;

    perform pg_catalog.pg_advisory_xact_lock(27410261);

    for scope_type, seconds, max_calls in
        select q.kind, q.window_seconds, q.max_calls
        from (values
            ('session', 600, 25),
            ('session', 86400, 35),
            ('ip', 600, 60),
            ('ip', 86400, 180),
            ('global', 86400, 300)
        ) as q(kind, window_seconds, max_calls)
    loop
        identifier := case scope_type
            when 'session' then p_session_key
            when 'ip' then p_ip_key
            else 'global'
        end;
        scope_name := scope_type || ':' || identifier;
        start_epoch := current_epoch - (current_epoch % seconds);
        select used into existing from public.ai_request_counters
        where scope = scope_name and window_seconds = seconds and window_start = start_epoch;
        if coalesce(existing, 0) >= max_calls then
            return false;
        end if;
    end loop;

    for scope_type, seconds, max_calls in
        select q.kind, q.window_seconds, q.max_calls
        from (values
            ('session', 600, 25),
            ('session', 86400, 35),
            ('ip', 600, 60),
            ('ip', 86400, 180),
            ('global', 86400, 300)
        ) as q(kind, window_seconds, max_calls)
    loop
        identifier := case scope_type
            when 'session' then p_session_key
            when 'ip' then p_ip_key
            else 'global'
        end;
        scope_name := scope_type || ':' || identifier;
        start_epoch := current_epoch - (current_epoch % seconds);
        insert into public.ai_request_counters(scope, window_seconds, window_start, used)
        values (scope_name, seconds, start_epoch, 1)
        on conflict (scope, window_seconds, window_start)
        do update set used = public.ai_request_counters.used + 1;
    end loop;
    delete from public.ai_request_counters where window_start < current_epoch - 172800;
    return true;
end;
$$;
revoke execute on function public.consume_koreropal_ai_quota(text, text) from public, anon, authenticated;
grant execute on function public.consume_koreropal_ai_quota(text, text) to service_role;

create or replace function public.delete_koreropal_ratings(p_recovery_code text)
returns integer
language plpgsql security definer set search_path = ''
as $$
declare
    first_count integer;
    second_count integer;
begin
    if p_recovery_code !~ '^KP-([A-Z0-9]{10}|[A-F0-9]{40})$' then
        raise exception 'Invalid recovery code';
    end if;
    delete from public.daily_checkins where anonymous_id = p_recovery_code;
    get diagnostics first_count = row_count;
    delete from public.evaluation_sessions where anonymous_id = p_recovery_code;
    get diagnostics second_count = row_count;
    return first_count + second_count;
end;
$$;
revoke execute on function public.delete_koreropal_ratings(text) from public, anon, authenticated;
grant execute on function public.delete_koreropal_ratings(text) to service_role;
