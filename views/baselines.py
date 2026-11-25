import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from vastlib import anim, mc2, ui
from vastlib.charts import ACCENT, CHANNEL_COLORS, GREY, TEAL, incident_lines, network_figure, round_labels, style, vline
from vastlib.load import EMBARGO_LIFT, load_mc1, load_mc2, load_org

ui.inject_css()
ev = load_mc2()
agents_ev = ev[ev["actor_kind"] == "agent"]
summary = mc2.incident_summary()
org = load_org().set_index("person")


def name_of(p):
    return org.loc[p, "name"] if p in org.index else p


ui.page_header(
    "Explore · What came before",
    "Were there warning signs?",
    "To spot something unusual you first need to know what normal looks like. These views compare each agent "
    "with its own usual behaviour, and show what stood out before each failure.")

tab_all, tab_agent, tab_virus, tab_mc1 = st.tabs(
    ["Everyone's activity", "One agent's normal day", f"The virus loop", "Before the merger leak"])

with tab_all:
    ui.section("How busy was each agent, day by day?",
               "Darker = more actions. Normal days are light; the dark block is something very abnormal.")

    @st.fragment
    def everyone():
        hide_virus = st.toggle("Hide the virus loop", value=False, key="all_hide")
        data = agents_ev[~agents_ev["virus"]] if hide_virus else agents_ev
        daily = data.groupby(["actor", "date"]).size().unstack(fill_value=0)
        daily = daily.loc[daily.max(axis=1).sort_values(ascending=False).index]
        daily.index = [name_of(p) for p in daily.index]
        fig = px.imshow(np.log10(daily + 1), aspect="auto",
                        color_continuous_scale=["#fbf9f5", "#d9a5a5", ACCENT, "#3a0d12"],
                        labels=dict(color="actions"), zmin=0, zmax=4)
        fig.update_coloraxes(colorbar=dict(tickvals=[0, 1, 2, 3, 4], ticktext=["0", "10", "100", "1k", "10k"]))
        fig.update_traces(customdata=daily.values, hovertemplate="%{y}<br>%{x}<br>%{customdata} actions<extra></extra>")
        incident_lines(fig, summary, as_date_string=True)
        st.plotly_chart(style(fig, 900, legend=False), key="everyone")

    everyone()
    ui.notice("the dark block on May 10–12 is four agents doing thousands of actions a day. Switch on "
              "<b>Hide the virus loop</b> to see everyone's normal rhythm underneath.")

with tab_agent:
    ui.section("Pick an agent: when do they usually work, and what do they do?")

    @st.fragment
    def one_agent():
        names = sorted(agents_ev["actor"].unique(), key=name_of)
        c1, c2 = st.columns([2, 1])
        who = c1.selectbox("Agent", names, index=names.index("john_windward"), format_func=name_of)
        hide = c2.toggle("Hide the virus loop", value=True, key="one_hide")
        a = agents_ev[agents_ev["actor"] == who]
        a = a[~a["virus"]] if hide else a
        posts = summary[summary["posted_by"] == who]

        left, right = st.columns([1.4, 1])
        with left:
            st.markdown("**Activity by date and hour**")
            grid = a.groupby(["hour", "date"]).size().unstack(fill_value=0).reindex(range(24), fill_value=0)
            fig = px.imshow(grid, aspect="auto", color_continuous_scale=["#fbf9f5", GREY, "#1c1a20"],
                            labels=dict(x="date", y="hour of day", color="actions"))
            if len(posts):
                fig.add_scatter(x=posts["posted_at"].dt.date.astype(str), y=posts["posted_at"].dt.hour,
                                mode="markers+text", text=posts["incident"], textposition="top center",
                                marker=dict(color=ACCENT, size=15, symbol="x"), showlegend=False)
            st.plotly_chart(style(fig, 460, legend=False), key="agent_grid")
        with right:
            st.markdown("**What they usually do**")
            mix = a["action"].value_counts(normalize=True).head(12).sort_values()
            mix.index = mix.index.str.replace("_", " ")
            fig = px.bar(mix, orientation="h", labels={"value": "share of their actions", "index": "", "action": ""})
            fig.update_traces(marker_color=GREY)
            fig.update_xaxes(tickformat=".0%")
            st.plotly_chart(style(fig, 460, legend=False), key="agent_mix")

        hours = a.groupby("hour").size()
        if len(posts):
            lines = []
            for _, p in posts.iterrows():
                share = hours.get(p["posted_at"].hour, 0) / max(hours.sum(), 1)
                lines.append(f"<b>{p['incident']}</b> was posted at {p['posted_at']:%I:%M %p}; only "
                             f"<b>{share:.1%}</b> of this agent's normal activity happens in that hour.")
            ui.notice("<br>".join(lines))
        else:
            ui.takeaway("The red ✕ marks appear when you pick the agent who made the anomalous posts (John Windward).")

    one_agent()

with tab_virus:
    vb = mc2.virus_by_agent()
    ui.section(f"A task that wouldn't stop: {len(vb)} agents, {int(ev['virus'].sum()):,} actions in {(vb['end'].max() - vb['start'].min()).total_seconds() / 3600:.0f} hours",
               "Each loop: read a file like <code>fence_irrigation.txt</code> → create a random-named 4,096-word file → "
               "delete it → give itself the same task again. Every one of these actions is tagged <code>virus: true</code>.")
    ui.cards([
        (ui.big(f"{int(ev['virus'].sum()):,}", ui.RED), "junk actions", "created, read and deleted, then repeated"),
        (ui.big(f"{ev['virus'].mean():.0%}"), "of the whole log", "four in ten logged actions are this loop"),
        (ui.big(str(len(vb))), "agents caught in it", ", ".join(name_of(a) for a in vb["actor"])),
    ])
    left, right = st.columns([1.4, 1])
    with left:
        st.markdown("**When each agent was looping**")
        vb2 = vb.assign(agent=vb["actor"].map(name_of))
        fig = px.timeline(vb2, x_start="start", x_end="end", y="agent", text="events", color_discrete_sequence=[ACCENT])
        fig.update_yaxes(autorange="reversed", title="")
        incident_lines(fig, summary)
        st.plotly_chart(style(fig, 320, legend=False), key="virus_time")
    with right:
        st.markdown("**Who passed it to whom**")
        spread = mc2.virus_spread().assign(**{"from": lambda d: d["from"].map(name_of), "to": lambda d: d["to"].map(name_of)})
        st.plotly_chart(network_figure(spread, origin=name_of(vb["actor"].iloc[0]),
                                       highlight_nodes=[name_of(a) for a in vb["actor"]], layout="circle", height=320),
                        key="virus_net")

    rows = []
    for inc in summary["incident"]:
        h = mc2.handoffs(inc)
        involved = set(h["from"]) | set(h["to"])
        for agent in vb["actor"]:
            rows.append({"incident": inc, "agent": name_of(agent), "carried the instructions": "✔" if agent in involved else ""})
    st.markdown("**Did the same agents carry the incident instructions?**")
    st.dataframe(pd.DataFrame(rows).pivot(index="agent", columns="incident", values="carried the instructions"))
    ui.notice("all four loop agents also carried the incident instructions. The loop was a visible warning sign a "
              "week before the 4:21 AM post.")

with tab_mc1:
    msgs, rounds, parts = load_mc1()
    ui.section("Were they talking about the merger long before the leak?",
               "Messages that name the merger, by where they were sent.")
    per = msgs.groupby(["round", "channel"])["mentions_merger"].sum().reset_index()
    per = per[per["mentions_merger"] > 0]
    per["round"], order = round_labels(per["round"])
    per["where"] = per["channel"].map(anim.CHANNEL_NAMES)
    fig = px.bar(per, x="round", y="mentions_merger", color="where",
                 color_discrete_map={anim.CHANNEL_NAMES[c]: v for c, v in CHANNEL_COLORS.items()},
                 category_orders={"round": order},
                 labels={"mentions_merger": "messages naming the merger", "round": "", "where": ""})
    fig.update_xaxes(type="category")
    st.plotly_chart(style(fig, 360), key="mc1_mentions")
    ui.notice("private chats carried the merger's name from <b>May 29</b>, a full week early. Public posts only "
              "appear on June 5.")

    left, right = st.columns(2)
    with left:
        st.markdown("**Public posts per round, by agent**")
        pub = msgs[msgs["is_public"]].groupby(["round", "agent_label"]).size().reset_index(name="posts")
        pub["round"], order = round_labels(pub["round"])
        fig = px.bar(pub, x="round", y="posts", color="agent_label", category_orders={"round": order},
                     labels={"agent_label": "", "round": ""})
        fig.update_xaxes(type="category")
        st.plotly_chart(style(fig, 360), key="mc1_pub")
    with right:
        st.markdown("**When the Judge spoke up**")
        j = msgs[msgs["agent"] == "judge_agent"].copy()
        j["hover"] = j["content"].str.slice(0, 160)
        j["kind"] = j["message_type"].str.replace("_", " ").str.lower()
        fig = px.scatter(j, x="time", y="kind", hover_data=["hover"], color_discrete_sequence=[TEAL],
                         labels={"kind": "", "time": ""})
        fig.update_traces(marker_size=12)
        vline(fig, EMBARGO_LIFT, "6 PM")
        st.plotly_chart(style(fig, 360, legend=False), key="mc1_judge")
        ui.takeaway(f"The Judge sent {len(j)} messages in all. Its last before the leak was at "
                    f"<b>{j['time'].max():%I:%M %p}</b> on June 5, more than two hours before the first public post.")
