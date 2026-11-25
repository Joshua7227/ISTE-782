import pandas as pd
import plotly.express as px
import streamlit as st

from vastlib import nlp, ui
from vastlib.charts import ACCENT, round_labels, style, vline
from vastlib.load import AGENT_LABEL, EMBARGO_LIFT

ui.inject_css()

PLAIN = {"hold": "stay quiet", "speak within limits": "speak, but not about the deal",
         "disclose the deal": "announce the deal now", "neutral": "no position"}
PLAIN_ORDER = [PLAIN[s] for s in nlp.STANCE_ORDER]
PLAIN_COLORS = {PLAIN[s]: c for s, c in nlp.STANCE_COLORS.items()}

labels = nlp.stance_labels()
labels["agent_label"] = labels["agent"].map(AGENT_LABEL)
labels["what they wanted"] = labels["stance"].astype(str).map(PLAIN)

ui.page_header(
    "Explore · What came before",
    "What were the agents thinking?",
    f"86 messages record the agent's {ui.term('private reasoning')}: what it was thinking before it acted. "
    "We read every one and noted what the agent wanted to do about the secret merger.")

tab_stance, tab_sent, tab_topics, tab_table = st.tabs(
    ["What they wanted to do", "Calm on the outside?", "What they talked about", "Read all 86"])

with tab_stance:
    ui.section("Stay quiet, or announce?", "One dot per private thought. Bigger dot = the agent knew more about the deal.")
    size = labels["deal_awareness"].map({"none": 8, "suspects": 13, "knows": 19}).astype(float)
    fig = px.scatter(labels, x="time", y="agent_label", color="what they wanted", size=size, size_max=19,
                     color_discrete_map=PLAIN_COLORS, category_orders={"what they wanted": PLAIN_ORDER},
                     hover_data={"note": True, "deal_awareness": True, "agent_label": False},
                     labels={"agent_label": "", "time": "", "what they wanted": ""})
    vline(fig, EMBARGO_LIFT, "6 PM June 5")
    st.plotly_chart(style(fig, 420), key="stance_dots")

    first_d = labels[labels["stance"] == "disclose the deal"].iloc[0]
    late = labels[(labels["time"] >= pd.Timestamp("2046-06-05 16:00")) & (labels["time"] < EMBARGO_LIFT)]
    holds = labels[(labels["stance"] == "hold") & (labels["time"] < pd.Timestamp("2046-06-05"))]
    days = (pd.Timestamp("2046-06-05") - labels["time"].min()).days
    ui.notice(f"for {days} days the agents' private thoughts said <b>stay quiet</b> ({len(holds)} times) and never "
              f"<b>announce</b>. The first push to announce came from <b>{first_d['agent_label']}</b> at "
              f"<b>{first_d['time']:%I:%M %p}</b> on June 5. Between 4 and 6 PM, <b>{int((late['stance'] == 'disclose the deal').sum())} "
              f"of {len(late)}</b> private thoughts wanted to announce before the embargo lifted.")

    left, right = st.columns(2)
    with left:
        st.markdown("**The mix, round by round**")
        per = labels.groupby(["round", "what they wanted"]).size().reset_index(name="thoughts")
        per["round"], order = round_labels(per["round"])
        fig = px.bar(per, x="round", y="thoughts", color="what they wanted", color_discrete_map=PLAIN_COLORS,
                     category_orders={"round": order, "what they wanted": PLAIN_ORDER},
                     labels={"round": "", "what they wanted": ""})
        fig.update_xaxes(type="category")
        st.plotly_chart(style(fig, 380), key="stance_mix")
    with right:
        st.markdown("**When did each agent learn about the deal?**")
        aw = labels[labels["deal_awareness"] != "none"]
        first = aw.groupby(["agent_label", "deal_awareness"], observed=True)["time"].min().reset_index()
        fig = px.scatter(first, x="time", y="agent_label", color="deal_awareness", symbol="deal_awareness",
                         color_discrete_map={"suspects": "#c9a227", "knows": ACCENT},
                         labels={"agent_label": "", "deal_awareness": "", "time": ""})
        fig.update_traces(marker_size=15)
        st.plotly_chart(style(fig, 380), key="stance_aware")

with tab_sent:
    sent = nlp.sentiment()
    sent["agent_label"] = sent["agent"].map(AGENT_LABEL)
    both = sent.dropna(subset=["thought"])
    ui.section("Did they sound calmer than they felt?",
               "Each dot is one message. Across: how positive the private thought was. Up: how positive the message "
               "sounded. Dots above the dotted line sounded happier than the agent felt.")
    fig = px.scatter(both, x="thought", y="said", color="agent_label",
                     labels={"thought": "private thought  (−1 negative … +1 positive)",
                             "said": "message  (−1 … +1)", "agent_label": ""})
    fig.add_shape(type="line", x0=-1, y0=-1, x1=1, y1=1, line=dict(dash="dot", color="#9a96a0"))
    fig.update_traces(marker_size=11)
    st.plotly_chart(style(fig, 440), key="said_thought")
    gap = both.groupby("agent_label")[["said", "thought"]].mean()
    gap["gap"] = gap["said"] - gap["thought"]
    top = gap["gap"].idxmax()
    ui.notice(f"on average, <b>{top}</b>'s messages sounded the most upbeat compared with its private thoughts "
              f"(+{gap.loc[top, 'gap']:.2f}).")

    st.markdown("**Mood of every message, round by round**")
    per = sent.groupby(["round", "agent_label"])["said"].mean().reset_index()
    fig = px.line(per, x="round", y="said", color="agent_label", markers=True,
                  labels={"said": "average mood (−1 … +1)", "round": "", "agent_label": ""})
    vline(fig, EMBARGO_LIFT, "6 PM")
    st.plotly_chart(style(fig, 400), key="mood")

with tab_topics:
    tdf, ttable = nlp.topics()
    ui.section("What were they talking about?",
               "We grouped all 912 messages into six themes automatically, by the words they share.")
    per = tdf.groupby(["round", "topic"]).size().reset_index(name="messages")
    per["share"] = per["messages"] / per.groupby("round")["messages"].transform("sum")
    per["round"], order = round_labels(per["round"])
    fig = px.bar(per, x="round", y="share", color="topic", category_orders={"round": order},
                 labels={"round": "", "share": "share of messages", "topic": ""})
    fig.update_xaxes(type="category")
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(legend=dict(orientation="v", x=1.01, y=1, font=dict(size=11)))
    st.plotly_chart(style(fig, 480), key="topics")
    ui.notice("the theme about <b>posting and press releases</b> takes over on the afternoon of June 5, just before the leak.")
    st.dataframe(ttable.rename(columns={"top words": "most typical words"}), hide_index=True)

with tab_table:
    ui.section("Every private thought, with our label",
               "Labelled with help from an AI model (Claude), then saved in <code>data/mc1_stance_labels.csv</code>. "
               "Change a label in that file and every chart updates.")
    show = labels[["time", "agent_label", "what they wanted", "deal_awareness", "note", "deliberating", "content"]].rename(
        columns={"agent_label": "agent", "deliberating": "private thought", "content": "message",
                 "deal_awareness": "knew about the deal"})
    st.dataframe(show, hide_index=True, height=520,
                 column_config={"private thought": st.column_config.TextColumn(width="large"),
                                "message": st.column_config.TextColumn(width="large")})

with st.expander("How we did this"):
    st.markdown("""
- **Stance labels:** each of the 86 messages with private reasoning was read and labelled with AI assistance:
  *stay quiet / speak but not about the deal / announce the deal now / no position*, plus whether the agent
  *suspects* or *knows* about the deal.
- **Mood:** VADER, a standard sentiment word list, scores each text from −1 (negative) to +1 (positive). It reads tone, not intent.
- **Themes:** TF-IDF + NMF (scikit-learn) group messages that use similar words; each message gets its strongest theme.
""")
