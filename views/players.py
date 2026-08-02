from datetime import date
import pandas as pd
import streamlit as st
from components.layout import page_header
from services.supabase_client import fetch_all,insert_row,update_row,upload_player_photo
from utils.constants import PLAYER_CATEGORIES,PLAYER_POSITIONS,PLAYER_STATUSES
from utils.formatting import player_label

page_header("Joueurs","Créer, modifier et archiver les joueurs")
players=fetch_all("players",order="last_name")
tabs=st.tabs(["Liste","Ajouter","Modifier"])
with tabs[0]:
    active_only=st.toggle("Afficher uniquement les joueurs actifs",True)
    shown=[p for p in players if p.get("is_active")] if active_only else players
    if shown:
        st.dataframe(pd.DataFrame([{"Nom":player_label(p),"Catégorie":p.get("category"),"Poste":p.get("position"),"Statut":p.get("status"),"Actif":"Oui" if p.get("is_active") else "Non"} for p in shown]),hide_index=True,use_container_width=True)
    else: st.info("Aucun joueur.")
with tabs[1]:
    with st.form("add_player",clear_on_submit=True):
        c1,c2=st.columns(2)
        first=c1.text_input("Prénom *"); last=c2.text_input("Nom *")
        birth=c1.date_input("Date de naissance",value=None)
        pos=c2.selectbox("Poste",[""]+PLAYER_POSITIONS)
        cat=c1.selectbox("Catégorie",PLAYER_CATEGORIES)
        status=c2.selectbox("Statut",PLAYER_STATUSES)
        arrival=c1.date_input("Date d'arrivée",date.today())
        photo=c2.file_uploader("Photo",type=["jpg","jpeg","png"])
        submit=st.form_submit_button("Ajouter le joueur",use_container_width=True)
    if submit:
        if not first.strip() or not last.strip(): st.error("Prénom et nom obligatoires.")
        else:
            row=insert_row("players",{"first_name":first.strip(),"last_name":last.strip().upper(),"birth_date":birth.isoformat() if birth else None,"position":pos or None,"category":cat,"status":status,"arrival_date":arrival.isoformat(),"is_active":True})
            if photo:
                url=upload_player_photo(row["id"],photo.name,photo.getvalue(),photo.type)
                update_row("players",row["id"],{"photo_url":url})
            st.success("Joueur ajouté."); st.rerun()
with tabs[2]:
    if not players: st.info("Aucun joueur à modifier.")
    else:
        pid=st.selectbox("Joueur",[p["id"] for p in players],format_func=lambda x:player_label(next(p for p in players if p["id"]==x)))
        p=next(p for p in players if p["id"]==pid)
        with st.form("edit_player"):
            c1,c2=st.columns(2)
            first=c1.text_input("Prénom",p.get("first_name") or "")
            last=c2.text_input("Nom",p.get("last_name") or "")
            posvals=[""]+PLAYER_POSITIONS; current=p.get("position") or ""
            pos=c1.selectbox("Poste",posvals,index=posvals.index(current) if current in posvals else 0)
            cat=c2.selectbox("Catégorie",PLAYER_CATEGORIES,index=PLAYER_CATEGORIES.index(p.get("category")) if p.get("category") in PLAYER_CATEGORIES else 0)
            status=c1.selectbox("Statut",PLAYER_STATUSES,index=PLAYER_STATUSES.index(p.get("status")) if p.get("status") in PLAYER_STATUSES else 0)
            active=c2.toggle("Joueur actif",bool(p.get("is_active")))
            photo=st.file_uploader("Remplacer la photo",type=["jpg","jpeg","png"])
            save=st.form_submit_button("Enregistrer",use_container_width=True)
        if save:
            update_row("players",pid,{"first_name":first.strip(),"last_name":last.strip().upper(),"position":pos or None,"category":cat,"status":status,"is_active":active})
            if photo:
                url=upload_player_photo(pid,photo.name,photo.getvalue(),photo.type)
                update_row("players",pid,{"photo_url":url})
            st.success("Modifications enregistrées."); st.rerun()
