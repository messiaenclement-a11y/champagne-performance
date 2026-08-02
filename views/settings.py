import pandas as pd
import streamlit as st

from components.layout import page_header
from services.supabase_client import (
    fetch_all,
    test_connection,
    upsert_rows,
)


page_header(
    "Paramètres",
    "Configuration générale de la V1",
)


# -------------------------------------------------------------------
# Vérification de la connexion Supabase
# -------------------------------------------------------------------
connection_ok, connection_message = test_connection()

if connection_ok:
    st.success(connection_message)
else:
    st.error(connection_message)


# -------------------------------------------------------------------
# Chargement des paramètres existants
# -------------------------------------------------------------------
settings = fetch_all("app_settings")

current_settings = {
    row["key"]: row.get("value")
    for row in settings
}


# -------------------------------------------------------------------
# Formulaire des paramètres
# -------------------------------------------------------------------
with st.form("settings_form"):
    club_name = st.text_input(
        "Nom du club",
        value=current_settings.get(
            "club_name",
            "Champagne Basket Formation",
        ),
    )

    season = st.text_input(
        "Saison en cours",
        value=current_settings.get(
            "season",
            "2026-2027",
        ),
    )

    shooting_min_attempts = st.number_input(
        "Minimum de tirs pour la stabilité",
        min_value=1,
        max_value=1000,
        value=int(
            current_settings.get(
                "shooting_min_attempts",
                10,
            )
        ),
        step=1,
    )

    jump_orange_threshold = st.number_input(
        "Seuil orange saut (%)",
        value=float(
            current_settings.get(
                "jump_orange_threshold",
                -5,
            )
        ),
        step=0.5,
    )

    jump_red_threshold = st.number_input(
        "Seuil rouge saut (%)",
        value=float(
            current_settings.get(
                "jump_red_threshold",
                -10,
            )
        ),
        step=0.5,
    )

    save_settings = st.form_submit_button(
        "Enregistrer les paramètres",
        use_container_width=True,
    )


if save_settings:
    upsert_rows(
        "app_settings",
        [
            {
                "key": "club_name",
                "value": club_name.strip(),
            },
            {
                "key": "season",
                "value": season.strip(),
            },
            {
                "key": "shooting_min_attempts",
                "value": str(shooting_min_attempts),
            },
            {
                "key": "jump_orange_threshold",
                "value": str(jump_orange_threshold),
            },
            {
                "key": "jump_red_threshold",
                "value": str(jump_red_threshold),
            },
        ],
        on_conflict="key",
    )

    st.success("Paramètres enregistrés.")
    st.rerun()


# -------------------------------------------------------------------
# État de la base
# -------------------------------------------------------------------
st.subheader("État de la base")

tables = [
    "players",
    "attendance_sessions",
    "attendance_records",
    "shooting_sessions",
    "jump_tests",
    "strength_sessions",
]

table_status_rows = []

for table_name in tables:
    try:
        rows = fetch_all(table_name)

        table_status_rows.append(
            {
                "Table": table_name,
                "Nombre de lignes": len(rows),
                "Statut": "OK",
            }
        )

    except Exception as error:
        table_status_rows.append(
            {
                "Table": table_name,
                "Nombre de lignes": None,
                "Statut": f"Erreur : {error}",
            }
        )


table_status_dataframe = pd.DataFrame(
    table_status_rows
)

_ = st.dataframe(
    table_status_dataframe,
    hide_index=True,
    use_container_width=True,
)