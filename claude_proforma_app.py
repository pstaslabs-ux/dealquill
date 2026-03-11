import streamlit as st

st.set_page_config(
    page_title="DealQuill",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("pages/Analyzer.py", title="Analyzer", icon="🏢"),
    st.Page("pages/1_History.py", title="History", icon="📋"),
])
pg.run()
