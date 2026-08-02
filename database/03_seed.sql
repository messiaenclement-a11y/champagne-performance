insert into public.app_settings(key,value) values
('club_name','Champagne Basket Formation'),
('season','2026-2027'),
('shooting_min_attempts','10'),
('jump_orange_threshold','-5'),
('jump_red_threshold','-10')
on conflict(key) do nothing;
