import streamlit as st
from utils.constants import APP_NAME,CLUB_NAME
def page_header(title,subtitle=None):
    st.title(title)
    if subtitle: st.caption(subtitle)
def sidebar_brand():
    st.sidebar.markdown(f"## {APP_NAME}")
    st.sidebar.caption(CLUB_NAME)
    st.sidebar.divider()
