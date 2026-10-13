-- Run in Supabase SQL editor. Create manager accounts via Supabase Auth.
create table if not exists public.manager_sites (user_id uuid not null references auth.users(id) on delete cascade, site_id text not null, primary key(user_id,site_id));
create table if not exists public.production_live (site_id text primary key, updated_at timestamptz not null, shift_date date not null, total integer not null, passenger integer not null, suv integer not null, unknown integer not null, flow_per_minute numeric not null, status text not null, best_hour_count integer not null, best_hour_label text not null);
create table if not exists public.production_hourly (site_id text not null,shift_date date not null,slot integer not null,start_at timestamptz not null,end_at timestamptz not null,count integer not null,completed boolean not null,primary key(site_id,shift_date,slot));
create table if not exists public.production_incidents (site_id text not null,incident_id text not null,started timestamptz not null,ended timestamptz,duration_seconds integer not null,status text not null,reason text,notes text,submitted_by text,primary key(site_id,incident_id));
alter table public.manager_sites enable row level security;
alter table public.production_live enable row level security;
alter table public.production_hourly enable row level security;
alter table public.production_incidents enable row level security;
create policy "managers see own membership" on public.manager_sites for select to authenticated using (user_id=auth.uid());
create policy "managers view live" on public.production_live for select to authenticated using (exists(select 1 from public.manager_sites m where m.user_id=auth.uid() and m.site_id=production_live.site_id));
create policy "managers view hours" on public.production_hourly for select to authenticated using (exists(select 1 from public.manager_sites m where m.user_id=auth.uid() and m.site_id=production_hourly.site_id));
create policy "managers view incidents" on public.production_incidents for select to authenticated using (exists(select 1 from public.manager_sites m where m.user_id=auth.uid() and m.site_id=production_incidents.site_id));
-- Column-specific update grant; RLS additionally restricts site. No count or incident timing updates allowed from manager clients.
revoke update on public.production_incidents from authenticated;
grant update (reason,notes,submitted_by) on public.production_incidents to authenticated;
create policy "managers edit incident reasons only" on public.production_incidents for update to authenticated using (exists(select 1 from public.manager_sites m where m.user_id=auth.uid() and m.site_id=production_incidents.site_id)) with check (exists(select 1 from public.manager_sites m where m.user_id=auth.uid() and m.site_id=production_incidents.site_id));
-- Example after creating a user: insert into public.manager_sites(user_id,site_id) values ('USER-UUID','brisbane-1');
