from __future__ import annotations

import time
from datetime import date

import streamlit as st

from components.layout import page_header
from services.supabase_client import get_supabase
from utils.formatting import player_label

SHOOTING_CONTEXTS = {
    "statique_sans_opposition": "Statique - sans opposition",
    "statique_avec_opposition": "Statique - avec opposition",
    "mouvement_sans_opposition": "En mouvement - sans opposition",
    "mouvement_avec_opposition": "En mouvement - avec opposition",
}

ZONES = [
    ("0G", "0°G"),
    ("45G", "45°G"),
    ("70G", "70°G"),
    ("AXE", "AXE"),
    ("70D", "70°D"),
    ("45D", "45°D"),
    ("0D", "0°D"),
]

STATE_DEFAULTS = {
    "shooting_step": 1,
    "shooting_player_id": None,
    "shooting_player_name": "",
    "shooting_zone": "",
    "shooting_context": "statique_sans_opposition",
    "shooting_zone_label": "",
    "shooting_made": "0",
    "shooting_attempted": "0",
    "shooting_timer_running": False,
    "shooting_timer_started_at": None,
    "shooting_elapsed_seconds": 0,
    "shooting_session_date": date.today(),
    "shooting_lock_made": False,
    "shooting_lock_attempted": False,
    "shooting_lock_made_value": 0,
    "shooting_lock_attempted_value": 10,
}

for key, value in STATE_DEFAULTS.items():
    st.session_state.setdefault(key, value)

st.markdown(
    """
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1800px;}
        .shooting-header {background:#111827;color:white;padding:14px 18px;border-radius:14px;
            font-size:1.45rem;font-weight:800;margin-bottom:10px;}
        .shooting-steps {display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:10px 0 12px;}
        .shooting-step {padding:10px 8px;border:1px solid #d1d5db;border-radius:12px;
            background:white;color:#6b7280;text-align:center;font-size:.95rem;}
        .shooting-step.active {background:#B8A05A;border-color:#B8A05A;color:white;font-weight:700;}
        .shooting-context {color:#6b7280;font-size:.95rem;margin:2px 0 12px;min-height:22px;}
        .shooting-number {display:flex;align-items:center;justify-content:center;min-height:120px;
            padding:20px;border:1px solid #d1d5db;border-radius:18px;background:white;
            font-size:4.2rem;font-weight:800;margin-bottom:12px;}
        .shooting-summary {background:#f3f4f6;padding:14px;border-radius:12px;text-align:center;
            font-weight:700;margin:12px 0;}
        div[data-testid="stButton"] > button {min-height:62px;border-radius:999px;
            font-size:1.15rem;border:1px solid #d1d5db;background:white;}
        div[data-testid="stButton"] > button:hover {border-color:#B8A05A;color:#9A874B;}
        div[data-testid="stButton"] > button[kind="primary"] {background:#B8A05A;
            border-color:#B8A05A;color:white;font-weight:700;}
        div[data-testid="stButton"] > button[kind="primary"]:hover {background:#9A874B;
            border-color:#9A874B;color:white;}
        @media (max-width:900px) {
            .shooting-steps {grid-template-columns:repeat(2,1fr);}
            div[data-testid="stButton"] > button {min-height:68px;font-size:1.05rem;}
            .shooting-number {font-size:3.5rem;}
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_players() -> list[dict]:
    response = (
        get_supabase()
        .table("players")
        .select("*")
        .eq("is_active", True)
        .order("last_name")
        .execute()
    )
    return response.data or []


def player_button_label(player: dict) -> str:
    first_name = str(player.get("first_name") or "").strip()
    return first_name.upper() if first_name else player_label(player).upper()


def current_elapsed_seconds() -> int:
    elapsed = int(st.session_state.shooting_elapsed_seconds or 0)
    if st.session_state.shooting_timer_running and st.session_state.shooting_timer_started_at:
        elapsed += int(time.time() - float(st.session_state.shooting_timer_started_at))
    return max(0, elapsed)


def format_timer(total_seconds: int) -> str:
    minutes, seconds = divmod(max(0, int(total_seconds)), 60)
    return f"{minutes:02d}:{seconds:02d}"


def start_timer() -> None:
    if not st.session_state.shooting_timer_running:
        st.session_state.shooting_timer_started_at = time.time()
        st.session_state.shooting_timer_running = True


def stop_timer() -> None:
    if st.session_state.shooting_timer_running:
        st.session_state.shooting_elapsed_seconds = current_elapsed_seconds()
        st.session_state.shooting_timer_started_at = None
        st.session_state.shooting_timer_running = False


def adjust_timer(delta_seconds: int) -> None:
    was_running = st.session_state.shooting_timer_running
    st.session_state.shooting_elapsed_seconds = max(0, current_elapsed_seconds() + delta_seconds)
    st.session_state.shooting_timer_started_at = time.time() if was_running else None


def apply_locked_values() -> None:
    if st.session_state.shooting_lock_made:
        st.session_state.shooting_made = str(
            int(st.session_state.shooting_lock_made_value)
        )

    if st.session_state.shooting_lock_attempted:
        st.session_state.shooting_attempted = str(
            int(st.session_state.shooting_lock_attempted_value)
        )


def reset_entry(change_player: bool = True) -> None:
    st.session_state.shooting_zone = ""
    st.session_state.shooting_zone_label = ""
    st.session_state.shooting_made = "0"
    st.session_state.shooting_attempted = "0"
    apply_locked_values()
    if change_player:
        st.session_state.shooting_player_id = None
        st.session_state.shooting_player_name = ""
        st.session_state.shooting_step = 1
    else:
        st.session_state.shooting_step = 2


def append_digit(field_name: str, digit: int) -> None:
    value = str(st.session_state[field_name] or "0")
    if value == "0":
        value = ""
    st.session_state[field_name] = value + str(digit)


def clear_number(field_name: str) -> None:
    st.session_state[field_name] = "0"


def backspace_number(field_name: str) -> None:
    value = str(st.session_state[field_name] or "0")[:-1]
    st.session_state[field_name] = value or "0"


def select_player(player: dict) -> None:
    st.session_state.shooting_player_id = player["id"]
    st.session_state.shooting_player_name = player_button_label(player)
    st.session_state.shooting_zone = ""
    st.session_state.shooting_zone_label = ""
    st.session_state.shooting_made = "0"
    st.session_state.shooting_attempted = "0"
    apply_locked_values()
    st.session_state.shooting_step = 2


def select_zone(zone_code: str, zone_label: str) -> None:
    st.session_state.shooting_zone = zone_code
    st.session_state.shooting_zone_label = zone_label
    st.session_state.shooting_made = "0"
    st.session_state.shooting_attempted = "0"
    apply_locked_values()

    if st.session_state.shooting_lock_made:
        st.session_state.shooting_step = 4
    else:
        st.session_state.shooting_step = 3


def save_shooting_entry() -> None:
    player_id = st.session_state.shooting_player_id
    player_name = st.session_state.shooting_player_name
    zone = st.session_state.shooting_zone
    made = int(st.session_state.shooting_made or 0)
    attempted = int(st.session_state.shooting_attempted or 0)
    session_date = st.session_state.shooting_session_date.isoformat()
    shooting_context = st.session_state.shooting_context
    duration_seconds = current_elapsed_seconds()

    if not player_id:
        st.error("Choisis un joueur.")
        return
    if not zone:
        st.error("Choisis un spot.")
        return
    if made > attempted:
        st.error("Le nombre de tirs réussis ne peut pas dépasser le nombre de tirs tentés.")
        return

    db = get_supabase()
    sessions = (
        db.table("shooting_sessions").select("*")
        .eq("player_id", player_id).eq("session_date", session_date)
        .limit(1).execute().data or []
    )

    if sessions:
        shooting_session = sessions[0]
        db.table("shooting_sessions").update(
            {"duration_seconds": duration_seconds}
        ).eq("id", shooting_session["id"]).execute()
    else:
        response = db.table("shooting_sessions").insert({
            "player_id": player_id,
            "session_date": session_date,
            "duration_seconds": duration_seconds,
            "comment": None,
        }).execute()
        shooting_session = response.data[0]

    results = (
        db.table("shooting_results").select("*")
        .eq("shooting_session_id", shooting_session["id"])
        .eq("zone", zone).eq("context", shooting_context).limit(1).execute().data or []
    )

    if results:
        result = results[0]
        db.table("shooting_results").update({
            "attempted": int(result.get("attempted") or 0) + attempted,
            "made": int(result.get("made") or 0) + made,
        }).eq("id", result["id"]).execute()
    else:
        db.table("shooting_results").insert({
            "shooting_session_id": shooting_session["id"],
            "zone": zone,
            "context": shooting_context,
            "attempted": attempted,
            "made": made,
        }).execute()

    st.session_state.shooting_success_message = (
        f"{player_name} · {SHOOTING_CONTEXTS[shooting_context]} · {st.session_state.shooting_zone_label} · {made}/{attempted} enregistré."
    )
    reset_entry(change_player=True)
    st.rerun()


def render_number_pad(field_name: str) -> None:
    for row_index, row_digits in enumerate([[1, 2, 3], [4, 5, 6], [7, 8, 9]]):
        columns = st.columns(3)
        for column_index, digit in enumerate(row_digits):
            with columns[column_index]:
                if st.button(str(digit), key=f"{field_name}_{row_index}_{digit}", use_container_width=True):
                    append_digit(field_name, digit)
                    st.rerun()

    clear_col, zero_col, back_col = st.columns(3)
    with clear_col:
        if st.button("C", key=f"{field_name}_clear", type="primary", use_container_width=True):
            clear_number(field_name)
            st.rerun()
    with zero_col:
        if st.button("0", key=f"{field_name}_zero", use_container_width=True):
            append_digit(field_name, 0)
            st.rerun()
    with back_col:
        if st.button("⌫", key=f"{field_name}_backspace", use_container_width=True):
            backspace_number(field_name)
            st.rerun()


st.markdown('<div class="shooting-header">SAISIE TIRS</div>', unsafe_allow_html=True)

settings_col, timer_col = st.columns([1, 2])
with settings_col:
    selected_date = st.date_input(
        "Date de séance",
        value=st.session_state.shooting_session_date,
        key="shooting_date_widget",
    )
    if selected_date != st.session_state.shooting_session_date:
        st.session_state.shooting_session_date = selected_date
        reset_entry(change_player=True)
        st.rerun()

    st.markdown("**Contexte de tir**")
    selected_context = st.selectbox(
        "Contexte",
        options=list(SHOOTING_CONTEXTS.keys()),
        format_func=lambda value: SHOOTING_CONTEXTS[value],
        index=list(SHOOTING_CONTEXTS.keys()).index(st.session_state.shooting_context),
        label_visibility="collapsed",
        key="shooting_context_widget",
    )
    if selected_context != st.session_state.shooting_context:
        st.session_state.shooting_context = selected_context
        reset_entry(change_player=True)
        st.rerun()

    st.markdown("**Valeurs verrouillées**")

    lock_made_col, made_value_col = st.columns([1.6, 1])
    with lock_made_col:
        lock_made = st.checkbox(
            "Verrouiller les réussis",
            value=st.session_state.shooting_lock_made,
            key="shooting_lock_made_widget",
        )
    with made_value_col:
        made_lock_value = st.number_input(
            "Valeur réussis",
            min_value=0,
            step=1,
            value=int(st.session_state.shooting_lock_made_value),
            disabled=not lock_made,
            label_visibility="collapsed",
            key="shooting_lock_made_value_widget",
        )

    lock_attempted_col, attempted_value_col = st.columns([1.6, 1])
    with lock_attempted_col:
        lock_attempted = st.checkbox(
            "Verrouiller les tentés",
            value=st.session_state.shooting_lock_attempted,
            key="shooting_lock_attempted_widget",
        )
    with attempted_value_col:
        attempted_lock_value = st.number_input(
            "Valeur tentés",
            min_value=0,
            step=1,
            value=int(st.session_state.shooting_lock_attempted_value),
            disabled=not lock_attempted,
            label_visibility="collapsed",
            key="shooting_lock_attempted_value_widget",
        )

    st.session_state.shooting_lock_made = lock_made
    st.session_state.shooting_lock_attempted = lock_attempted
    st.session_state.shooting_lock_made_value = int(made_lock_value)
    st.session_state.shooting_lock_attempted_value = int(attempted_lock_value)
    apply_locked_values()

    if (
        lock_made
        and lock_attempted
        and int(made_lock_value) > int(attempted_lock_value)
    ):
        st.error(
            "La valeur verrouillée des réussis ne peut pas "
            "dépasser celle des tentés."
        )


@st.fragment(run_every="1s")
def timer_fragment() -> None:
    st.markdown(
        f'<div style="text-align:center;font-size:2rem;font-weight:800;padding:8px 12px;'
        f'border:1px solid #d1d5db;border-radius:12px;background:white;margin-bottom:8px;">'
        f'{format_timer(current_elapsed_seconds())}</div>',
        unsafe_allow_html=True,
    )
    minus_col, toggle_col, plus_col = st.columns([1, 2, 1])
    with minus_col:
        if st.button("−", key="timer_minus", use_container_width=True):
            adjust_timer(-1)
            st.rerun(scope="fragment")
    with toggle_col:
        label = "■ Arrêter" if st.session_state.shooting_timer_running else "▶ Démarrer"
        if st.button(label, key="timer_toggle", type="primary" if not st.session_state.shooting_timer_running else "secondary", use_container_width=True):
            stop_timer() if st.session_state.shooting_timer_running else start_timer()
            st.rerun(scope="fragment")
    with plus_col:
        if st.button("+", key="timer_plus", use_container_width=True):
            adjust_timer(1)
            st.rerun(scope="fragment")

with timer_col:
    timer_fragment()

current_step = int(st.session_state.shooting_step)
labels = ["1. Joueur", "2. Spot", "3. Réussis", "4. Tentés"]
step_html = "".join(
    f'<div class="shooting-step{" active" if i == current_step else ""}">{label}</div>'
    for i, label in enumerate(labels, start=1)
)
st.markdown(f'<div class="shooting-steps">{step_html}</div>', unsafe_allow_html=True)

context = [f"Contexte : {SHOOTING_CONTEXTS[st.session_state.shooting_context]}"]
if st.session_state.shooting_player_name:
    context.append(f"Joueur : {st.session_state.shooting_player_name}")
if st.session_state.shooting_zone_label:
    context.append(f"Spot : {st.session_state.shooting_zone_label}")
if current_step >= 4:
    context.append(f"Réussis : {st.session_state.shooting_made}")
st.markdown(f'<div class="shooting-context">{" · ".join(context)}</div>', unsafe_allow_html=True)

if st.session_state.get("shooting_success_message"):
    st.success(st.session_state.pop("shooting_success_message"))

if current_step == 1:
    players = get_players()
    if not players:
        st.warning("Aucun joueur actif. Ajoute d'abord les joueurs dans le module Joueurs.")
    else:
        for start in range(0, len(players), 4):
            row_players = players[start:start + 4]
            columns = st.columns(4)
            for index, player in enumerate(row_players):
                with columns[index]:
                    if st.button(player_button_label(player), key=f"player_{player['id']}", use_container_width=True):
                        select_player(player)
                        st.rerun()
    _ = st.button("← Retour", disabled=True, use_container_width=True)

elif current_step == 2:
    for start in range(0, len(ZONES), 3):
        row_zones = ZONES[start:start + 3]
        columns = st.columns(3)
        for index, (zone_code, zone_label) in enumerate(row_zones):
            with columns[index]:
                if st.button(zone_label, key=f"zone_{zone_code}", use_container_width=True):
                    select_zone(zone_code, zone_label)
                    st.rerun()
    if st.button("← Retour", use_container_width=True):
        reset_entry(change_player=True)
        st.rerun()

elif current_step == 3:
    st.markdown(f'<div class="shooting-number">{st.session_state.shooting_made}</div>', unsafe_allow_html=True)
    render_number_pad("shooting_made")
    back_col, next_col = st.columns(2)
    with back_col:
        if st.button("← Retour", key="made_back", use_container_width=True):
            st.session_state.shooting_step = 2
            st.rerun()
    with next_col:
        if st.button("Suivant →", key="made_next", type="primary", use_container_width=True):
            if st.session_state.shooting_lock_attempted:
                st.session_state.shooting_attempted = str(
                    int(st.session_state.shooting_lock_attempted_value)
                )
            st.session_state.shooting_step = 4
            st.rerun()

elif current_step == 4:
    st.markdown(f'<div class="shooting-number">{st.session_state.shooting_attempted}</div>', unsafe_allow_html=True)

    if st.session_state.shooting_lock_attempted:
        st.info(
            "Les tirs tentés sont verrouillés sur "
            f"{st.session_state.shooting_lock_attempted_value}."
        )
    else:
        render_number_pad("shooting_attempted")
    made = int(st.session_state.shooting_made or 0)
    attempted = int(st.session_state.shooting_attempted or 0)
    st.markdown(
        f'<div class="shooting-summary">{st.session_state.shooting_player_name} · '
        f'{SHOOTING_CONTEXTS[st.session_state.shooting_context]} · {st.session_state.shooting_zone_label} → {made}/{attempted}</div>',
        unsafe_allow_html=True,
    )
    if attempted < made:
        st.error("Le nombre de tirs tentés doit être supérieur ou égal au nombre de tirs réussis.")
    back_col, send_col = st.columns(2)
    with back_col:
        if st.button("← Retour", key="attempted_back", use_container_width=True):
            if st.session_state.shooting_lock_made:
                st.session_state.shooting_step = 2
            else:
                st.session_state.shooting_step = 3
            st.rerun()
    with send_col:
        if st.button("Envoyer ✅", key="attempted_send", type="primary", use_container_width=True, disabled=attempted < made):
            save_shooting_entry()
    same_col, change_col = st.columns(2)
    with same_col:
        if st.button("Nouvelle saisie — même joueur", key="same_player", use_container_width=True):
            reset_entry(change_player=False)
            st.rerun()
    with change_col:
        if st.button("Changer de joueur", key="change_player", use_container_width=True):
            reset_entry(change_player=True)
            st.rerun()