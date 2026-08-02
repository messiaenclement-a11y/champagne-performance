alter table public.players enable row level security;
alter table public.attendance_sessions enable row level security;
alter table public.attendance_records enable row level security;
alter table public.shooting_sessions enable row level security;
alter table public.shooting_results enable row level security;
alter table public.jump_tests enable row level security;
alter table public.strength_templates enable row level security;
alter table public.strength_template_exercises enable row level security;
alter table public.strength_sessions enable row level security;
alter table public.strength_session_exercises enable row level security;
alter table public.strength_player_results enable row level security;
alter table public.staff_comments enable row level security;
alter table public.app_settings enable row level security;

insert into storage.buckets(id,name,public)
values('player-photos','player-photos',true)
on conflict(id) do update set public=excluded.public;
