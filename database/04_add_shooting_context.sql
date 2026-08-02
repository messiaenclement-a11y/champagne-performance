alter table public.shooting_results
add column if not exists context text not null default 'sans_opposition';

alter table public.shooting_results
drop constraint if exists shooting_results_shooting_session_id_zone_key;

alter table public.shooting_results
drop constraint if exists shooting_results_context_check;

alter table public.shooting_results
add constraint shooting_results_context_check
check (context in ('sans_opposition','mouvement','avec_opposition'));

create unique index if not exists uq_shooting_results_session_context_zone
on public.shooting_results(shooting_session_id, context, zone);
