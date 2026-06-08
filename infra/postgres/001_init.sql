create extension if not exists pgcrypto;

create schema if not exists auth;
create schema if not exists private;

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then
    create role service_role;
  end if;
end;
$$;

create table if not exists auth.users (
  id uuid primary key default gen_random_uuid(),
  email text unique,
  created_at timestamptz not null default now()
);

create or replace function auth.uid()
returns uuid
language sql
stable
as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;

create table if not exists public.atlas_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.atlas_subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references auth.users(id) on delete cascade,
  stripe_customer_id text unique,
  stripe_subscription_id text unique,
  plan text not null default 'trial',
  status text not null default 'trialing',
  monthly_reports integer not null default 5 check (monthly_reports >= 0),
  period_reports_used integer not null default 0 check (period_reports_used >= 0),
  current_period_start timestamptz not null default now(),
  current_period_end timestamptz not null default (now() + interval '1 month'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.atlas_research_runs (
  id text primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  ticker text not null,
  report_date date not null,
  depth text not null check (depth in ('quick', 'standard', 'deep')),
  analysts text[] not null default '{}',
  status text not null check (status in ('queued', 'running', 'completed', 'failed')),
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  report_id text,
  error_message text
);

create table if not exists public.atlas_reports (
  id text primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  run_id text not null unique references public.atlas_research_runs(id) on delete cascade,
  report jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.atlas_watchlist_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  ticker text not null,
  company_name text not null,
  created_at timestamptz not null default now(),
  unique (user_id, ticker)
);

create table if not exists public.atlas_usage_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  research_run_id text references public.atlas_research_runs(id) on delete set null,
  event_type text not null,
  quantity integer not null default 1 check (quantity > 0),
  cost_cents integer not null default 0 check (cost_cents >= 0),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists atlas_subscriptions_user_idx
  on public.atlas_subscriptions using btree (user_id);
create index if not exists atlas_subscriptions_stripe_customer_idx
  on public.atlas_subscriptions using btree (stripe_customer_id);
create index if not exists atlas_research_runs_user_created_idx
  on public.atlas_research_runs using btree (user_id, created_at desc);
create index if not exists atlas_research_runs_user_status_idx
  on public.atlas_research_runs using btree (user_id, status);
create index if not exists atlas_reports_user_created_idx
  on public.atlas_reports using btree (user_id, created_at desc);
create index if not exists atlas_reports_run_idx
  on public.atlas_reports using btree (run_id);
create index if not exists atlas_watchlist_user_created_idx
  on public.atlas_watchlist_items using btree (user_id, created_at desc);
create index if not exists atlas_usage_events_user_created_idx
  on public.atlas_usage_events using btree (user_id, created_at desc);
create index if not exists atlas_usage_events_run_idx
  on public.atlas_usage_events using btree (research_run_id);

alter table public.atlas_profiles enable row level security;
alter table public.atlas_subscriptions enable row level security;
alter table public.atlas_research_runs enable row level security;
alter table public.atlas_reports enable row level security;
alter table public.atlas_watchlist_items enable row level security;
alter table public.atlas_usage_events enable row level security;

grant select, insert, update on public.atlas_profiles to authenticated;
grant select, insert, update on public.atlas_subscriptions to authenticated;
grant select, insert, update, delete on public.atlas_research_runs to authenticated;
grant select, insert, update, delete on public.atlas_reports to authenticated;
grant select, insert, update, delete on public.atlas_watchlist_items to authenticated;
grant select, insert on public.atlas_usage_events to authenticated;

drop policy if exists "atlas_profiles_select_own" on public.atlas_profiles;
create policy "atlas_profiles_select_own"
  on public.atlas_profiles for select to authenticated
  using ((select auth.uid()) = id);

drop policy if exists "atlas_profiles_insert_own" on public.atlas_profiles;
create policy "atlas_profiles_insert_own"
  on public.atlas_profiles for insert to authenticated
  with check ((select auth.uid()) = id);

drop policy if exists "atlas_profiles_update_own" on public.atlas_profiles;
create policy "atlas_profiles_update_own"
  on public.atlas_profiles for update to authenticated
  using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

drop policy if exists "atlas_subscriptions_select_own" on public.atlas_subscriptions;
create policy "atlas_subscriptions_select_own"
  on public.atlas_subscriptions for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "atlas_research_runs_select_own" on public.atlas_research_runs;
create policy "atlas_research_runs_select_own"
  on public.atlas_research_runs for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "atlas_research_runs_insert_own" on public.atlas_research_runs;
create policy "atlas_research_runs_insert_own"
  on public.atlas_research_runs for insert to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "atlas_research_runs_update_own" on public.atlas_research_runs;
create policy "atlas_research_runs_update_own"
  on public.atlas_research_runs for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "atlas_reports_select_own" on public.atlas_reports;
create policy "atlas_reports_select_own"
  on public.atlas_reports for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "atlas_reports_insert_own" on public.atlas_reports;
create policy "atlas_reports_insert_own"
  on public.atlas_reports for insert to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "atlas_watchlist_select_own" on public.atlas_watchlist_items;
create policy "atlas_watchlist_select_own"
  on public.atlas_watchlist_items for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "atlas_watchlist_insert_own" on public.atlas_watchlist_items;
create policy "atlas_watchlist_insert_own"
  on public.atlas_watchlist_items for insert to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "atlas_watchlist_update_own" on public.atlas_watchlist_items;
create policy "atlas_watchlist_update_own"
  on public.atlas_watchlist_items for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "atlas_watchlist_delete_own" on public.atlas_watchlist_items;
create policy "atlas_watchlist_delete_own"
  on public.atlas_watchlist_items for delete to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "atlas_usage_events_select_own" on public.atlas_usage_events;
create policy "atlas_usage_events_select_own"
  on public.atlas_usage_events for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "atlas_usage_events_insert_own" on public.atlas_usage_events;
create policy "atlas_usage_events_insert_own"
  on public.atlas_usage_events for insert to authenticated
  with check ((select auth.uid()) = user_id);

create or replace function private.handle_new_atlas_user()
returns trigger
language plpgsql
security definer
set search_path = public, auth
as $$
begin
  insert into public.atlas_profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do update set email = excluded.email, updated_at = now();

  insert into public.atlas_subscriptions (user_id, plan, status, monthly_reports, period_reports_used)
  values (new.id, 'trial', 'trialing', 5, 0)
  on conflict (user_id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created_atlas on auth.users;
create trigger on_auth_user_created_atlas
  after insert on auth.users
  for each row execute function private.handle_new_atlas_user();
