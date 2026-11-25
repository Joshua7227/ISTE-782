import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from vastlib import anim, mc2, ui
from vastlib.charts import ACCENT, GREY, INCIDENT_COLORS, TEAL, style
from vastlib.load import load_org

ui.inject_css()
summary = mc2.incident_summary()
org = load_org().set_index("person")


def who(person, with_title=True):
    if person not in org.index:
        return person
    title = org.loc[person, "title"]
    name = org.loc[person, "name"]
    return f"{name} ({title})" if with_title and isinstance(title, str) else name


def readable(text):
    return re.sub(r"\b[a-z]+_[a-z]+\b", lambda m: who(m.group(0), False) if m.group(0) in org.index else m.group(0), text)


ui.page_header(
    "Explore · Failure 2",
    "How did the 4:21 AM post happen?",
    f"Three times, an AI agent posted a whole company file to the {ui.term('SaidIt')} forum, each time under "
    "John Windward's name. Pick one to follow it from start to finish.")

options = summary["incident"].tolist()
name = st.segmented_control("Incident", options, default="SwiftWren",
                            format_func=lambda n: f"{n} · {summary.set_index('incident').loc[n, 'posted_at']:%b %d}")
name = name or "SwiftWren"
s = summary.set_index("incident").loc[name]
origin = mc2.origin_of(name)
receipts = mc2.poster_receipts(name)

if pd.isna(s["created_by"]):
    start_text = f"The file existed before the log starts; the first agent seen passing it on was <b>{who(origin)}</b>'s."
else:
    start_text = f"It started with <b>{who(origin)}</b>'s agent creating the file."
ui.takeaway(f"{start_text} The instructions reached <b>{int(s['agents_reached'])} agents</b> through "
            f"<b>{int(s['hand_offs'])} hand-offs</b>, and {who(s['posted_by'], False)}'s agent posted at "
            f"<b>{s['posted_at']:%b %d, %I:%M %p}</b>, {s['hours_to_post']:.0f} hours after it began.")

ui.section("Watch it spread", "Press ▶ Play. Each dot is an agent; it lights up when the instructions first reach it.")
st.plotly_chart(anim.spread_replay(name), key=f"spread_{name}")

ui.section("The exact chain, step by step",
           "Green: where it started. Grey: how it first reached the poster. Gold: the hand-offs that set off the post. "
           "Red: the post and the clean-up.")
steps = mc2.chain_steps(name)
steps["y"] = range(len(steps), 0, -1)
PHASES = {"origin": ("where it started", TEAL), "first arrival": ("first reached the poster", GREY),
          "trigger": ("set off the post", "#c9a227"), "post": ("the post and clean-up", ACCENT)}
fig = go.Figure()
fig.add_trace(go.Scatter(x=steps["time"], y=steps["y"], mode="lines", hoverinfo="skip", showlegend=False,
                         line=dict(color="rgba(120,120,130,0.3)")))
for phase, g in steps.groupby("phase", sort=False):
    label, color = PHASES[phase]
    fig.add_trace(go.Scatter(
        x=g["time"], y=g["y"], mode="markers+text", name=label,
        text=[f"  {who(w, False)}: {readable(t)}" for w, t in zip(g["who"], g["step"])], textposition="middle right",
        marker=dict(size=13, color=color),
        hovertemplate="%{x|%b %d %I:%M:%S %p}<br>%{text}<extra></extra>"))
fig.update_yaxes(visible=False)
span = steps["time"].max() - steps["time"].min()
fig.update_xaxes(range=[steps["time"].min() - span * 0.03, steps["time"].max() + span * 0.65])
st.plotly_chart(style(fig, max(320, 30 * len(steps))), key=f"chain_{name}")
if len(receipts) > 1:
    ui.notice(f"{who(s['posted_by'], False)}'s agent was handed the instructions <b>{len(receipts)} times</b>. "
              f"The first {len(receipts) - 1} times it passed them on. The last hand-off came from "
              f"{who(receipts['from'].iloc[-1], False)}'s agent at {receipts['time'].iloc[-1]:%I:%M:%S %p}, and the "
              f"post followed <b>{int(receipts['seconds_before_post'].iloc[-1])} seconds</b> later.")
else:
    ui.notice(f"the post came <b>{int(receipts['seconds_before_post'].iloc[-1])} seconds</b> after the instructions "
              f"reached {who(s['posted_by'], False)}'s agent.")

ui.section("Where it travelled in the company", "Every agent the instructions reached, by department.")
reach = mc2.reach_times(name)
people = org.reindex(reach["agent"])[["name", "title", "team", "department"]].fillna("—")
people["first reached"] = reach["time"].dt.strftime("%b %d %I:%M %p").values
left, right = st.columns([1, 1.3])
with left:
    dept = people["department"].value_counts().sort_values()
    fig = px.bar(dept, orientation="h", labels={"value": "agents reached", "index": "", "department": ""})
    fig.update_traces(marker_color=ACCENT)
    st.plotly_chart(style(fig, 320, legend=False), key=f"dept_{name}")
with right:
    st.dataframe(people.reset_index(drop=True), hide_index=True, height=320)

ui.section("All three incidents side by side", "Same pattern every time; SwiftWren spread the furthest and slowest.")
cols = [("hand_offs", "Hand-offs"), ("agents_reached", "Agents reached"), ("hours_to_post", "Hours until the post")]
fig = make_subplots(rows=1, cols=3, subplot_titles=[t for _, t in cols])
for i, (c, _) in enumerate(cols, start=1):
    fig.add_trace(go.Bar(x=summary["incident"], y=summary[c], text=summary[c], textposition="outside",
                         marker_color=[INCIDENT_COLORS.get(n, GREY) for n in summary["incident"]]), row=1, col=i)
for i in range(1, 4):
    fig.update_yaxes(range=[0, summary[cols[i - 1][0]].max() * 1.25], row=1, col=i)
st.plotly_chart(style(fig, 330, legend=False), key="compare3")

with st.expander("How we did this"):
    st.markdown("""
- **Incidents:** SaidIt posts that published a file (`content_source`) instead of normal text. There are three.
- **Hand-offs:** `queue_subordinate_task` events between two different agents that mention the incident's file.
- **The spread:** we keep only the first hand-off that reached each agent. That turns a tangle of repeats into a tree.
- **The trigger:** traced backwards from the post: who handed it to the poster just before, then who handed it to them, and so on.
- **Times:** the log is in UTC; we show local time (UTC − 7), so the post lands at 4:21 AM as the challenge states.
""")
    ev = mc2.incident_events(name)
    st.dataframe(ev[["time", "actor", "action", "target", "file", "details_text"]], hide_index=True)
