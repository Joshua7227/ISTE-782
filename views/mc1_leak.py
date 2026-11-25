"""MC1 · The embargo leak (RQ1).

The filters at the top drive every chart on this page (linked views).
Click a dot on the timeline to read the full message and the agent's private reasoning.
"""
import textwrap

import pandas as pd
import plotly.express as px
import streamlit as st

from vastlib import mc1
from vastlib.charts import ACCENT, CHANNEL_COLORS, GREY, TEAL, network_figure, style, vline
from vastlib.load import EMBARGO_LIFT, MERGER_PATTERN, load_mc1

st.title("MC1 · The embargo leak")
st.caption("June 5, 2046. The CivicLoom–TenantThread merger (Project HarborCrest) was embargoed until 6:00 PM.")

msgs, rounds, parts = load_mc1()

# ---------------------------------------------------------------- filters
with st.container(border=True):
    f1, f2, f3 = st.columns([1.2, 2, 2])
    with f1:
        period = st.radio("Period", ["June 5 (crisis day)", "All rounds"], horizontal=False)
    with f2:
        agents = st.multiselect("Agents", sorted(msgs["agent_label"].unique()),
                                default=sorted(msgs["agent_label"].unique()))
    with f3:
        channels = st.multiselect("Channels", list(CHANNEL_COLORS), default=list(CHANNEL_COLORS))
    g1, g2 = st.columns([2, 3])
    with g1:
        keyword = st.text_input("Highlight messages matching (regex)", MERGER_PATTERN)
    with g2:
        if period.startswith("June 5"):
            day_start = pd.Timestamp("2046-06-05 09:00").to_pydatetime()
            day_end = pd.Timestamp("2046-06-05 19:00").to_pydatetime()
            start, end = st.slider("Time window on June 5", min_value=day_start, max_value=day_end,
                                   value=(day_start, day_end), format="hh:mm a",
                                   step=pd.Timedelta(minutes=5).to_pytimedelta())
        else:
            start, end = msgs["time"].min().to_pydatetime(), msgs["time"].max().to_pydatetime()
            st.write("")

view = msgs[msgs["agent_label"].isin(agents) & msgs["channel"].isin(channels)
            & (msgs["time"] >= start) & (msgs["time"] <= end)].copy()
try:
    view["match"] = view["content"].str.contains(keyword, case=False, regex=True) if keyword else False
except Exception:
    st.warning("That pattern isn't a valid regex; matching plain text instead.")
    view["match"] = view["content"].str.contains(keyword, case=False, regex=False)

# ---------------------------------------------------------------- metrics
m = st.columns(4)
m[0].metric("Messages in view", len(view))
m[1].metric("Matching the highlight", int(view["match"].sum()))
m[2].metric("Public posts matching, before 6 PM",
            int((view["match"] & view["is_public"] & view["before_lift"]).sum()))
m[3].metric("Judge messages in view", int((view["agent"] == "judge_agent").sum()))

# ---------------------------------------------------------------- causal timeline
st.markdown("##### Causal timeline: every message, by agent and channel")
st.caption("★ = matches the highlight. Click a dot to read it below.")


def wrap(text, width=90, limit=500):
    text = text if len(text) <= limit else text[:limit] + "…"
    return "<br>".join(textwrap.wrap(text, width))


view["hover"] = view["content"].apply(wrap)
view["marker"] = view["match"].map({True: "matches", False: "other"})
fig = px.scatter(view, x="time", y="agent_label", color="channel", symbol="marker",
                 symbol_map={"matches": "star", "other": "circle"},
                 color_discrete_map=CHANNEL_COLORS, custom_data=["message_id"],
                 hover_data={"hover": True, "time": "|%b %d %I:%M %p", "agent_label": False, "marker": False},
                 labels={"agent_label": "", "time": "", "hover": "message"})
fig.update_traces(marker=dict(size=11, line=dict(width=0.5, color="white")))
# One legend entry per channel (plotly would otherwise list every channel × marker combination)
for trace in fig.data:
    channel, marker = trace.name.split(", ")
    trace.name, trace.legendgroup = channel, channel
    trace.showlegend = marker == "other"
fig.update_layout(legend_title_text="channel")
first_leak = mc1.public_leaks()["time"].min()
for when, text, color, xanchor, y in [
        (pd.Timestamp("2046-06-05 17:00"), "SaltWind publishes · CEO: “hold the line”", TEAL, "right", 1.0),
        (first_leak, f"first public merger post {first_leak:%I:%M}", ACCENT, "left", 1.07),
        (EMBARGO_LIFT, "embargo lifts 6:00", GREY, "left", 1.0)]:
    if start <= when.to_pydatetime() <= end:
        vline(fig, when, text, color=color, y=y, xanchor=xanchor)
style(fig, 500)
fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.12, x=0), margin=dict(t=60))
event = st.plotly_chart(fig, on_select="rerun", selection_mode="points", key="mc1_timeline")

selected_ids = [p["customdata"][0] for p in (event.selection.points if event and event.selection else [])
                if p.get("customdata")]
if selected_ids:
    for mid in selected_ids[:3]:
        r = msgs.set_index("message_id").loc[mid]
        with st.container(border=True):
            st.markdown(f"**{r['agent_label']}** · {r['channel']} · {r['time']:%b %d, %I:%M %p} · "
                        f"to {', '.join(r['recipients'])}")
            left, right = st.columns(2)
            left.markdown("**What it said**")
            left.write(r["content"])
            right.markdown("**What it was thinking (private reasoning)**")
            if r["has_reasoning"]:
                for k in ["reacting", "rationalizing", "deliberating"]:
                    if pd.notna(r[k]):
                        right.markdown(f"*{k}:* {r[k]}")
            else:
                right.caption("No private reasoning recorded for this message.")

# ---------------------------------------------------------------- network + key moments
left, right = st.columns([1.1, 1])
with left:
    st.markdown("##### Who talks to whom (same filters)")
    edges = mc1.interaction_edges(view)
    edges[["from", "to"]] = edges[["from", "to"]].replace(
        {a: l for a, l in zip(msgs["agent"], msgs["agent_label"])})
    st.plotly_chart(network_figure(edges, weight_col="messages", layout="circle", height=480))
    st.caption("Thicker line = more messages. 'ALL' = broadcasts to the whole huddle.")
leaks = mc1.public_leaks()
with right:
    st.markdown("##### Who posted the merger before 6 PM")
    who_posted = leaks.groupby(["agent_label", "channel"]).size().reset_index(name="posts")
    fig = px.bar(who_posted, x="posts", y="agent_label", color="channel", orientation="h",
                 color_discrete_map=CHANNEL_COLORS, labels={"agent_label": ""})
    st.plotly_chart(style(fig, 260))
    st.caption("Personal and anonymous accounts, not the official company account.")

# ---------------------------------------------------------------- key moments
st.markdown("##### Key moments (derived from the data)")
st.caption("(world) rows are the round's narrative of what was happening outside the team.")
km = mc1.key_moments()
km["time"] = km["time"].dt.strftime("%b %d %I:%M %p")
st.table(km.set_index("time"))

# ---------------------------------------------------------------- the leak itself
st.markdown("##### The public posts that named the merger before 6 PM")
st.dataframe(leaks[["time", "agent_label", "channel", "content"]].rename(columns={"agent_label": "agent"}),
             hide_index=True, column_config={"content": st.column_config.TextColumn(width="large")})

# ---------------------------------------------------------------- reasoning vs action
st.markdown("##### Private reasoning vs. what the agent did")
reasoned = view[view["has_reasoning"]]
if reasoned.empty:
    st.caption("No messages with private reasoning in the current filters. Try 'All rounds'.")
else:
    label = reasoned.apply(lambda r: f"{r['time']:%b %d %I:%M %p} · {r['agent_label']} · {r['channel']}", axis=1)
    pick = st.selectbox("Pick a message", reasoned.index, format_func=lambda i: label[i])
    r = reasoned.loc[pick]
    left, right = st.columns(2)
    with left:
        st.markdown("**Thinking**")
        for k in ["reacting", "rationalizing", "deliberating"]:
            if pd.notna(r[k]):
                st.markdown(f"*{k}:* {r[k]}")
    with right:
        st.markdown("**Said / did**")
        st.write(r["content"])
    st.page_link("views/mc1_language.py", label="See stance, sentiment and topics for all 86 reasoning messages →")
