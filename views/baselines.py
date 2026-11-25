"""Baselines & warning signs (RQ2).

What does 'normal' look like for each agent, and what stood out before each failure?
"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from vastlib import mc2
from vastlib.charts import (ACCENT, CHANNEL_COLORS, GREY, TEAL, incident_lines, network_figure,
                            round_labels, style, vline)
from vastlib.load import EMBARGO_LIFT, load_mc1, load_mc2

st.title("Baselines & warning signs")

tab_all, tab_agent, tab_virus, tab_mc1 = st.tabs(
    ["MC2 · Company-wide", "MC2 · One agent", "MC2 · The virus loop", "MC1 · Warning signs"])

ev = load_mc2()
agents_ev = ev[ev["actor_kind"] == "agent"]
summary = mc2.incident_summary()

# ---------------------------------------------------------------- company-wide
with tab_all:
    st.markdown("##### Every agent's events per day")
    st.caption("Log color scale, so a normal day (a few dozen events) and a runaway day (thousands) both show. "
               "Agents are sorted by their busiest day.")
    hide_virus = st.toggle("Remove the virus loop", value=False, key="all_hide")
    data = agents_ev[~agents_ev["virus"]] if hide_virus else agents_ev
    daily = data.groupby(["actor", "date"]).size().unstack(fill_value=0)
    daily = daily.loc[daily.max(axis=1).sort_values(ascending=False).index]
    fig = px.imshow(np.log10(daily + 1), aspect="auto", color_continuous_scale=["#fbf9f5", "#d9a5a5", ACCENT, "#3a0d12"],
                    labels=dict(color="events"), zmin=0, zmax=4)
    fig.update_coloraxes(colorbar=dict(tickvals=[0, 1, 2, 3, 4], ticktext=["0", "10", "100", "1k", "10k"]))
    fig.update_traces(customdata=daily.values, hovertemplate="%{y}<br>%{x}<br>%{customdata} events<extra></extra>")
    incident_lines(fig, summary, as_date_string=True)  # dashed line on each day with an anomalous post
    st.plotly_chart(style(fig, 900, legend=False))
    st.caption("The dark block on May 10–12 is the virus loop: four agents doing thousands of events a day. "
               "Toggle it off to see everyone's normal rhythm.")

# ---------------------------------------------------------------- one agent
with tab_agent:
    names = sorted(agents_ev["actor"].unique())
    who = st.selectbox("Agent", names, index=names.index("john_windward"))
    hide = st.toggle("Remove the virus loop", value=True, key="one_hide")
    a = agents_ev[agents_ev["actor"] == who]
    a = a[~a["virus"]] if hide else a

    left, right = st.columns([1.4, 1])
    with left:
        st.markdown("##### Activity by date and hour")
        grid = a.groupby(["hour", "date"]).size().unstack(fill_value=0).reindex(range(24), fill_value=0)
        fig = px.imshow(grid, aspect="auto", color_continuous_scale=["#fbf9f5", GREY, "#1c1a20"],
                        labels=dict(x="date", y="hour of day", color="events"))
        posts = summary[summary["posted_by"] == who]
        if len(posts):
            fig.add_scatter(x=posts["posted_at"].dt.date.astype(str), y=posts["posted_at"].dt.hour,
                            mode="markers+text", text=posts["incident"], textposition="top center",
                            marker=dict(color=ACCENT, size=14, symbol="x"), showlegend=False)
        st.plotly_chart(style(fig, 460, legend=False))
        st.caption("Red × = an anomalous post by this agent. Is it at an hour the agent is normally active?")
    with right:
        st.markdown("##### What this agent usually does")
        mix = a["action"].value_counts(normalize=True).head(12).sort_values()
        fig = px.bar(mix, orientation="h", labels={"value": "share of events", "index": ""})
        fig.update_traces(marker_color=GREY)
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(style(fig, 460, legend=False))

    hours = a.groupby("hour").size()
    if len(posts):
        for _, p in posts.iterrows():
            share = hours.get(p["posted_at"].hour, 0) / max(hours.sum(), 1)
            st.write(f"**{p['incident']}** was posted at {p['posted_at']:%I:%M %p}. "
                     f"Only {share:.1%} of this agent's normal activity happens in that hour.")

# ---------------------------------------------------------------- virus loop
with tab_virus:
    vb = mc2.virus_by_agent()
    st.markdown("##### A self-repeating loop: 4 agents, 75k events, May 10–12")
    st.write("Each cycle: check in → read a file like `fence_irrigation.txt` → create a random-named "
             "4,096-word file → delete it → queue the same task again. Every event is tagged `virus: true`.")
    c = st.columns(4)
    c[0].metric("Virus events", f"{int(ev['virus'].sum()):,}")
    c[1].metric("Share of the whole log", f"{ev['virus'].mean():.0%}")
    c[2].metric("Agents running it", len(vb))
    c[3].metric("Hours it ran", f"{(vb['end'].max() - vb['start'].min()).total_seconds() / 3600:.0f}")

    left, right = st.columns([1.4, 1])
    with left:
        st.markdown("##### When each agent was looping")
        fig = px.timeline(vb, x_start="start", x_end="end", y="actor", text="events",
                          color_discrete_sequence=[ACCENT])
        fig.update_yaxes(autorange="reversed", title="")
        incident_lines(fig, summary)
        st.plotly_chart(style(fig, 320, legend=False))
    with right:
        st.markdown("##### Who passed it to whom")
        st.plotly_chart(network_figure(mc2.virus_spread(), origin=vb["actor"].iloc[0],
                                       highlight_nodes=vb["actor"], layout="circle", height=320))

    st.markdown("##### Are the loop agents also in the incident chains?")
    rows = []
    for inc in summary["incident"]:
        h = mc2.handoffs(inc)
        involved = set(h["from"]) | set(h["to"])
        on_path = set(mc2.path_to_poster(inc))
        for agent in vb["actor"]:
            rows.append({"incident": inc, "agent": agent,
                         "in the chain": "yes" if agent in involved else "",
                         "on the path to the post": "yes" if agent in on_path else ""})
    st.dataframe(pd.DataFrame(rows).pivot(index="agent", columns="incident", values="in the chain"),
                 )
    st.caption("All four loop agents also handled the incident instructions. The loop is a warning sign that was visible "
               "a week before the May 17 post.")

# ---------------------------------------------------------------- MC1
with tab_mc1:
    msgs, rounds, parts = load_mc1()
    st.markdown("##### Did the agents start talking about the merger long before the leak?")
    per = msgs.groupby(["round", "channel"])["mentions_merger"].sum().reset_index()
    per = per[per["mentions_merger"] > 0]
    per["round"], order = round_labels(per["round"])
    fig = px.bar(per, x="round", y="mentions_merger", color="channel", color_discrete_map=CHANNEL_COLORS,
                 category_orders={"round": order},
                 labels={"mentions_merger": "messages naming CivicLoom / HarborCrest", "round": ""})
    fig.update_xaxes(type="category")
    st.plotly_chart(style(fig, 360))
    st.caption("Private channels carried the merger name from May 29. Public channels only start on June 5.")

    left, right = st.columns(2)
    with left:
        st.markdown("##### Public posting per round")
        pub = msgs[msgs["is_public"]].groupby(["round", "agent_label"]).size().reset_index(name="posts")
        pub["round"], order = round_labels(pub["round"])
        fig = px.bar(pub, x="round", y="posts", color="agent_label", category_orders={"round": order},
                     labels={"agent_label": "agent", "round": ""})
        fig.update_xaxes(type="category")
        st.plotly_chart(style(fig, 360))
    with right:
        st.markdown("##### The Judge's activity")
        j = msgs[msgs["agent"] == "judge_agent"].copy()
        j["hover"] = j["content"].str.slice(0, 160)
        fig = px.scatter(j, x="time", y="message_type", hover_data=["hover"], color_discrete_sequence=[TEAL])
        fig.update_traces(marker_size=11)
        vline(fig, EMBARGO_LIFT, "6 PM")
        st.plotly_chart(style(fig, 360, legend=False))
        st.caption(f"The Judge sent {len(j)} messages in total. Its last one before the leak was at "
                   f"{j['time'].max():%I:%M %p} on June 5.")
