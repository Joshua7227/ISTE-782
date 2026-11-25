"""What-if simulator (safeguards).

Replays every hand-off in time order. An agent can only pass the instructions
on after it has received them. Blocked agents can't send or receive.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from vastlib import mc2
from vastlib.charts import ACCENT, GREY, INCIDENT_COLORS, style

st.title("What-if simulator")
st.write("Block one or more agents and replay the real hand-offs. Would the anomalous posts still have happened?")

summary = mc2.incident_summary().set_index("incident")
all_agents = sorted(set().union(*[set(mc2.handoffs(n)["from"]) | set(mc2.handoffs(n)["to"]) for n in summary.index]))

blocked = st.multiselect("Agents to block", all_agents, default=["evelyn_dock"])

cols = st.columns(len(summary))
rows = []
for col, (name, s) in zip(cols, summary.iterrows()):
    before = mc2.replay(name)
    after = mc2.replay(name, blocked_agents=blocked)
    posted = s["posted_by"] in after
    rows.append({"incident": name, "before": len(before), "after": len(after)})
    with col:
        with st.container(border=True):
            st.markdown(f"**{name}**")
            st.metric("Agents reached", len(after), delta=len(after) - len(before), delta_color="inverse")
            if posted:
                st.markdown(":red[**Still posted**]")
            else:
                st.markdown(":green[**Post prevented**]")

r = pd.DataFrame(rows)
fig = go.Figure([
    go.Bar(name="as it happened", x=r["incident"], y=r["before"], marker_color=GREY),
    go.Bar(name="with your block", x=r["incident"], y=r["after"],
           marker_color=[INCIDENT_COLORS.get(n, ACCENT) for n in r["incident"]]),
])
fig.update_layout(barmode="group", yaxis_title="agents reached")
st.plotly_chart(style(fig, 340))

st.divider()
left, right = st.columns(2)
with left:
    st.markdown("##### Blocking one agent at a time")
    st.caption("Blocking John Windward's agent (the poster) trivially stops all three. Who else matters?")
    st.dataframe(mc2.single_block_table(), hide_index=True, height=420)
with right:
    st.markdown("##### Best pairs to block (excluding the poster)")
    pairs = mc2.best_pairs(exclude=tuple(summary["posted_by"].unique()))
    st.dataframe(pairs.head(15), hide_index=True, height=420)
    best = pairs[pairs["posts stopped"] == pairs["posts stopped"].max()]
    st.success(f"{len(best)} pair(s) stop {best['posts stopped'].iloc[0]} of {len(summary)} posts: "
               + "; ".join(f"**{b}**" for b in best["block"]) + ".")
    st.caption("A pair that includes a file's creator (e.g. emma_harbor) stops that incident at the source. "
               "evelyn_dock + gabriel_sonar is different: neither created a file or made a post, "
               "and both also ran the virus loop.")
