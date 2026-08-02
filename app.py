import streamlit as st
from services.auth import require_access,logout_button
from components.layout import sidebar_brand

st.set_page_config(page_title="Champagne Performance",page_icon="🏀",layout="wide")
require_access()
sidebar_brand()
pages={
"Pilotage":[st.Page("views/dashboard.py",title="Tableau de bord",icon="📊",default=True)],
"Suivi sportif":[
st.Page("views/players.py",title="Joueurs",icon="👥"),
st.Page("views/attendance.py",title="Présences",icon="✅"),
st.Page("views/shooting.py",title="Tirs",icon="🏀"),
st.Page("views/jumps.py",title="Sauts",icon="🦘"),
st.Page("views/strength.py",title="Musculation",icon="🏋️")],
"Documents":[st.Page("views/reports.py",title="Rapports",icon="📄")],
"Administration":[st.Page("views/settings.py",title="Paramètres",icon="⚙️")]}
nav=st.navigation(pages)
logout_button()
_ = nav.run()
