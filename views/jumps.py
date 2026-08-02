from datetime import date,timedelta
import pandas as pd
import streamlit as st
from components.layout import page_header
from services.supabase_client import fetch_all,insert_row,get_supabase
from services.calculations import official_jump,jump_variation,fatigue_status
from utils.constants import JUMP_TYPES
from utils.formatting import player_label

page_header("Sauts","3 essais obligatoires, moyenne des 2 meilleurs")
players=fetch_all("players",order="last_name",filters={"is_active":True})
if not players: st.warning("Ajoutez d'abord un joueur."); st.stop()
with st.form("jump_form"):
    c1,c2,c3=st.columns(3)
    pid=c1.selectbox("Joueur",[p["id"] for p in players],format_func=lambda x:player_label(next(p for p in players if p["id"]==x)))
    d=c2.date_input("Date",date.today()); typ=c3.selectbox("Type",JUMP_TYPES)
    j1=c1.number_input("Saut 1 (cm)",min_value=0.0,step=0.1)
    j2=c2.number_input("Saut 2 (cm)",min_value=0.0,step=0.1)
    j3=c3.number_input("Saut 3 (cm)",min_value=0.0,step=0.1)
    comment=st.text_area("Commentaire")
    go=st.form_submit_button("Enregistrer le test",use_container_width=True)
if go:
    try: score=official_jump([j1,j2,j3])
    except ValueError as exc: st.error(str(exc))
    else:
        prev=(get_supabase().table("jump_tests").select("official_score").eq("player_id",pid).eq("test_type",typ).gte("test_date",(d-timedelta(weeks=4)).isoformat()).lt("test_date",d.isoformat()).execute().data or [])
        vals=[float(x["official_score"]) for x in prev if x.get("official_score") is not None]
        ref=round(sum(vals)/len(vals),2) if vals else None
        diff_cm,diff_pct=jump_variation(score,ref); status=fatigue_status(diff_pct)
        insert_row("jump_tests",{"player_id":pid,"test_date":d.isoformat(),"test_type":typ,"jump_1":j1,"jump_2":j2,"jump_3":j3,"official_score":score,"reference_4w":ref,"difference_cm":diff_cm,"difference_pct":diff_pct,"fatigue_status":status,"comment":comment.strip() or None})
        st.success(f"Score officiel : {score} cm — Statut : {status}"); st.rerun()
tests=fetch_all("jump_tests",order="test_date",desc=True)
st.subheader("Historique")
names={p["id"]:player_label(p) for p in players}
if tests:
    st.dataframe(pd.DataFrame([{"Date":t["test_date"],"Joueur":names.get(t["player_id"],"Joueur archivé"),"Test":t["test_type"],"Score":t["official_score"],"Référence 4 sem.":t.get("reference_4w"),"Écart %":t.get("difference_pct"),"Statut":t.get("fatigue_status")} for t in tests]),hide_index=True,use_container_width=True)
