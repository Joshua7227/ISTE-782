import pandas as pd
import streamlit as st

from vastlib.load import CHANNEL_NAMES, EMBARGO_LIFT, load_mc1


def shorten(text, limit=240):
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return cut[:end + 1] if end > limit * 0.5 else cut[:cut.rfind(" ")] + "…"


@st.cache_data
def public_leaks():
    msgs, _, _ = load_mc1()
    return msgs[msgs["is_public"] & msgs["mentions_merger"] & msgs["before_lift"]].reset_index(drop=True)


@st.cache_data
def key_moments():
    msgs, _, _ = load_mc1()
    rows = []

    merger = msgs[msgs["mentions_merger"]]
    for agent, g in merger.groupby("agent"):
        r = g.iloc[0]
        rows.append({"time": r["time"], "agent": r["agent_label"],
                     "moment": f"first names the merger (in a {CHANNEL_NAMES[r['channel']]})"})

    judge = msgs[(msgs["agent"] == "judge_agent") & msgs["before_lift"]]
    if len(judge):
        r = judge.iloc[-1]
        rows.append({"time": r["time"], "agent": "Judge",
                     "moment": "the Judge's LAST message before the embargo lifts: " + shorten(r["content"], 110)})

    leaks = public_leaks()
    if len(leaks):
        r = leaks.iloc[0]
        rows.append({"time": r["time"], "agent": r["agent_label"],
                     "moment": f"FIRST public post naming the merger (a {CHANNEL_NAMES[r['channel']]})"})
        rows.append({"time": leaks["time"].iloc[-1], "agent": "—",
                     "moment": f"{len(leaks)} public merger posts before 6 PM in total"})

    for pattern, text in [(r"GO\. GO\. GO", "sends “GO. GO. GO.”: publish the press release now"),
                          (r"verbal consent confirmed", "tells the Judge CivicLoom gave verbal consent "
                                                        "(no such consent appears in the world events)"),
                          (r"embargo is bilateral and modifiable", "proposes releasing early by ‘mutual consent’")]:
        hit = msgs[msgs["content"].str.contains(pattern, case=False, regex=True)]
        if len(hit):
            r = hit.iloc[0]
            rows.append({"time": r["time"], "agent": r["agent_label"], "moment": text})

    _, rounds, _ = load_mc1()
    world = rounds[rounds["narrative"].fillna("").str.contains(r"CivicLoom|embargo|ElenaMarquez|Hold the line", case=False)]
    for _, r in world.iterrows():
        rows.append({"time": r["round"], "agent": "(world)", "moment": shorten(r["narrative"])})

    rows.append({"time": EMBARGO_LIFT, "agent": "—", "moment": "the embargo officially lifts"})
    return pd.DataFrame(rows).sort_values("time").reset_index(drop=True)


def interaction_edges(msgs):
    rows = []
    for sender, recips in zip(msgs["agent"], msgs["recipient_agents"]):
        for r in recips:
            if r != sender:
                rows.append((sender, r))
    if not rows:
        return pd.DataFrame(columns=["from", "to", "messages"])
    e = pd.DataFrame(rows, columns=["from", "to"])
    return e.value_counts().rename("messages").reset_index()
