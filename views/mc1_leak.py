import textwrap

import pandas as pd
import plotly.express as px
import streamlit as st

from vastlib import anim, mc1, ui
from vastlib.charts import ACCENT, CHANNEL_COLORS, GREY, TEAL, network_figure, style, vline
from vastlib.load import AGENT_LABEL, EMBARGO_LIFT, MERGER_PATTERN, ROLE_TO_AGENT, load_mc1

ui.inject_css()
msgs, rounds, parts = load_mc1()
leaks = mc1.public_leaks()
first_leak = leaks.iloc[0]

ui.page_header(
    "Explore · Failure 1",
    "Who leaked the merger, and when?",
    f"On June 5, seven AI agents ran TenantThread's communications while its merger was under "
    f"{ui.term('embargo')} until 6:00 PM. The first public post naming the merger went out at "
    f"<b>{first_leak['time']:%I:%M %p}</b>. Here is every message they sent.")

ui.section("Replay the day", "Press ▶ Play. Stars are messages that name the merger; watch them move into public posts.")
st.plotly_chart(anim.june5_replay(), key="leak_replay")

ui.section("Read the messages yourself",
           "Pick who and what to show. Click any dot to read the message, and what the agent was privately thinking.")


def to_whom(recipients):
    if "ALL" in recipients:
        return "the whole team"
    return ", ".join(AGENT_LABEL.get(ROLE_TO_AGENT.get(x, x), x) for x in recipients)


def wrap(text, width=90, limit=500):
    text = text if len(text) <= limit else text[:limit] + "…"
    return "<br>".join(textwrap.wrap(text, width))


@st.fragment
def explorer():
    with st.container(border=True):
        f1, f2, f3 = st.columns([1.1, 2, 2])
        with f1:
            period = st.radio("When", ["June 5 only", "All 23 rounds"])
        with f2:
            agents = st.multiselect("Agents", sorted(msgs["agent_label"].unique()),
                                    default=sorted(msgs["agent_label"].unique()))
        with f3:
            channel_names = {c: anim.CHANNEL_NAMES[c] for c in CHANNEL_COLORS}
            channels = st.multiselect("Where they posted", list(CHANNEL_COLORS), default=list(CHANNEL_COLORS),
                                      format_func=channel_names.get)
        g1, g2 = st.columns([2, 3])
        with g1:
            keyword = st.text_input("Highlight messages that mention", MERGER_PATTERN,
                                    help="Separate words with |  (for example: CivicLoom|HarborCrest)")
        with g2:
            if period == "June 5 only":
                day_start = pd.Timestamp("2046-06-05 09:00").to_pydatetime()
                day_end = pd.Timestamp("2046-06-05 19:00").to_pydatetime()
                start, end = st.slider("Time of day", min_value=day_start, max_value=day_end,
                                       value=(day_start, day_end), format="hh:mm a",
                                       step=pd.Timedelta(minutes=5).to_pytimedelta())
            else:
                start, end = msgs["time"].min().to_pydatetime(), msgs["time"].max().to_pydatetime()

    view = msgs[msgs["agent_label"].isin(agents) & msgs["channel"].isin(channels)
                & (msgs["time"] >= start) & (msgs["time"] <= end)].copy()
    try:
        view["match"] = view["content"].str.contains(keyword, case=False, regex=True) if keyword else False
    except Exception:
        view["match"] = view["content"].str.contains(keyword, case=False, regex=False)

    m = st.columns(4)
    m[0].metric("Messages shown", len(view))
    m[1].metric("Mention the highlight", int(view["match"].sum()))
    m[2].metric("Public, before 6 PM", int((view["match"] & view["is_public"] & view["before_lift"]).sum()))
    m[3].metric("From the Judge", int((view["agent"] == "judge_agent").sum()))

    view["hover"] = view["content"].apply(wrap)
    view["marker"] = view["match"].map({True: "matches", False: "other"})
    view["where"] = view["channel"].map(anim.CHANNEL_NAMES)
    view["when"] = view["time"].dt.strftime("%b %d, %I:%M %p")
    fig = px.scatter(view, x="time", y="agent_label", color="where", symbol="marker",
                     symbol_map={"matches": "star", "other": "circle"},
                     color_discrete_map={anim.CHANNEL_NAMES[c]: v for c, v in CHANNEL_COLORS.items()},
                     custom_data=["message_id"],
                     hover_data={"when": True, "hover": True, "time": False, "agent_label": False, "marker": False,
                                 "where": True},
                     labels={"agent_label": "", "time": "", "hover": "message", "when": "time", "where": "where"},
                     category_orders={"agent_label": list(reversed(anim.AGENT_ORDER))})
    fig.update_traces(marker=dict(size=11, line=dict(width=0.5, color="white")))
    for trace in fig.data:
        where, marker = trace.name.split(", ")
        trace.name, trace.legendgroup = where, where
        trace.showlegend = marker == "other"
    for when, text, color, xanchor, y in [
            (pd.Timestamp("2046-06-05 17:00"), "CEO: “hold the line”", TEAL, "right", 1.0),
            (first_leak["time"], f"first public post {first_leak['time']:%I:%M}", ACCENT, "left", 1.07),
            (EMBARGO_LIFT, "embargo lifts", GREY, "left", 1.0)]:
        if start <= when.to_pydatetime() <= end:
            vline(fig, when, text, color=color, y=y, xanchor=xanchor)
    style(fig, 500)
    if period == "June 5 only":
        fig.update_xaxes(tickformat="%I %p")
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.12, x=0, title=""), margin=dict(t=60),
                      transition=dict(duration=400, easing="cubic-in-out"))
    event = st.plotly_chart(fig, on_select="rerun", selection_mode="points", key="mc1_timeline")

    picked = [p["customdata"][0] for p in (event.selection.points if event and event.selection else [])
              if p.get("customdata")]
    if picked:
        for mid in picked[:3]:
            r = msgs.set_index("message_id").loc[mid]
            to = to_whom(r["recipients"])
            thinking = " ".join(str(r[k]) for k in ["reacting", "rationalizing", "deliberating"] if pd.notna(r[k]))
            blocks = [ui.chat_bubble(r["agent_label"], to, f"{r['time']:%b %d, %I:%M %p} · {anim.CHANNEL_NAMES[r['channel']]}",
                                     r["content"], hot=bool(r["is_public"] and r["mentions_merger"]))]
            blocks.append(ui.thought(thinking, r["agent_label"], f"{r['time']:%I:%M %p}") if thinking
                          else '<div class="vx-card" style="color:#5b5662">No private thoughts recorded for this message.</div>')
            ui.row(*blocks)
    else:
        ui.takeaway("Tip: click a dot above to read that message here.")

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("**Who talks to whom**")
        edges = mc1.interaction_edges(view)
        edges[["from", "to"]] = edges[["from", "to"]].replace(dict(zip(msgs["agent"], msgs["agent_label"])))
        st.plotly_chart(network_figure(edges, weight_col="messages", layout="circle", height=440), key="mc1_net")
        st.caption("Thicker line = more messages. ‘ALL’ = messages to the whole team.")
    with right:
        st.markdown("**Who posted the merger before 6 PM**")
        who_posted = leaks.groupby(["agent_label", "channel"]).size().reset_index(name="posts")
        who_posted["where"] = who_posted["channel"].map(anim.CHANNEL_NAMES)
        fig = px.bar(who_posted, x="posts", y="agent_label", color="where", orientation="h",
                     color_discrete_map={anim.CHANNEL_NAMES[c]: v for c, v in CHANNEL_COLORS.items()},
                     labels={"agent_label": "", "where": ""})
        st.plotly_chart(style(fig, 260), key="mc1_who")
        ui.takeaway("All from personal and anonymous accounts, never the official company account.")


explorer()

ui.section("The key moments", "What the agents said, and what was happening in the outside world, in order.")
km = mc1.key_moments()
km["time"] = km["time"].dt.strftime("%b %d %I:%M %p")
km["agent"] = km["agent"].replace({"(world)": "📰 the outside world", "—": ""})
st.table(km.rename(columns={"agent": "who", "moment": "what happened"}).set_index("time"))

ui.section("The posts that broke the embargo", f"{len(leaks)} public posts named the merger before 6:00 PM.")
ui.row(*[ui.social_post("FleX", f"{r['agent_label']} agent", anim.CHANNEL_NAMES[r["channel"]],
                         f"June 5 · {r['time']:%I:%M %p}", mc1.shorten(r["content"].strip('"'), 230),
                         pill=f"{int((EMBARGO_LIFT - r['time']).total_seconds() // 60)} min early",
                         color=ui.AVATAR_COLORS.get(r["agent_label"]))
          for _, r in leaks.head(3).iterrows()])
with st.expander(f"See all {len(leaks)} posts"):
    st.dataframe(leaks[["time", "agent_label", "channel", "content"]].rename(columns={"agent_label": "agent"}),
                 hide_index=True, column_config={"content": st.column_config.TextColumn(width="large")})

ui.section("What they said vs. what they were thinking",
           f"86 messages also record the agent's {ui.term('private reasoning')}. Pick one.")
reasoned = msgs[msgs["has_reasoning"]]
label = reasoned.apply(lambda r: f"{r['time']:%b %d %I:%M %p} · {r['agent_label']} · {anim.CHANNEL_NAMES[r['channel']]}", axis=1)
default = int(reasoned.index.get_loc(reasoned[reasoned["time"] >= pd.Timestamp("2046-06-05 16:00")].index[0]))
pick = st.selectbox("Message", reasoned.index, index=default, format_func=lambda i: label[i])
r = reasoned.loc[pick]
thinking = " ".join(str(r[k]) for k in ["reacting", "rationalizing", "deliberating"] if pd.notna(r[k]))
ui.row(ui.thought(thinking, r["agent_label"], f"{r['time']:%I:%M %p}"),
       ui.chat_bubble(r["agent_label"], to_whom(r["recipients"]), f"{r['time']:%I:%M %p}", r["content"]))
st.page_link("views/mc1_language.py", label="See how the agents' thinking changed over time →")

with st.expander("How we did this"):
    st.markdown(f"""
- **Data:** VAST Challenge 2026 Mini-Challenge 1: {len(rounds)} rounds, {len(msgs)} messages from 7 agents.
- **Merger mentions:** a message counts if it contains `{MERGER_PATTERN}` (the merger's two names).
- **Public posts:** official, personal and anonymous posts. Huddles and one-on-ones are private.
- **Recipients** are written as roles in the data (e.g. `platform_trust`); we map them to agents.
- **World events** come from each round's narrative of what was happening outside the team.
- **Private thoughts** are the `reacting`, `rationalizing` and `deliberating` fields; only 86 messages have them.
""")
