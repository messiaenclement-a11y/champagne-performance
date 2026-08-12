from __future__ import annotations

import time
from datetime import date
from math import pi

import matplotlib.pyplot as plt
import streamlit as st

from services.supabase_client import get_supabase
from utils.formatting import player_label


# ============================================================
# CONFIGURATION
# ============================================================

CLUB_DARK = "#1A2434"
CLUB_BLUE = "#04B3EA"
CLUB_GOLD = "#B8A05A"

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
    "shooting_context": "statique_sans_opposition",
    "shooting_session_date": date.today(),

    "shooting_lock_made": False,
    "shooting_lock_attempted": False,
    "shooting_lock_made_value": 0,
    "shooting_lock_attempted_value": 10,

    "shooting_timer_running": False,
    "shooting_timer_started_at": None,
    "shooting_elapsed_seconds": 0,

    "shooting_sync_ack": 0,
    "shooting_open_report": False,
}

for key, value in STATE_DEFAULTS.items():
    st.session_state.setdefault(key, value)


# ============================================================
# STYLE STREAMLIT
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1800px;
    }

    div[data-testid="stExpander"] details {
        border: 0;
    }

    div[data-testid="stExpander"] summary {
        background: #1A2434;
        color: white;
        border-radius: 14px;
        padding: 12px 18px;
        font-weight: 800;
    }

    div[data-testid="stExpander"] summary p {
        color: white;
        font-size: 1.25rem;
        font-weight: 800;
    }

    .report-card {
        background: white;
        border: 1px solid #e4e8ee;
        border-radius: 16px;
        padding: 16px 18px;
        min-height: 110px;
        box-shadow: 0 3px 12px rgba(26, 36, 52, .05);
    }

    .report-card-label {
        color: #6b7280;
        font-size: .8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .04em;
    }

    .report-card-value {
        color: #1A2434;
        font-size: 2rem;
        line-height: 1.1;
        font-weight: 850;
        margin-top: 8px;
    }

    .report-card-sub {
        color: #8a94a3;
        font-size: .78rem;
        margin-top: 6px;
    }

    .report-section-title {
        background: #1A2434;
        color: white;
        border-radius: 10px;
        padding: 9px 13px;
        font-size: .9rem;
        font-weight: 800;
        margin: 12px 0;
    }

    .ranking-header,
    .ranking-row {
        display: grid;
        grid-template-columns: 42px 1fr 100px 85px;
        align-items: center;
        gap: 8px;
    }

    .ranking-header {
        color: #8a94a3;
        font-size: .73rem;
        font-weight: 700;
        padding: 5px 10px;
    }

    .ranking-row {
        background: white;
        border: 1px solid #e8ebef;
        border-radius: 11px;
        padding: 10px;
        margin-bottom: 7px;
    }

    .ranking-row.top {
        border-left: 5px solid #B8A05A;
        background: #fcfaf4;
    }

    .ranking-rank {
        font-weight: 850;
        color: #1A2434;
    }

    .ranking-name {
        font-weight: 750;
        color: #1A2434;
    }

    .ranking-pct {
        font-weight: 850;
        color: #1A2434;
        text-align: right;
    }

    .ranking-volume {
        color: #7c8796;
        text-align: right;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# JOUEURS
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
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


# ============================================================
# CHRONOMÈTRE
# ============================================================

def current_elapsed_seconds() -> int:
    elapsed = int(st.session_state.shooting_elapsed_seconds or 0)

    if (
        st.session_state.shooting_timer_running
        and st.session_state.shooting_timer_started_at
    ):
        elapsed += int(
            time.time()
            - float(st.session_state.shooting_timer_started_at)
        )

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


def adjust_timer(seconds: int) -> None:
    was_running = st.session_state.shooting_timer_running

    st.session_state.shooting_elapsed_seconds = max(
        0,
        current_elapsed_seconds() + seconds,
    )

    if was_running:
        st.session_state.shooting_timer_started_at = time.time()


@st.fragment(run_every="1s")
def timer_fragment() -> None:

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:2rem;
            font-weight:850;
            padding:8px 12px;
            border:1px solid #d1d5db;
            border-radius:12px;
            background:white;
            margin-bottom:8px;
        ">
            {format_timer(current_elapsed_seconds())}
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 2, 1])

    with c1:
        if st.button("−", key="timer_minus", use_container_width=True):
            adjust_timer(-1)

    with c2:
        label = (
            "■ Arrêter"
            if st.session_state.shooting_timer_running
            else "▶ Démarrer"
        )

        if st.button(
            label,
            key="timer_toggle",
            type="primary",
            use_container_width=True,
        ):
            if st.session_state.shooting_timer_running:
                stop_timer()
            else:
                start_timer()

    with c3:
        if st.button("+", key="timer_plus", use_container_width=True):
            adjust_timer(1)


# ============================================================
# SYNCHRONISATION SUPABASE
# ============================================================

def sync_entries(entries: list[dict]) -> int:
    """
    Enregistre les tirs stockés localement dans le navigateur.
    Les entrées sont d'abord regroupées afin de limiter le nombre
    d'opérations Supabase.
    """

    if not entries:
        return 0

    db = get_supabase()

    # Regroupement :
    # date + joueur + zone + contexte
    grouped = {}

    for entry in entries:
        key = (
            entry["date"],
            entry["player_id"],
            entry["zone"],
            entry["context"],
        )

        if key not in grouped:
            grouped[key] = {
                "made": 0,
                "attempted": 0,
            }

        grouped[key]["made"] += int(entry["made"])
        grouped[key]["attempted"] += int(entry["attempted"])

    session_cache = {}
    duration = current_elapsed_seconds()

    for (
        session_date,
        player_id,
        zone,
        context,
    ), values in grouped.items():

        session_key = (session_date, player_id)

        # ----------------------------------------------------
        # SESSION JOUEUR / DATE
        # ----------------------------------------------------

        if session_key not in session_cache:

            sessions = (
                db.table("shooting_sessions")
                .select("*")
                .eq("player_id", player_id)
                .eq("session_date", session_date)
                .limit(1)
                .execute()
                .data
                or []
            )

            if sessions:
                session = sessions[0]

                (
                    db.table("shooting_sessions")
                    .update({"duration_seconds": duration})
                    .eq("id", session["id"])
                    .execute()
                )

            else:
                response = (
                    db.table("shooting_sessions")
                    .insert(
                        {
                            "player_id": player_id,
                            "session_date": session_date,
                            "duration_seconds": duration,
                            "comment": None,
                        }
                    )
                    .execute()
                )

                session = response.data[0]

            session_cache[session_key] = session

        session = session_cache[session_key]

        # ----------------------------------------------------
        # RÉSULTAT SPOT / CONTEXTE
        # ----------------------------------------------------

        existing = (
            db.table("shooting_results")
            .select("*")
            .eq("shooting_session_id", session["id"])
            .eq("zone", zone)
            .eq("context", context)
            .limit(1)
            .execute()
            .data
            or []
        )

        if existing:
            result = existing[0]

            (
                db.table("shooting_results")
                .update(
                    {
                        "made":
                            int(result.get("made") or 0)
                            + values["made"],

                        "attempted":
                            int(result.get("attempted") or 0)
                            + values["attempted"],
                    }
                )
                .eq("id", result["id"])
                .execute()
            )

        else:
            (
                db.table("shooting_results")
                .insert(
                    {
                        "shooting_session_id": session["id"],
                        "zone": zone,
                        "context": context,
                        "made": values["made"],
                        "attempted": values["attempted"],
                    }
                )
                .execute()
            )

    return len(entries)


# ============================================================
# DONNÉES BILAN
# ============================================================

def get_collective_session_data(session_date: date) -> dict:

    db = get_supabase()

    sessions = (
        db.table("shooting_sessions")
        .select("*")
        .eq("session_date", session_date.isoformat())
        .execute()
        .data
        or []
    )

    if not sessions:
        return {
            "sessions": [],
            "results": [],
            "players": {},
        }

    session_ids = [s["id"] for s in sessions]

    results = (
        db.table("shooting_results")
        .select("*")
        .in_("shooting_session_id", session_ids)
        .execute()
        .data
        or []
    )

    player_ids = list(
        {
            s["player_id"]
            for s in sessions
            if s.get("player_id")
        }
    )

    player_rows = (
        db.table("players")
        .select("*")
        .in_("id", player_ids)
        .execute()
        .data
        or []
        if player_ids
        else []
    )

    return {
        "sessions": sessions,
        "results": results,
        "players": {
            player["id"]: player
            for player in player_rows
        },
    }


def get_previous_shooting_date(current_date: date):

    rows = (
        get_supabase()
        .table("shooting_sessions")
        .select("session_date")
        .lt("session_date", current_date.isoformat())
        .order("session_date", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )

    if not rows:
        return None

    return date.fromisoformat(rows[0]["session_date"])


def calculate_session_summary(session_date: date) -> dict:

    data = get_collective_session_data(session_date)

    sessions = data["sessions"]
    results = data["results"]
    players = data["players"]

    session_to_player = {
        session["id"]: session["player_id"]
        for session in sessions
    }

    total_attempted = sum(
        int(result.get("attempted") or 0)
        for result in results
    )

    total_made = sum(
        int(result.get("made") or 0)
        for result in results
    )

    percentage = (
        total_made / total_attempted * 100
        if total_attempted
        else 0
    )

    duration = max(
        [
            int(session.get("duration_seconds") or 0)
            for session in sessions
        ],
        default=0,
    )

    shots_per_5 = (
        total_attempted / duration * 300
        if duration
        else 0
    )

    # --------------------------------------------------------
    # JOUEURS
    # --------------------------------------------------------

    player_stats = {}

    for result in results:

        player_id = session_to_player.get(
            result["shooting_session_id"]
        )

        if not player_id:
            continue

        player = players.get(player_id, {})

        if player_id not in player_stats:
            player_stats[player_id] = {
                "name": player_button_label(player),
                "made": 0,
                "attempted": 0,
            }

        player_stats[player_id]["made"] += int(
            result.get("made") or 0
        )

        player_stats[player_id]["attempted"] += int(
            result.get("attempted") or 0
        )

    ranking = []

    for stat in player_stats.values():

        attempted = stat["attempted"]

        pct = (
            stat["made"] / attempted * 100
            if attempted
            else 0
        )

        ranking.append(
            {
                **stat,
                "percentage": pct,
            }
        )

    # Classement par %.
    # Le volume départage uniquement une égalité parfaite.
    ranking.sort(
        key=lambda row: (
            row["percentage"],
            row["attempted"],
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # SPOTS
    # --------------------------------------------------------

    zones = {
        code: {
            "made": 0,
            "attempted": 0,
        }
        for code, _ in ZONES
    }

    for result in results:

        zone = result.get("zone")

        if zone not in zones:
            continue

        zones[zone]["made"] += int(
            result.get("made") or 0
        )

        zones[zone]["attempted"] += int(
            result.get("attempted") or 0
        )

    zone_percentages = {}

    for code, _ in ZONES:

        attempted = zones[code]["attempted"]

        zone_percentages[code] = (
            zones[code]["made"] / attempted * 100
            if attempted
            else 0
        )

    return {
        "total_attempted": total_attempted,
        "total_made": total_made,
        "success_pct": percentage,
        "duration_seconds": duration,
        "shots_per_5_min": shots_per_5,
        "ranking": ranking,
        "player_of_day":
            ranking[0]["name"]
            if ranking
            else "—",
        "zones": zone_percentages,
    }


# ============================================================
# RADAR
# ============================================================

def create_session_radar(
    current_summary: dict,
    previous_summary: dict | None,
):

    labels = [label for _, label in ZONES]

    current = [
        current_summary["zones"][code]
        for code, _ in ZONES
    ]

    previous = (
        [
            previous_summary["zones"][code]
            for code, _ in ZONES
        ]
        if previous_summary
        else None
    )

    count = len(labels)

    angles = [
        n / count * 2 * pi
        for n in range(count)
    ]

    angles += angles[:1]
    current += current[:1]

    if previous:
        previous += previous[:1]

    fig, ax = plt.subplots(
        figsize=(6.3, 5.6),
        subplot_kw={"polar": True},
    )

    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fbfcfd")

    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(
        labels,
        fontsize=9,
        color=CLUB_DARK,
        fontweight="bold",
    )

    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(
        ["20", "40", "60", "80", "100"],
        fontsize=8,
        color="#7c8796",
    )

    ax.spines["polar"].set_color("#d9dee5")
    ax.grid(color="#dfe4ea", linewidth=.8)

    ax.plot(
        angles,
        current,
        color=CLUB_GOLD,
        linewidth=2.8,
        label="Séance actuelle",
    )

    ax.fill(
        angles,
        current,
        color=CLUB_GOLD,
        alpha=.18,
    )

    if previous:

        ax.plot(
            angles,
            previous,
            color=CLUB_BLUE,
            linewidth=2.3,
            label="Séance précédente",
        )

        ax.fill(
            angles,
            previous,
            color=CLUB_BLUE,
            alpha=.07,
        )

    ax.legend(
        loc="lower center",
        bbox_to_anchor=(.5, -.18),
        ncol=2,
        frameon=False,
        fontsize=9,
    )

    fig.tight_layout()

    return fig


# ============================================================
# BILAN
# ============================================================

@st.dialog(
    "Bilan de fin de séance",
    width="large",
)
def show_session_report():

    session_date = (
        st.session_state.shooting_session_date
    )

    summary = calculate_session_summary(
        session_date
    )

    if not summary["total_attempted"]:
        st.warning(
            "Aucun tir enregistré pour cette séance."
        )
        return

    previous_date = get_previous_shooting_date(
        session_date
    )

    previous_summary = (
        calculate_session_summary(previous_date)
        if previous_date
        else None
    )

    st.markdown(
        f"""
        <div style="
            margin-bottom:14px;
            color:#7c8796;
            font-size:.9rem;
        ">
            {session_date.strftime("%d/%m/%Y")}
            · {summary["total_made"]}/{summary["total_attempted"]} tirs réussis
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # CARTES
    # --------------------------------------------------------

    cards = st.columns(4)

    values = [
        (
            "Tirs tentés",
            str(summary["total_attempted"]),
            "Volume collectif",
        ),
        (
            "Tirs / 5 min",
            f'{summary["shots_per_5_min"]:.1f}',
            "Rythme de séance",
        ),
        (
            "% réussite",
            f'{summary["success_pct"]:.1f} %',
            f'{summary["total_made"]}/{summary["total_attempted"]}',
        ),
        (
            "Joueur du jour",
            summary["player_of_day"],
            "Meilleur % de réussite",
        ),
    ]

    for col, (label, value, sub) in zip(
        cards,
        values,
    ):
        with col:
            st.markdown(
                f"""
                <div class="report-card">
                    <div class="report-card-label">{label}</div>
                    <div class="report-card-value">{value}</div>
                    <div class="report-card-sub">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # RADAR + CLASSEMENT
    # --------------------------------------------------------

    st.markdown(
        '<div class="report-section-title">'
        'PERFORMANCE COLLECTIVE & CLASSEMENT'
        '</div>',
        unsafe_allow_html=True,
    )

    radar_col, ranking_col = st.columns(
        [1.15, 1],
        gap="large",
    )

    with radar_col:

        fig = create_session_radar(
            summary,
            previous_summary,
        )

        st.pyplot(
            fig,
            use_container_width=True,
        )

        plt.close(fig)

    with ranking_col:

        st.markdown(
            f"""
            <div style="
                font-size:1.2rem;
                font-weight:850;
                color:#1A2434;
                margin-bottom:3px;
            ">
                Classement de la séance
            </div>

            <div style="
                color:#7c8796;
                font-size:.82rem;
                margin-bottom:10px;
            ">
                Tous les joueurs · classement par % de réussite
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="ranking-header">
                <div>#</div>
                <div>Joueur</div>
                <div style="text-align:right;">Réussite</div>
                <div style="text-align:right;">Tirs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        ranking_html = ""

        for index, player in enumerate(
            summary["ranking"],
            start=1,
        ):

            row_class = (
                "ranking-row top"
                if index == 1
                else "ranking-row"
            )

            ranking_html += f"""
                <div class="{row_class}">
                    <div class="ranking-rank">{index}</div>
                    <div class="ranking-name">{player["name"]}</div>
                    <div class="ranking-pct">
                        {player["percentage"]:.1f} %
                    </div>
                    <div class="ranking-volume">
                        {player["made"]}/{player["attempted"]}
                    </div>
                </div>
            """

        st.markdown(
            ranking_html,
            unsafe_allow_html=True,
        )


# ============================================================
# CALLBACKS DU MODE TURBO
# ============================================================

def component_payload(trigger_name: str):
    component_state = st.session_state.get(
        "shooting_turbo_component"
    )

    if component_state is None:
        return None

    try:
        return getattr(
            component_state,
            trigger_name,
        )
    except Exception:
        return None


def handle_sync():
    payload = component_payload("sync")

    if not payload:
        return

    entries = payload.get("entries") or []

    if not entries:
        st.toast(
            "Aucun tir à synchroniser.",
            icon="✅",
        )
        return

    try:
        count = sync_entries(entries)

        st.session_state.shooting_sync_ack += 1

        st.toast(
            f"{count} saisie(s) synchronisée(s).",
            icon="✅",
        )

    except Exception as exc:
        st.error(
            "Synchronisation impossible. "
            "Les tirs restent conservés sur la tablette."
        )
        st.exception(exc)


def handle_report():
    payload = component_payload("report")

    entries = (
        payload.get("entries") or []
        if payload
        else []
    )

    try:

        if entries:
            sync_entries(entries)
            st.session_state.shooting_sync_ack += 1

        stop_timer()

        st.session_state.shooting_open_report = True

    except Exception as exc:
        st.error(
            "Impossible de synchroniser avant le bilan. "
            "Les tirs restent conservés localement."
        )
        st.exception(exc)


# ============================================================
# PARAMÈTRES DE SÉANCE
# ============================================================

with st.expander(
    "SAISIE TIRS",
    expanded=True,
):

    settings_col, timer_col = st.columns(
        [1, 2]
    )

    with settings_col:

        selected_date = st.date_input(
            "Date de séance",
            value=st.session_state.shooting_session_date,
            key="shooting_date_widget",
        )

        st.session_state.shooting_session_date = (
            selected_date
        )

        st.markdown("**Contexte de tir**")

        context_keys = list(
            SHOOTING_CONTEXTS.keys()
        )

        context = st.selectbox(
            "Contexte",
            context_keys,
            format_func=lambda value:
                SHOOTING_CONTEXTS[value],
            index=context_keys.index(
                st.session_state.shooting_context
            ),
            label_visibility="collapsed",
            key="shooting_context_widget",
        )

        st.session_state.shooting_context = context

        st.markdown("**Valeurs verrouillées**")

        c1, c2 = st.columns([1.6, 1])

        with c1:
            lock_made = st.checkbox(
                "Verrouiller les réussis",
                value=st.session_state.shooting_lock_made,
            )

        with c2:
            lock_made_value = st.number_input(
                "Réussis",
                min_value=0,
                step=1,
                value=int(
                    st.session_state.shooting_lock_made_value
                ),
                disabled=not lock_made,
                label_visibility="collapsed",
            )

        c1, c2 = st.columns([1.6, 1])

        with c1:
            lock_attempted = st.checkbox(
                "Verrouiller les tentés",
                value=st.session_state.shooting_lock_attempted,
            )

        with c2:
            lock_attempted_value = st.number_input(
                "Tentés",
                min_value=0,
                step=1,
                value=int(
                    st.session_state.shooting_lock_attempted_value
                ),
                disabled=not lock_attempted,
                label_visibility="collapsed",
            )

        st.session_state.shooting_lock_made = (
            lock_made
        )

        st.session_state.shooting_lock_attempted = (
            lock_attempted
        )

        st.session_state.shooting_lock_made_value = (
            int(lock_made_value)
        )

        st.session_state.shooting_lock_attempted_value = (
            int(lock_attempted_value)
        )

    with timer_col:
        timer_fragment()


# ============================================================
# COMPOSANT TURBO
# ============================================================

TURBO_HTML = """
<div id="shooting-app">

    <div class="turbo-toolbar">
        <div>
            <div class="turbo-title">SAISIE TURBO</div>
            <div id="context-label" class="turbo-context"></div>
        </div>

        <div class="sync-area">
            <div id="pending" class="pending"></div>
            <button id="sync-btn" class="small-action">Synchroniser</button>
            <button id="report-btn" class="report-action">Bilan séance</button>
        </div>
    </div>

    <div id="steps" class="steps"></div>

    <div id="flash" class="flash"></div>

    <div id="content"></div>

</div>
"""

TURBO_CSS = """
:host {
    font-family: var(--st-font);
}

#shooting-app {
    width:100%;
    color:#1A2434;
    padding-top:5px;
}

.turbo-toolbar {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
    margin-bottom:12px;
}

.turbo-title {
    font-size:.8rem;
    font-weight:900;
    letter-spacing:.06em;
    color:#1A2434;
}

.turbo-context {
    font-size:.82rem;
    color:#7c8796;
    margin-top:2px;
}

.sync-area {
    display:flex;
    align-items:center;
    justify-content:flex-end;
    gap:7px;
    flex-wrap:wrap;
}

.pending {
    font-size:.78rem;
    font-weight:750;
    color:#7c8796;
    margin-right:5px;
}

.small-action,
.report-action {
    border:0;
    border-radius:999px;
    min-height:38px;
    padding:0 15px;
    font-weight:750;
    cursor:pointer;
    touch-action:manipulation;
}

.small-action {
    background:#eef1f5;
    color:#1A2434;
}

.report-action {
    background:#1A2434;
    color:white;
}

.steps {
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:8px;
    margin:8px 0 12px;
}

.step {
    min-height:44px;
    display:flex;
    justify-content:center;
    align-items:center;
    background:white;
    border:1px solid #d9dee5;
    border-radius:11px;
    color:#6f7987;
    font-size:.9rem;
}

.step.active {
    background:#B8A05A;
    border-color:#B8A05A;
    color:white;
    font-weight:850;
}

.button-grid {
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:12px;
}

.big-btn {
    width:100%;
    min-height:62px;
    border:1px solid #d4dae2;
    border-radius:999px;
    background:white;
    color:#111827;
    font-size:1rem;
    font-weight:650;
    cursor:pointer;
    touch-action:manipulation;
    -webkit-tap-highlight-color:transparent;
}

.big-btn:active {
    transform:scale(.985);
    background:#f4f5f7;
}

.zone-grid {
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:12px;
}

.zone-btn {
    min-height:70px;
}

.number-display {
    display:flex;
    align-items:center;
    justify-content:center;
    min-height:100px;
    border:1px solid #d4dae2;
    border-radius:16px;
    background:white;
    font-size:4rem;
    font-weight:900;
    margin-bottom:12px;
}

.numpad {
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:8px;
}

.num-btn {
    min-height:66px;
    border:1px solid #d4dae2;
    border-radius:14px;
    background:white;
    font-size:1.4rem;
    font-weight:750;
    cursor:pointer;
    touch-action:manipulation;
}

.num-btn.gold {
    background:#B8A05A;
    color:white;
    border-color:#B8A05A;
}

.nav-row {
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin-top:11px;
}

.nav-btn {
    min-height:55px;
    border-radius:999px;
    border:1px solid #d4dae2;
    background:white;
    font-weight:750;
    cursor:pointer;
}

.nav-btn.primary {
    background:#B8A05A;
    color:white;
    border-color:#B8A05A;
}

.selection-info {
    color:#707b89;
    font-size:.86rem;
    margin-bottom:10px;
}

.summary {
    background:#f2f4f7;
    border-radius:13px;
    padding:13px;
    text-align:center;
    margin-bottom:11px;
    font-weight:750;
}

.flash {
    min-height:22px;
    font-size:.85rem;
    color:#139957;
    font-weight:750;
    margin-bottom:4px;
}

.empty {
    padding:30px;
    text-align:center;
    color:#7c8796;
}

@media (max-width:900px) {

    .turbo-toolbar {
        align-items:flex-start;
    }

    .button-grid {
        grid-template-columns:repeat(4,1fr);
        gap:8px;
    }

    .big-btn {
        min-height:68px;
        font-size:.9rem;
    }

    .steps {
        gap:5px;
    }

    .step {
        font-size:.8rem;
        min-height:40px;
    }
}
"""

TURBO_JS = """
export default function(component) {

    const {
        parentElement,
        data,
        setTriggerValue
    } = component;

    const content = parentElement.querySelector("#content");
    const stepsBox = parentElement.querySelector("#steps");
    const pendingBox = parentElement.querySelector("#pending");
    const flashBox = parentElement.querySelector("#flash");
    const contextLabel = parentElement.querySelector("#context-label");
    const syncBtn = parentElement.querySelector("#sync-btn");
    const reportBtn = parentElement.querySelector("#report-btn");

    const QUEUE_KEY = "champagne_shooting_queue_v2";
    const ACK_KEY = "champagne_shooting_ack_v2";

    let queue = [];

    try {
        queue = JSON.parse(
            window.localStorage.getItem(QUEUE_KEY) || "[]"
        );
    } catch {
        queue = [];
    }

    const lastAck = Number(
        window.localStorage.getItem(ACK_KEY) || 0
    );

    if ((data.ack || 0) > lastAck) {
        queue = [];
        window.localStorage.setItem(
            QUEUE_KEY,
            JSON.stringify(queue)
        );
        window.localStorage.setItem(
            ACK_KEY,
            String(data.ack)
        );
    }

    let step = 1;
    let player = null;
    let zone = null;
    let made = "0";
    let attempted = "0";

    const saveQueue = () => {
        window.localStorage.setItem(
            QUEUE_KEY,
            JSON.stringify(queue)
        );
        updatePending();
    };

    const updatePending = () => {
        pendingBox.textContent =
            queue.length === 0
            ? "Tout est synchronisé"
            : `${queue.length} saisie(s) en attente`;
    };

    const showFlash = (text) => {
        flashBox.textContent = text;
        window.clearTimeout(window.__shootFlashTimer);
        window.__shootFlashTimer = window.setTimeout(
            () => {
                flashBox.textContent = "";
            },
            1400
        );
    };

    contextLabel.textContent = data.context_label;

    const stepLabels = [
        "1. Joueur",
        "2. Spot",
        "3. Réussis",
        "4. Tentés"
    ];

    const renderSteps = () => {
        stepsBox.innerHTML = "";

        stepLabels.forEach((label, index) => {
            const el = document.createElement("div");
            el.className =
                "step" +
                (step === index + 1 ? " active" : "");
            el.textContent = label;
            stepsBox.appendChild(el);
        });
    };

    const addInfo = () => {
        const parts = [];

        if (player) parts.push(`Joueur : ${player.name}`);
        if (zone) parts.push(`Spot : ${zone.label}`);

        if (!parts.length) return "";

        return `
            <div class="selection-info">
                ${parts.join(" · ")}
            </div>
        `;
    };

    const createButton = (
        label,
        className,
        onClick
    ) => {
        const button = document.createElement("button");
        button.className = className;
        button.textContent = label;
        button.onclick = onClick;
        return button;
    };

    const renderPlayers = () => {

        content.innerHTML = "";

        if (!data.players.length) {
            content.innerHTML =
                '<div class="empty">Aucun joueur actif.</div>';
            return;
        }

        const grid = document.createElement("div");
        grid.className = "button-grid";

        data.players.forEach((p) => {
            grid.appendChild(
                createButton(
                    p.name,
                    "big-btn",
                    () => {
                        player = p;
                        zone = null;
                        made = "0";
                        attempted = "0";
                        step = 2;
                        render();
                    }
                )
            );
        });

        content.appendChild(grid);
    };

    const renderZones = () => {

        content.innerHTML = addInfo();

        const grid = document.createElement("div");
        grid.className = "zone-grid";

        data.zones.forEach((z) => {

            grid.appendChild(
                createButton(
                    z.label,
                    "big-btn zone-btn",
                    () => {

                        zone = z;

                        made = data.lock_made
                            ? String(data.lock_made_value)
                            : "0";

                        attempted = data.lock_attempted
                            ? String(data.lock_attempted_value)
                            : "0";

                        step = data.lock_made ? 4 : 3;

                        render();
                    }
                )
            );
        });

        content.appendChild(grid);

        const back = createButton(
            "← Retour",
            "nav-btn",
            () => {
                step = 1;
                player = null;
                zone = null;
                render();
            }
        );

        const nav = document.createElement("div");
        nav.className = "nav-row";
        nav.style.gridTemplateColumns = "1fr";
        nav.appendChild(back);

        content.appendChild(nav);
    };

    const appendDigit = (field, digit) => {

        let value = field === "made"
            ? made
            : attempted;

        if (value === "0") value = "";

        value += String(digit);

        if (field === "made") made = value;
        else attempted = value;

        render();
    };

    const backspace = (field) => {

        let value = field === "made"
            ? made
            : attempted;

        value = value.slice(0, -1) || "0";

        if (field === "made") made = value;
        else attempted = value;

        render();
    };

    const clearValue = (field) => {

        if (field === "made") made = "0";
        else attempted = "0";

        render();
    };

    const renderNumpad = (field) => {

        content.innerHTML = addInfo();

        const display = document.createElement("div");
        display.className = "number-display";
        display.textContent =
            field === "made"
            ? made
            : attempted;

        content.appendChild(display);

        const pad = document.createElement("div");
        pad.className = "numpad";

        [1,2,3,4,5,6,7,8,9].forEach((digit) => {
            pad.appendChild(
                createButton(
                    String(digit),
                    "num-btn",
                    () => appendDigit(field, digit)
                )
            );
        });

        pad.appendChild(
            createButton(
                "C",
                "num-btn gold",
                () => clearValue(field)
            )
        );

        pad.appendChild(
            createButton(
                "0",
                "num-btn",
                () => appendDigit(field, 0)
            )
        );

        pad.appendChild(
            createButton(
                "⌫",
                "num-btn",
                () => backspace(field)
            )
        );

        content.appendChild(pad);

        const nav = document.createElement("div");
        nav.className = "nav-row";

        if (field === "made") {

            nav.appendChild(
                createButton(
                    "← Retour",
                    "nav-btn",
                    () => {
                        step = 2;
                        render();
                    }
                )
            );

            nav.appendChild(
                createButton(
                    "Suivant →",
                    "nav-btn primary",
                    () => {

                        if (data.lock_attempted) {
                            attempted = String(
                                data.lock_attempted_value
                            );
                        }

                        step = 4;
                        render();
                    }
                )
            );

        } else {

            nav.appendChild(
                createButton(
                    "← Retour",
                    "nav-btn",
                    () => {
                        step = data.lock_made ? 2 : 3;
                        render();
                    }
                )
            );
        }

        content.appendChild(nav);
    };

    const submitEntry = () => {

        const m = Number(made || 0);
        const a = Number(attempted || 0);

        if (m > a) {
            showFlash(
                "⚠️ Les réussis ne peuvent pas dépasser les tentés."
            );
            return;
        }

        const entry = {
            id:
                (window.crypto?.randomUUID?.())
                || `${Date.now()}-${Math.random()}`,

            date: data.date,
            context: data.context,

            player_id: player.id,
            player_name: player.name,

            zone: zone.code,
            zone_label: zone.label,

            made: m,
            attempted: a,

            created_at: Date.now()
        };

        queue.push(entry);
        saveQueue();

        showFlash(
            `✓ ${player.name} · ${zone.label} · ${m}/${a} enregistré`
        );

        // IMPORTANT :
        // aucune communication Streamlit ici.
        // Retour instantané à la sélection joueur.

        step = 1;
        player = null;
        zone = null;
        made = "0";
        attempted = "0";

        render();
    };

    const renderAttempted = () => {

        content.innerHTML = addInfo();

        const m = Number(made || 0);
        const a = Number(attempted || 0);

        const display = document.createElement("div");
        display.className = "number-display";
        display.textContent = attempted;

        content.appendChild(display);

        if (!data.lock_attempted) {

            const pad = document.createElement("div");
            pad.className = "numpad";

            [1,2,3,4,5,6,7,8,9].forEach((digit) => {
                pad.appendChild(
                    createButton(
                        String(digit),
                        "num-btn",
                        () => appendDigit("attempted", digit)
                    )
                );
            });

            pad.appendChild(
                createButton(
                    "C",
                    "num-btn gold",
                    () => clearValue("attempted")
                )
            );

            pad.appendChild(
                createButton(
                    "0",
                    "num-btn",
                    () => appendDigit("attempted", 0)
                )
            );

            pad.appendChild(
                createButton(
                    "⌫",
                    "num-btn",
                    () => backspace("attempted")
                )
            );

            content.appendChild(pad);
        }

        const summary = document.createElement("div");
        summary.className = "summary";
        summary.textContent =
            `${player.name} · ${zone.label} → ${m}/${a}`;

        content.appendChild(summary);

        const nav = document.createElement("div");
        nav.className = "nav-row";

        nav.appendChild(
            createButton(
                "← Retour",
                "nav-btn",
                () => {
                    step = data.lock_made ? 2 : 3;
                    render();
                }
            )
        );

        nav.appendChild(
            createButton(
                "Envoyer ✓",
                "nav-btn primary",
                submitEntry
            )
        );

        content.appendChild(nav);
    };

    const render = () => {

        renderSteps();
        updatePending();

        if (step === 1) renderPlayers();
        else if (step === 2) renderZones();
        else if (step === 3) renderNumpad("made");
        else if (step === 4) renderAttempted();
    };

    syncBtn.onclick = () => {

        if (!queue.length) {
            showFlash("✓ Rien à synchroniser");
            return;
        }

        setTriggerValue(
            "sync",
            {
                entries: [...queue],
                sent_at: Date.now()
            }
        );
    };

    reportBtn.onclick = () => {

        setTriggerValue(
            "report",
            {
                entries: [...queue],
                sent_at: Date.now()
            }
        );
    };

    render();
}
"""


shooting_component = st.components.v2.component(
    name="champagne_shooting_turbo",
    html=TURBO_HTML,
    css=TURBO_CSS,
    js=TURBO_JS,
)


players = get_players()

component_players = [
    {
        "id": player["id"],
        "name": player_button_label(player),
    }
    for player in players
]

component_zones = [
    {
        "code": code,
        "label": label,
    }
    for code, label in ZONES
]


shooting_component(
    data={
        "players": component_players,
        "zones": component_zones,

        "date":
            st.session_state
            .shooting_session_date
            .isoformat(),

        "context":
            st.session_state
            .shooting_context,

        "context_label":
            SHOOTING_CONTEXTS[
                st.session_state.shooting_context
            ],

        "lock_made":
            st.session_state
            .shooting_lock_made,

        "lock_made_value":
            int(
                st.session_state
                .shooting_lock_made_value
            ),

        "lock_attempted":
            st.session_state
            .shooting_lock_attempted,

        "lock_attempted_value":
            int(
                st.session_state
                .shooting_lock_attempted_value
            ),

        "ack":
            st.session_state
            .shooting_sync_ack,
    },

    key="shooting_turbo_component",

    on_sync_change=handle_sync,
    on_report_change=handle_report,

    width="stretch",
    height="content",
)


# ============================================================
# OUVERTURE DU BILAN APRÈS SYNCHRONISATION
# ============================================================

if st.session_state.pop(
    "shooting_open_report",
    False,
):
    show_session_report()