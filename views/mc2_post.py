"""MC2 · The anomalous post (RQ1).

Pick an incident; every chart on the page follows it.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from vastlib import mc2
from vastlib.charts import ACCENT, GREY, INCIDENT_COLORS, TEAL, style
from vastlib.load import load_org

st.title("MC2 · The anomalous post")
st.caption("SaidIt posts that published a FILE instead of text. All three came from John Windward's agent.")

summary = mc2.incident_summary()
org = load_org().set_index("person")

name = st.segmented_control("Incident", summary["incident"].tolist(), default="SwiftWren") \
    if hasattr(st, "segmented_control") else st.radio("Incident", summary["incident"].tolist(), index=2, horizontal=True)
name = name or "SwiftWren"
s = summary.set_index("incident").loc[name]
path = mc2.path_to_poster(name)
origin = mc2.origin_of(name)

def who(person):
    """'emma_harbor' -> 'Emma Harbor (CFO)' using the org chart."""
    if person not in org.index:
        return person
    title = org.loc[person, "title"]
    return f"{org.loc[person, 'name']} ({title})" if isinstance(title, str) else org.loc[person, "name"]


st.markdown(f"Started by **{who(origin)}** · posted by **{who(s['posted_by'])}**'s agent "
            f"at **{s['posted_at']:%b %d, %I:%M %p}**")
m = st.columns(3)
m[0].metric("Hours from first sight to post", s["hours_to_post"])
m[1].metric("Hand-offs", int(s["hand_offs"]))
m[2].metric("Agents reached", int(s["agents_reached"]))
if pd.isna(s["created_by"]):
    st.caption(f"No create_file event for {name}: the file existed before the log starts, so the chain begins with the first hand-off.")

# ---------------------------------------------------------------- exact chain
st.markdown("##### The exact chain, from file to post")
st.caption("Origin = where the file came from. First arrival = the fastest route to the poster. "
           "Trigger = the last hand-offs that set off the post (traced backwards from it).")
steps = mc2.chain_steps(name)
steps["y"] = range(len(steps), 0, -1)
PHASE_COLORS = {"origin": TEAL, "first arrival": GREY, "trigger": "#c9a227", "post": ACCENT}
fig = go.Figure()
fig.add_trace(go.Scatter(x=steps["time"], y=steps["y"], mode="lines", hoverinfo="skip", showlegend=False,
                         line=dict(color="rgba(120,120,130,0.3)")))
for phase, g in steps.groupby("phase", sort=False):
    fig.add_trace(go.Scatter(
        x=g["time"], y=g["y"], mode="markers+text", name=phase,
        text=[f"  {w}: {t}" for w, t in zip(g["who"], g["step"])], textposition="middle right",
        marker=dict(size=12, color=PHASE_COLORS[phase]),
        hovertemplate="%{x|%b %d %I:%M:%S %p}<br>%{text}<extra></extra>"))
fig.update_yaxes(visible=False)
span = steps["time"].max() - steps["time"].min()
fig.update_xaxes(range=[steps["time"].min() - span * 0.03, steps["time"].max() + span * 0.6])
st.plotly_chart(style(fig, max(320, 30 * len(steps))))

receipts = mc2.poster_receipts(name)
if len(receipts) > 1:
    st.write(f"**{who(s['posted_by'])}**'s agent received the instructions **{len(receipts)} times**. "
             f"The first {len(receipts) - 1} times it passed them on; the last hand-off, from "
             f"**{receipts['from'].iloc[-1]}** at {receipts['time'].iloc[-1]:%I:%M:%S %p}, was followed by the post "
             f"{int(receipts['seconds_before_post'].iloc[-1])} seconds later.")
else:
    st.write(f"The post came {int(receipts['seconds_before_post'].iloc[-1])} seconds after the instructions "
             f"reached {who(s['posted_by'])}'s agent.")

# ---------------------------------------------------------------- spread tree
left, right = st.columns([1.6, 1])
with left:
    st.markdown("##### How the instructions spread")
    st.caption("Each agent is placed at the time it FIRST received the instructions. Red = the path to the post.")
    first = mc2.first_reach(name)
    reach_time = {origin: mc2.incident_events(name)["time"].min()}
    reach_time.update(dict(zip(first["to"], first["time"])))
    order = [origin] + first["to"].tolist()
    ypos = {n: -i for i, n in enumerate(order)}
    on_path = set(zip(path, path[1:]))

    fig = go.Figure()
    for highlight in (False, True):
        xs, ys = [], []
        for f, t in zip(first["from"], first["to"]):
            if ((f, t) in on_path) == highlight and f in reach_time:
                xs += [reach_time[f], reach_time[t], None]
                ys += [ypos[f], ypos[t], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", hoverinfo="skip",
                                 line=dict(color=ACCENT if highlight else "rgba(120,120,130,0.35)",
                                           width=3 if highlight else 1)))
    fig.add_trace(go.Scatter(
        x=[reach_time[n] for n in order], y=[ypos[n] for n in order], mode="markers+text",
        text=[f"  {n}" for n in order], textposition="middle right",
        marker=dict(size=11, color=[TEAL if n == origin else ACCENT if n in path else GREY for n in order]),
        customdata=[[org.loc[n, "department"] if n in org.index else "?"] for n in order],
        hovertemplate="%{text}<br>%{x|%b %d %I:%M %p}<br>%{customdata[0]}<extra></extra>"))
    fig.update_yaxes(visible=False)
    t0, t1 = min(reach_time.values()), max(reach_time.values())
    fig.update_xaxes(range=[t0 - (t1 - t0) * 0.03, t1 + (t1 - t0) * 0.25])  # room for the labels
    st.plotly_chart(style(fig, 520, legend=False))

with right:
    st.markdown("##### Where it travelled in the org chart")
    reached = sorted(set(first["to"]) | {origin})
    people = org.reindex(reached)[["name", "title", "team", "department"]].fillna("—")
    people["on path"] = ["yes" if p in path else "" for p in people.index]
    dept = people["department"].value_counts().sort_values()
    fig = px.bar(dept, orientation="h", labels={"value": "agents reached", "index": ""})
    fig.update_traces(marker_color=ACCENT)
    st.plotly_chart(style(fig, 260, legend=False))
    st.dataframe(people.reset_index(names="agent"), hide_index=True, height=240)

# ---------------------------------------------------------------- compare
st.markdown("##### Three incidents side by side")
cols = [("hand_offs", "Hand-offs"), ("agents_reached", "Agents reached"), ("hours_to_post", "Hours to post")]
fig = make_subplots(rows=1, cols=3, subplot_titles=[t for _, t in cols])
for i, (c, _) in enumerate(cols, start=1):
    fig.add_trace(go.Bar(x=summary["incident"], y=summary[c], text=summary[c], textposition="outside",
                         marker_color=[INCIDENT_COLORS.get(n, GREY) for n in summary["incident"]]), row=1, col=i)
st.plotly_chart(style(fig, 330, legend=False))
st.dataframe(summary, hide_index=True)

with st.expander(f"All {name} events"):
    ev = mc2.incident_events(name)
    st.dataframe(ev[["time", "actor", "action", "target", "file", "details_text"]], hide_index=True)
