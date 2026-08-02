create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at=now(); return new; end; $$;

create table if not exists public.players(
id uuid primary key default gen_random_uuid(), first_name text not null,last_name text not null,
birth_date date,position text,category text,status text,photo_url text,is_active boolean not null default true,
arrival_date date,departure_date date,created_at timestamptz not null default now(),updated_at timestamptz not null default now());

create table if not exists public.attendance_sessions(
id uuid primary key default gen_random_uuid(),session_date date not null,session_time time,session_type text not null,
title text,comment text,created_at timestamptz not null default now(),updated_at timestamptz not null default now());

create table if not exists public.attendance_records(
id uuid primary key default gen_random_uuid(),attendance_session_id uuid not null references public.attendance_sessions(id) on delete cascade,
player_id uuid not null references public.players(id) on delete restrict,status text not null,comment text,
created_at timestamptz not null default now(),updated_at timestamptz not null default now(),
unique(attendance_session_id,player_id));

create table if not exists public.shooting_sessions(
id uuid primary key default gen_random_uuid(),player_id uuid not null references public.players(id) on delete restrict,
session_date date not null,duration_seconds integer not null default 0 check(duration_seconds>=0),comment text,
created_at timestamptz not null default now(),updated_at timestamptz not null default now());

create table if not exists public.shooting_results(
id uuid primary key default gen_random_uuid(),shooting_session_id uuid not null references public.shooting_sessions(id) on delete cascade,
zone text not null,attempted integer not null default 0 check(attempted>=0),made integer not null default 0 check(made>=0 and made<=attempted),
created_at timestamptz not null default now(),unique(shooting_session_id,zone));

create table if not exists public.jump_tests(
id uuid primary key default gen_random_uuid(),player_id uuid not null references public.players(id) on delete restrict,
test_date date not null,test_type text not null,jump_1 numeric(6,2) not null,jump_2 numeric(6,2) not null,jump_3 numeric(6,2) not null,
official_score numeric(6,2) not null,reference_4w numeric(6,2),difference_cm numeric(6,2),difference_pct numeric(7,2),
fatigue_status text,comment text,created_at timestamptz not null default now(),updated_at timestamptz not null default now());

create table if not exists public.strength_templates(
id uuid primary key default gen_random_uuid(),name text not null,is_active boolean not null default true,
created_at timestamptz not null default now(),updated_at timestamptz not null default now());

create table if not exists public.strength_template_exercises(
id uuid primary key default gen_random_uuid(),template_id uuid not null references public.strength_templates(id) on delete cascade,
exercise_name text not null,sets_count integer not null check(sets_count>0),reps_count integer not null check(reps_count>0),
display_order integer not null default 1,created_at timestamptz not null default now());

create table if not exists public.strength_sessions(
id uuid primary key default gen_random_uuid(),template_id uuid references public.strength_templates(id) on delete set null,
session_date date not null,comment text,status text not null default 'Planifiée',
created_at timestamptz not null default now(),updated_at timestamptz not null default now());

create table if not exists public.strength_session_exercises(
id uuid primary key default gen_random_uuid(),strength_session_id uuid not null references public.strength_sessions(id) on delete cascade,
exercise_name text not null,sets_count integer not null,reps_count integer not null,display_order integer not null default 1,
created_at timestamptz not null default now());

create table if not exists public.strength_player_results(
id uuid primary key default gen_random_uuid(),player_id uuid not null references public.players(id) on delete restrict,
session_exercise_id uuid not null references public.strength_session_exercises(id) on delete cascade,
load_kg numeric(7,2) not null default 0,rpe numeric(4,1) not null default 0 check(rpe>=0 and rpe<=10),
estimated_1rm numeric(7,2) not null default 0,comment text,
created_at timestamptz not null default now(),updated_at timestamptz not null default now(),unique(player_id,session_exercise_id));

create table if not exists public.staff_comments(
id uuid primary key default gen_random_uuid(),player_id uuid not null references public.players(id) on delete restrict,
report_month date not null,comment text not null default '',author text,
created_at timestamptz not null default now(),updated_at timestamptz not null default now(),unique(player_id,report_month));

create table if not exists public.app_settings(
key text primary key,value text,updated_at timestamptz not null default now());

do $$
declare t text;
begin
foreach t in array array['players','attendance_sessions','attendance_records','shooting_sessions','jump_tests','strength_templates','strength_sessions','strength_player_results','staff_comments']
loop
execute format('drop trigger if exists trg_%I_updated_at on public.%I',t,t);
execute format('create trigger trg_%I_updated_at before update on public.%I for each row execute function public.set_updated_at()',t,t);
end loop;
end $$;

create index if not exists idx_attendance_sessions_date on public.attendance_sessions(session_date);
create index if not exists idx_shooting_sessions_player_date on public.shooting_sessions(player_id,session_date);
create index if not exists idx_jump_tests_player_date on public.jump_tests(player_id,test_date);
create index if not exists idx_strength_sessions_date on public.strength_sessions(session_date);
