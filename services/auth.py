import hmac
import streamlit as st

def require_access():
    if st.session_state.get("authenticated"): return
    st.title("Champagne Performance")
    st.caption("Accès réservé au staff")
    with st.form("login"):
        code=st.text_input("Code d'accès",type="password")
        ok=st.form_submit_button("Se connecter",use_container_width=True)
    if ok:
        expected=str(st.secrets.get("APP_ACCESS_CODE",""))
        if expected and hmac.compare_digest(code,expected):
            st.session_state.authenticated=True
            st.rerun()
        st.error("Code incorrect.")
    st.stop()

def logout_button():
    if st.sidebar.button("Se déconnecter",use_container_width=True):
        st.session_state.clear()
        st.rerun()
