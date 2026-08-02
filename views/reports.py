from datetime import date

import streamlit as st

from components.layout import page_header
from services.report_data import load_player_report_data
from services.report_service import build_player_report
from services.report_stats import build_report_stats
from services.supabase_client import fetch_all, upsert_rows
from utils.formatting import player_label

page_header("Rapports individuels", "Rapport mensuel PDF")
players = fetch_all("players", order="last_name")
if not players:
    st.warning("Aucun joueur.")
    st.stop()

c1, c2, c3 = st.columns(3)
pid = c1.selectbox(
    "Joueur",
    [p["id"] for p in players],
    format_func=lambda x: player_label(next(p for p in players if p["id"] == x)),
)
today = date.today()
month = c2.selectbox("Mois", list(range(1, 13)), index=today.month - 1)
year = c3.number_input("Année", 2020, 2100, today.year)
rm = date(int(year), int(month), 1)
player = next(p for p in players if p["id"] == pid)

existing = fetch_all("staff_comments", filters={"player_id": pid, "report_month": rm.isoformat()})
author_default = existing[0].get("author") if existing else ""
comment_default = existing[0].get("comment") if existing else ""

with st.expander("Commentaire du staff", expanded=True):
    author = st.text_input("Auteur", value=author_default or "")
    comment = st.text_area(
        "Bilan mensuel / commentaire du staff",
        value=comment_default or "",
        height=150,
        placeholder="Points forts, axe prioritaire, objectif du prochain mois…",
    )
    if st.button("Enregistrer le commentaire", use_container_width=True):
        upsert_rows(
            "staff_comments",
            [{"player_id": pid, "report_month": rm.isoformat(), "comment": comment.strip(), "author": author.strip() or None}],
            "player_id,report_month",
        )
        st.success("Commentaire enregistré.")

try:
    data = load_player_report_data(player, int(year), int(month))
    stats = build_report_stats(data)
    a = stats["attendance"]
    s = stats["shooting"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Présence", f"{a['rate']:.0f}%", f"{a['present']}/{a['total']}")
    k2.metric("Tir global", f"{s['pct']:.1f}%", f"{s['made']}/{s['attempted']}")
    transfer = s["transfers"]["passage_mouvement"]
    k3.metric("Passage au mouvement", "—" if transfer is None else f"{transfer:.0f}%")
    k4.metric("Stabilité", "—" if s["stability"]["score"] is None else f"{s['stability']['score']:.0f}/100", s["stability"]["label"])

    pdf = build_player_report(player, int(year), int(month))
    st.download_button(
        "Télécharger le nouveau rapport PDF",
        pdf,
        file_name=f"rapport_{player.get('last_name', 'joueur')}_{year}_{month:02d}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )
except Exception as exc:
    st.error("Le rapport n'a pas pu être généré.")
    st.exception(exc)
