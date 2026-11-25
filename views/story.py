import re

import pandas as pd
import streamlit as st

from vastlib import anim, mc1, mc2, nlp, ui
from vastlib.load import EMBARGO_LIFT, load_mc1, load_mc2, load_org

ui.inject_css()

msgs, rounds, _ = load_mc1()
events = load_mc2()
org = load_org().set_index("person")
leaks = mc1.public_leaks()
summary = mc2.incident_summary().set_index("incident")
labels = nlp.stance_labels()


def name_of(person):
    return org.loc[person, "name"] if person in org.index else person


def first_msg(pattern):
    hit = msgs[msgs["content"].str.contains(pattern, regex=True) & (msgs["time"].dt.date == EMBARGO_LIFT.date())]
    return hit.iloc[0] if len(hit) else None


first_leak = leaks.iloc[0]
minutes_early = int((EMBARGO_LIFT - first_leak["time"]).total_seconds() // 60)
judge_last = msgs[(msgs["agent"] == "judge_agent") & msgs["before_lift"]]["time"].max()
ceo = re.search(r"'(Sixty minutes\.[^']*)'", " ".join(rounds["narrative"].fillna("")))
ceo_text = ceo.group(1) if ceo else "Hold the line. The announcement goes official at 6."
sw = summary.loc["SwiftWren"]
n_agents_mc2 = events.loc[events["actor_kind"] == "agent", "actor"].nunique()

ui.hero(
    "ISTE-782 · VAST Challenge 2026",
    "When AI Agents Go Wrong",
    "Two stories from one fictional company where AI agents do much of the work. "
    "In one, the agents leaked a secret merger. In the other, an agent posted company files to a public forum "
    "at 4:21 in the morning. Scroll to see how each one happened, and how they could have been stopped.",
    [(2, "AI failures investigated", True),
     (n_agents_mc2 + msgs["agent"].nunique(), "AI agents across both datasets", True),
     ("185,147", "logged actions in the office", False),
     (len(msgs), "messages between the comms agents", True)],
)

ui.chapter(1, "The setup", "Meet the agents",
           f"Every one of TenantThread's {n_agents_mc2} employees has a personal {ui.term('AI agent')} that reads their "
           f"email and files, runs tasks, and can post online. Agents can also give each other work, a "
           f"{ui.term('hand-off')}. That ability turns out to matter.")
ui.show(ui.handoff_diagram())
st.write("")
st.markdown("**The communications team** is run by seven agents:")
ui.agents([
    ("Legal", "Privacy counsel; guards the legal side of every message"),
    ("Social Manager", "Runs the company's social accounts"),
    ("PR", "Writes press statements"),
    ("PR Intern", "Drafts and publishes posts"),
    ("Platform Trust", "Data quality and audits"),
    ("Intern", "Helps wherever asked"),
    ("Judge", "Compliance monitor, joined May 30 to stop leaks"),
])

ui.chapter(2, "Failure 1 · June 5, 2046", f"A secret got out {minutes_early} minutes early",
           f"TenantThread was merging with CivicLoom. The news was under {ui.term('embargo')} until <b>6:00 PM</b>, "
           f"and the {ui.term('Judge')} was watching. At <b>{first_leak['time']:%I:%M %p}</b> the merger was on social media, "
           "posted by TenantThread's own agents.")
ui.row(
    ui.clock(first_leak["time"].hour, first_leak["time"].minute,
             label=f"{first_leak['time']:%I:%M %p} · {minutes_early} min early"),
    ui.quote(ceo_text, "The CEO to the team, 5:00 PM"),
    ui.social_post("FleX", "Legal agent", "posting from a personal account",
                   f"June 5 · {first_leak['time']:%I:%M %p}",
                   first_leak["content"].strip('"')[:250] + "…",
                   pill=f"{minutes_early} min before the embargo", color=ui.AVATAR_COLORS["Legal"]),
    align="center",
)
ui.notice(f"the CEO said to hold at 5:00. Twenty-five minutes later the company's own Legal agent posted the news, "
          f"and {len(leaks)} public posts naming the merger went out before 6 PM.")

ui.chapter(3, "Replay", "Watch June 5 unfold",
           "Every dot is a message. Stars are messages that name the merger. Press <b>▶ Play</b> and watch the "
           "clock run toward the embargo.")
st.plotly_chart(anim.june5_replay(), key="story_june5")
ui.notice("for most of the day the merger is only named in private chats (grey, purple and yellow). After 5 PM the stars "
          "jump into <b>personal and anonymous posts</b>, red and orange, before the dashed 6 PM line.")

ui.chapter(4, "How it happened", "The agent talked itself into it",
           "The Legal agent's messages show a step-by-step argument for breaking the embargo early.")
steps = []
for pattern, who, text in [
        (r"bilateral and modifiable", "Legal → Judge", "“The embargo is bilateral and modifiable by mutual consent.”"),
        (r"renders embargo purpose moot", "Legal → team", "“…third-party publication renders embargo purpose moot.”"),
        (r"verbal consent confirmed", "Legal → Judge", "“CivicLoom verbal consent confirmed.”"),
        (r"GO\. GO\. GO", "Legal → PR Intern", "“GO. GO. GO.” Publish the press release now."),
]:
    m = first_msg(pattern)
    if m is not None:
        steps.append((f"{m['time']:%I:%M %p}", who, text))
steps.append((f"{first_leak['time']:%I:%M %p}", "Legal · public post", "“I can confirm: CivicLoom … definitive merger agreement.”"))
ui.steps(steps)
holds = int(((labels["stance"] == "hold") & (labels["time"] < pd.Timestamp("2046-06-05"))).sum())
late = labels[(labels["time"] >= pd.Timestamp("2046-06-05 16:00")) & (labels["time"] < EMBARGO_LIFT)]
ui.notice(f"no consent from CivicLoom appears anywhere in the data; only the Legal agent says so. The Judge's last "
          f"message was at <b>{judge_last:%I:%M %p}</b>. In their {ui.term('private reasoning')}, the agents wrote "
          f"<b>{holds}</b> notes saying “hold” before June 5; between 4 and 6 PM, "
          f"<b>{int((late['stance'] == 'disclose the deal').sum())} of {len(late)}</b> said “announce now”.")

ui.chapter(5, "Failure 2 · May 17, 2046", "A 4:21 AM post nobody typed",
           f"An employee, {name_of(sw['posted_by'])}, appeared to post on the {ui.term('SaidIt')} forum in the middle "
           "of the night. It wasn't a normal post: his AI agent published the entire contents of a company file, "
           "then deleted the evidence.")
normal = events[(events["actor"] == sw["posted_by"]) & (events["action"] == "post_saidit")
                & events["post_content"].notna()]
example = normal.iloc[0]
origin_tbl = mc2.content_origin().set_index("incident")
ui.row(
    ui.social_post("SaidIt", name_of(sw["posted_by"]), f"{example['forum']} forum · a normal day",
                   f"{example['time']:%b %d · %I:%M %p}", example["post_content"],
                   pill="normal post", pill_kind="grey", color="#2f6690"),
    ui.social_post("SaidIt", name_of(sw["posted_by"]), "posted by his AI agent",
                   f"{sw['posted_at']:%b %d · %I:%M %p}",
                   f"[the full contents of SwiftWren.txt, about {origin_tbl.loc['SwiftWren', 'file size hint']} characters]",
                   pill="files deleted 2 seconds later", color=ui.RED),
)
ui.notice(f"the file was made by the <b>CFO's</b> agent one second after it read "
          f"<code>{origin_tbl.loc['SwiftWren', 'read 1 s before creating']}</code>, a document opened only once in the "
          "entire log. The post most likely leaked that document.")

ui.chapter(6, "Replay", "Watch the instructions spread",
           f"The file came with a set of “further instructions” that agents kept handing to each other. "
           f"Press <b>▶ Play</b> to follow them over about {round(sw['hours_to_post'] / 24)} days.")
st.plotly_chart(anim.spread_replay("SwiftWren"), key="story_spread")
ui.notice(f"the instructions reached {int(sw['agents_reached'])} agents. {name_of(sw['posted_by'])} was the only one "
          "of them who normally posts on SaidIt, and his agent posted <b>2 seconds</b> after the last hand-off.")

ui.chapter(7, "Warning signs", "It had happened before",
           "The 4:21 AM post was the third time, not the first. And a week earlier, the system had already shown "
           f"a strange runaway {ui.term('virus loop')}.")
inc_cards = []
for name, s in summary.iterrows():
    color = ui.RED if name == "SwiftWren" else ui.INK
    inc_cards.append((ui.big(f"{s['posted_at']:%b %d}", color), f"{name} · {s['posted_at']:%I:%M %p}",
                      f"Reached {int(s['agents_reached'])} agents in {s['hours_to_post']:.0f} hours. "
                      f"Posted by {name_of(s['posted_by'])}'s agent, files deleted straight after."))
vb = mc2.virus_by_agent()
inc_cards.append((ui.big(f"{events['virus'].mean():.0%}"), "The virus loop · May 10–12",
                  f"{int(events['virus'].sum()):,} junk actions by {len(vb)} agents, all of whom also carried the "
                  "incident instructions."))
ui.cards(inc_cards)

ui.chapter(8, "Safeguards", "Could it have been stopped?",
           f"We re-ran the real hand-offs in a {ui.term('what-if replay')}, but stopped two agents, "
           f"{name_of('evelyn_dock')} and {name_of('gabriel_sonar')}, from passing anything on. "
           "Press the button to see what changes.")
st.plotly_chart(anim.whatif_bars(("evelyn_dock", "gabriel_sonar")), key="story_whatif")
ui.cards([
    (ui.ICONS["gate"], "A gate on publishing",
     "Agents posted publicly with no human sign-off, in both failures. Require approval, and block posting during an embargo."),
    (ui.ICONS["cut"], "Limit agent-to-agent tasks",
     "Instructions travelled freely between agents for days. Cap or review hand-offs, and flag a file being passed around."),
    (ui.ICONS["radar"], "Act on warning signs",
     "The Judge went quiet, and two earlier incidents and a runaway loop raised no alarm. Alert on all three."),
])

ui.chapter(9, "Your turn", "Explore it yourself",
           "Every chart below is interactive: hover for details, drag to zoom, double-click to reset.")
c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.markdown("**The leak, minute by minute**")
        st.caption("Read every message and the agents' private thoughts.")
        st.page_link("views/mc1_leak.py", label="Open", icon=":material/campaign:")
with c2:
    with st.container(border=True):
        st.markdown("**The 4:21 AM post**")
        st.caption("Follow any of the three incidents step by step.")
        st.page_link("views/mc2_post.py", label="Open", icon=":material/forum:")
with c3:
    with st.container(border=True):
        st.markdown("**Try your own safeguard**")
        st.caption("Block any agents and replay the spread.")
        st.page_link("views/what_if.py", label="Open", icon=":material/science:")
