"""
When AI Agents Go Wrong — ISTE-782 VAST Challenge 2026 project website.

Run it with:   streamlit run app.py

This file only sets up the page list. Each page lives in views/,
and all the data loading/analysis lives in vastlib/.
"""
import streamlit as st

st.set_page_config(page_title="When AI Agents Go Wrong", page_icon="🔎", layout="wide")

pages = {
    "Overview": [
        st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
        st.Page("views/data_overview.py", title="The data", icon=":material/table_chart:"),
    ],
    "RQ1 · What happened": [
        st.Page("views/mc1_leak.py", title="MC1 · Embargo leak", icon=":material/campaign:"),
        st.Page("views/mc2_post.py", title="MC2 · Anomalous post", icon=":material/forum:"),
        st.Page("views/mc2_meaning.py", title="MC2 · What the posts mean", icon=":material/description:"),
    ],
    "RQ2 · What came before": [
        st.Page("views/baselines.py", title="Baselines & warning signs", icon=":material/monitoring:"),
        st.Page("views/mc1_language.py", title="MC1 · Stance & sentiment", icon=":material/psychology:"),
    ],
    "Conclusions": [
        st.Page("views/what_if.py", title="What-if simulator", icon=":material/science:"),
        st.Page("views/compare.py", title="Comparing the failures", icon=":material/compare_arrows:"),
    ],
}

nav = st.navigation(pages)

with st.sidebar:
    st.caption("ISTE-782 · VAST Challenge 2026")
    st.caption("Aarushi Sharma · Joshua Sheron Dhanapal · Siddharth Patondikar")

nav.run()
