from datetime import date, timedelta

import streamlit as st

from components.layout import page_header
from services.supabase_client import fetch_all, test_connection


page_header(
    "Tableau de bord",
    "Vue opérationnelle du centre de formation",
)

# Vérification de la connexion à Supabase
connection_ok, connection_message = test_connection()

if not connection_ok:
    st.error("Connexion à la base de données impossible.")
    st.code(connection_message)
    st.stop()


# Dates utiles
today = date.today()
week_start = today - timedelta(days=today.weekday())


# Récupération des données
players = fetch_all(
    "players",
    filters={"is_active": True},
)

attendance_sessions_today = fetch_all(
    "attendance_sessions",
    filters={"session_date": today.isoformat()},
)

shooting_sessions = fetch_all("shooting_sessions")
jump_tests = fetch_all("jump_tests")


# Données de la semaine
shooting_sessions_this_week = [
    session
    for session in shooting_sessions
    if session.get("session_date", "") >= week_start.isoformat()
]

jump_tests_this_week = [
    test
    for test in jump_tests
    if test.get("test_date", "") >= week_start.isoformat()
]


# Indicateurs principaux
metric_1, metric_2, metric_3, metric_4 = st.columns(4)

with metric_1:
    st.metric(
        label="Joueurs actifs",
        value=len(players),
    )

with metric_2:
    st.metric(
        label="Séances aujourd'hui",
        value=len(attendance_sessions_today),
    )

with metric_3:
    st.metric(
        label="Tirs cette semaine",
        value=len(shooting_sessions_this_week),
    )

with metric_4:
    st.metric(
        label="Tests de saut",
        value=len(jump_tests_this_week),
    )


# Accès rapides
st.subheader("Accès rapides")

quick_1, quick_2, quick_3, quick_4 = st.columns(4)

with quick_1:
    st.page_link(
        "views/attendance.py",
        label="Faire les présences",
        icon="✅",
        use_container_width=True,
    )

with quick_2:
    st.page_link(
        "views/shooting.py",
        label="Saisir une séance de tir",
        icon="🏀",
        use_container_width=True,
    )

with quick_3:
    st.page_link(
        "views/jumps.py",
        label="Saisir un test de saut",
        icon="🦘",
        use_container_width=True,
    )

with quick_4:
    st.page_link(
        "views/strength.py",
        label="Ouvrir la musculation",
        icon="🏋️",
        use_container_width=True,
    )


# Alertes
st.subheader("Alertes")

red_jump_tests = [
    test
    for test in jump_tests_this_week
    if test.get("fatigue_status") == "Rouge"
]

if red_jump_tests:
    st.error(
        f"{len(red_jump_tests)} test(s) de saut "
        f"en statut rouge cette semaine."
    )
else:
    st.success("Aucune alerte rouge cette semaine.")