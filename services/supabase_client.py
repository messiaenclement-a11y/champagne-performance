from typing import Any
import streamlit as st
from supabase import create_client

@st.cache_resource(show_spinner=False)
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SERVICE_ROLE_KEY"],
    )

def fetch_all(table, select="*", order=None, desc=False, filters=None):
    q=get_supabase().table(table).select(select)
    for k,v in (filters or {}).items():
        q=q.eq(k,v)
    if order:
        q=q.order(order, desc=desc)
    return q.execute().data or []

def insert_row(table,payload):
    return (get_supabase().table(table).insert(payload).execute().data or [{}])[0]

def insert_rows(table,payloads):
    if not payloads: return []
    return get_supabase().table(table).insert(payloads).execute().data or []

def update_row(table,row_id,payload):
    return (get_supabase().table(table).update(payload).eq("id",row_id).execute().data or [{}])[0]

def upsert_rows(table,payloads,on_conflict):
    if not payloads: return []
    return get_supabase().table(table).upsert(payloads,on_conflict=on_conflict).execute().data or []

def upload_player_photo(player_id,filename,data,content_type):
    ext=filename.rsplit(".",1)[-1].lower() if "." in filename else "jpg"
    path=f"{player_id}/profile.{ext}"
    bucket=get_supabase().storage.from_("player-photos")
    bucket.upload(path,data,{"content-type":content_type,"upsert":"true"})
    return bucket.get_public_url(path)

def test_connection():
    try:
        get_supabase().table("players").select("id").limit(1).execute()
        return True,"Connexion Supabase opérationnelle."
    except Exception as exc:
        return False,str(exc)
