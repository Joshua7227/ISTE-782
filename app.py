import streamlit as st

st.set_page_config(page_title="When AI Agents Go Wrong", page_icon="🔎", layout="wide")

pages = {
    "Start here": [
        st.Page("views/story.py", title="The story", icon=":material/auto_stories:", default=True),
    ],
    "Explore · What happened": [
        st.Page("views/mc1_leak.py", title="The merger leak", icon=":material/campaign:"),
        st.Page("views/mc2_post.py", title="The 4:21 AM post", icon=":material/forum:"),
        st.Page("views/mc2_meaning.py", title="What the posts mean", icon=":material/description:"),
    ],
    "Explore · What came before": [
        st.Page("views/baselines.py", title="Warning signs", icon=":material/monitoring:"),
        st.Page("views/mc1_language.py", title="What the agents were thinking", icon=":material/psychology:"),
    ],
    "Explore · How to stop it": [
        st.Page("views/what_if.py", title="What-if simulator", icon=":material/science:"),
        st.Page("views/compare.py", title="Both failures compared", icon=":material/compare_arrows:"),
    ],
    "About": [
        st.Page("views/data_overview.py", title="The data", icon=":material/table_chart:"),
    ],
}

nav = st.navigation(pages)

with st.sidebar:
    st.caption("ISTE-782 · VAST Challenge 2026")
    st.caption("Aarushi Sharma · Joshua Sheron Dhanapal · Siddharth Patondikar")

nav.run()
