import streamlit as st
from modules.auth import require_login, redirect_by_role

st.set_page_config(initial_sidebar_state="collapsed", page_title="Redirect")

require_login()
redirect_by_role()
st.stop()
