def player_label(player: dict) -> str:
    return f"{player.get('first_name','')} {player.get('last_name','')}".strip()

def seconds_to_hms(seconds):
    total=max(0,int(seconds or 0))
    h,r=divmod(total,3600); m,s=divmod(r,60)
    return f"{h:02d}:{m:02d}:{s:02d}"
