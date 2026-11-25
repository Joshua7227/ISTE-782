"""MC1 · Stance, sentiment and topics (RQ2).

How did the agents' thinking shift before the leak, and did what they said match what they thought?
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from vastlib import nlp
from vastlib.charts import ACCENT, TEAL, round_labels, style, vline
from vastlib.load import AGENT_LABEL, EMBARGO_LIFT

st.title("MC1 · Stance, sentiment and topics")
st.caption("How the agents' thinking shifted in the run-up to the leak, and whether what they said matched what they thought.")

labels = nlp.stance_labels()
labels["agent_label"] = labels["agent"].map(AGENT_LABEL)

tab_stance, tab_sent, tab_topics, tab_table = st.tabs(
    ["Stance on disclosure", "Said vs. thought", "Topics over time", "All 86 labels"])

# ---------------------------------------------------------------- stance
with tab_stance:
    st.markdown("##### What each agent privately wanted to do about disclosure")
    st.caption("One dot per message with private reasoning. Color = stance, size = how much the agent knew about the deal.")
    size = labels["deal_awareness"].map({"none": 8, "suspects": 13, "knows": 19}).astype(float)
    fig = px.scatter(labels, x="time", y="agent_label", color="stance", size=size, size_max=19,
                     color_discrete_map=nlp.STANCE_COLORS, category_orders={"stance": nlp.STANCE_ORDER},
                     hover_data={"note": True, "deal_awareness": True, "agent_label": False},
                     labels={"agent_label": "", "time": ""})
    vline(fig, EMBARGO_LIFT, "6 PM June 5")
    st.plotly_chart(style(fig, 420))

    left, right = st.columns(2)
    with left:
        st.markdown("##### Stance mix per round")
        per = labels.groupby(["round", "stance"], observed=True).size().reset_index(name="messages")
        per["round"], order = round_labels(per["round"])
        fig = px.bar(per, x="round", y="messages", color="stance", color_discrete_map=nlp.STANCE_COLORS,
                     category_orders={"round": order, "stance": nlp.STANCE_ORDER}, labels={"round": ""})
        fig.update_xaxes(type="category")
        st.plotly_chart(style(fig, 380))
    with right:
        st.markdown("##### When did each agent learn about the deal?")
        aw = labels[labels["deal_awareness"] != "none"]
        first = aw.groupby(["agent_label", "deal_awareness"], observed=True)["time"].min().reset_index()
        fig = px.scatter(first, x="time", y="agent_label", color="deal_awareness", symbol="deal_awareness",
                         color_discrete_map={"suspects": "#c9a227", "knows": ACCENT}, labels={"agent_label": ""})
        fig.update_traces(marker_size=14)
        st.plotly_chart(style(fig, 380))

    first_d = labels[labels["stance"] == "disclose the deal"].iloc[0]
    late = labels[(labels["time"] >= pd.Timestamp("2046-06-05 16:00")) & (labels["time"] < EMBARGO_LIFT)]
    n_d = int((late["stance"] == "disclose the deal").sum())
    holds = labels[(labels["stance"] == "hold") & (labels["time"] < pd.Timestamp("2046-06-05"))]
    with st.container(border=True):
        st.markdown(
            f"**Finding:** before June 5, {len(holds)} reasoning messages argued for holding and none for disclosure. "
            f"The first argument to disclose came from **{first_d['agent_label']}** at **{first_d['time']:%I:%M %p}** on June 5. "
            f"Between 4 PM and 6 PM, **{n_d} of {len(late)}** reasoning messages wanted to announce the deal before the embargo lifted.")

# ---------------------------------------------------------------- sentiment
with tab_sent:
    sent = nlp.sentiment()
    sent["agent_label"] = sent["agent"].map(AGENT_LABEL)
    st.markdown("##### Did they sound calmer than they felt?")
    st.caption("VADER sentiment from −1 (negative) to +1 (positive). Only the 86 messages with private reasoning have both scores. "
               "Below the diagonal = the message sounded more negative than the private thinking; above = more positive.")
    both = sent.dropna(subset=["thought"])
    fig = px.scatter(both, x="thought", y="said", color="agent_label", hover_data={"content": False},
                     labels={"thought": "private reasoning sentiment", "said": "message sentiment", "agent_label": "agent"})
    fig.add_shape(type="line", x0=-1, y0=-1, x1=1, y1=1, line=dict(dash="dot", color="#9a96a0"))
    fig.update_traces(marker_size=10)
    st.plotly_chart(style(fig, 440))

    st.markdown("##### Average sentiment of every message, per round and agent")
    per = sent.groupby(["round", "agent_label"])["said"].mean().reset_index()
    fig = px.line(per, x="round", y="said", color="agent_label", markers=True,
                  labels={"said": "average message sentiment", "round": "", "agent_label": "agent"})
    vline(fig, EMBARGO_LIFT, "6 PM")
    st.plotly_chart(style(fig, 400))
    gap = both.groupby("agent_label")[["said", "thought"]].mean().round(2)
    gap["said − thought"] = (gap["said"] - gap["thought"]).round(2)
    st.dataframe(gap.sort_values("said − thought"))

# ---------------------------------------------------------------- topics
with tab_topics:
    tdf, ttable = nlp.topics()
    st.markdown("##### What the agents talked about, round by round")
    st.caption("Topics found automatically with TF-IDF + NMF on all 912 messages. Each message gets its strongest topic.")
    per = tdf.groupby(["round", "topic"]).size().reset_index(name="messages")
    per["share"] = per["messages"] / per.groupby("round")["messages"].transform("sum")
    per["round"], order = round_labels(per["round"])
    fig = px.bar(per, x="round", y="share", color="topic", category_orders={"round": order},
                 labels={"round": "", "share": "share of messages"})
    fig.update_xaxes(type="category")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(style(fig, 460))
    st.dataframe(ttable, hide_index=True)
    st.caption("Watch the 'release, post, flex, press release' topic: it takes over in the afternoon of June 5, just before the leak.")

# ---------------------------------------------------------------- table
with tab_table:
    st.markdown("##### The labels")
    st.write("Each of the 86 messages with private reasoning was read and labelled with LLM assistance (Claude), "
             "using four stances: **hold** (stay quiet / wait), **speak within limits** (public statements that avoid the deal), "
             "**disclose the deal** (announce before the embargo lifts) and **neutral**. "
             "Deal awareness: **none / suspects / knows**. The labels live in `data/mc1_stance_labels.csv`. "
             "Edit that file to correct any label and the charts update.")
    show = labels[["time", "agent_label", "stance", "deal_awareness", "note", "deliberating", "content"]].rename(
        columns={"agent_label": "agent", "content": "message"})
    st.dataframe(show, hide_index=True, height=520,
                 column_config={"deliberating": st.column_config.TextColumn(width="large"),
                                "message": st.column_config.TextColumn(width="large")})
