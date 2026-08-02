from datetime import date, datetime

import pandas as pd
import streamlit as st

from components.layout import page_header
from services.supabase_client import fetch_all, insert_row, upsert_rows
from utils.constants import ATTENDANCE_STATUSES, ATTENDANCE_TYPES
from utils.formatting import player_label


page_header(
    "Présences",
    "Saisie collective rapide",
)

players = fetch_all(
    "players",
    order="last_name",
    filters={"is_active": True},
)

sessions = fetch_all(
    "attendance_sessions",
    order="session_date",
    desc=True,
)

tab_new, tab_entry, tab_history = st.tabs(
    [
        "Nouvelle séance",
        "Saisir les présences",
        "Historique",
    ]
)


# -------------------------------------------------------------------
# Nouvelle séance
# -------------------------------------------------------------------
with tab_new:
    with st.form("new_attendance_session"):
        col_1, col_2 = st.columns(2)

        session_date = col_1.date_input(
            "Date",
            value=date.today(),
        )

        session_time = col_2.time_input(
            "Heure",
            value=datetime.now().time().replace(
                second=0,
                microsecond=0,
            ),
        )

        session_type = col_1.selectbox(
            "Type",
            ATTENDANCE_TYPES,
        )

        title = col_2.text_input(
            "Titre",
            value=session_type,
        )

        comment = st.text_area(
            "Commentaire",
        )

        submitted = st.form_submit_button(
            "Créer la séance",
            use_container_width=True,
        )

    if submitted:
        insert_row(
            "attendance_sessions",
            {
                "session_date": session_date.isoformat(),
                "session_time": session_time.isoformat(),
                "session_type": session_type,
                "title": title.strip() or session_type,
                "comment": comment.strip() or None,
            },
        )

        st.success("Séance créée.")
        st.rerun()


# -------------------------------------------------------------------
# Saisie des présences
# -------------------------------------------------------------------
with tab_entry:
    if not sessions:
        st.info("Créez d'abord une séance.")

    elif not players:
        st.info("Aucun joueur actif.")

    else:
        session_id = st.selectbox(
            "Séance",
            options=[session["id"] for session in sessions],
            format_func=lambda selected_id: next(
                (
                    f"{session['session_date']} — "
                    f"{session.get('title') or session.get('session_type')}"
                )
                for session in sessions
                if session["id"] == selected_id
            ),
        )

        existing_records = fetch_all(
            "attendance_records",
            filters={
                "attendance_session_id": session_id,
            },
        )

        records_by_player = {
            record["player_id"]: record
            for record in existing_records
        }

        attendance_rows = []

        for player in players:
            current_record = records_by_player.get(
                player["id"],
                {},
            )

            attendance_rows.append(
                {
                    "player_id": player["id"],
                    "Joueur": player_label(player),
                    "Statut": current_record.get(
                        "status",
                        "Présent",
                    ),
                    "Commentaire": current_record.get(
                        "comment",
                        "",
                    ),
                }
            )

        attendance_dataframe = pd.DataFrame(
            attendance_rows
        )

        edited_attendance = st.data_editor(
            attendance_dataframe,
            hide_index=True,
            use_container_width=True,
            disabled=[
                "player_id",
                "Joueur",
            ],
            column_config={
                "player_id": None,
                "Statut": st.column_config.SelectboxColumn(
                    "Statut",
                    options=ATTENDANCE_STATUSES,
                    required=True,
                ),
                "Commentaire": st.column_config.TextColumn(
                    "Commentaire",
                ),
            },
            key=f"attendance_editor_{session_id}",
        )

        save_attendance = st.button(
            "Enregistrer les présences",
            type="primary",
            use_container_width=True,
        )

        if save_attendance:
            payloads = []

            for row in edited_attendance.to_dict("records"):
                payloads.append(
                    {
                        "attendance_session_id": session_id,
                        "player_id": row["player_id"],
                        "status": row["Statut"],
                        "comment": row["Commentaire"] or None,
                    }
                )

            upsert_rows(
                "attendance_records",
                payloads,
                on_conflict="attendance_session_id,player_id",
            )

            st.success("Présences enregistrées.")


# -------------------------------------------------------------------
# Historique
# -------------------------------------------------------------------
with tab_history:
    if not sessions:
        st.info("Aucune séance enregistrée.")

    else:
        history_rows = []

        for session in sessions:
            history_rows.append(
                {
                    "Date": session.get("session_date"),
                    "Heure": session.get("session_time"),
                    "Type": session.get("session_type"),
                    "Titre": session.get("title"),
                    "Commentaire": session.get("comment"),
                }
            )

        history_dataframe = pd.DataFrame(
            history_rows
        )

        _ = st.dataframe(
            history_dataframe,
            hide_index=True,
            use_container_width=True,
        )