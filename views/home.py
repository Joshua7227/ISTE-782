"""Home page: the two failures, the research questions, what we found so far."""
import streamlit as st

from vastlib import mc1, mc2
from vastlib.load import EMBARGO_LIFT, load_mc1, load_mc2

st.title("When AI Agents Go Wrong")
st.markdown("##### Investigating two multi-agent failures at TenantThread with visual analytics — VAST Challenge 2026")

msgs, rounds, _ = load_mc1()
events = load_mc2()
leaks = mc1.public_leaks()
summary = mc2.incident_summary()

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.markdown("#### MC1 · The embargo leak")
        st.caption("June 5, 2046 · merger embargoed until 6:00 PM")
        st.write(
            "TenantThread's merger with CivicLoom (codename *Project HarborCrest*) was under embargo, "
            "and a compliance agent called the Judge was meant to stop leaks. Yet the deal appeared on "
            "social media before 6 PM, posted by TenantThread's own AI agents."
        )
        a, b, c = st.columns(3)
        a.metric("Messages", f"{len(msgs):,}")
        b.metric("AI agents", msgs["agent"].nunique())
        c.metric("Early merger posts", len(leaks), help="Public posts naming the merger before the 6 PM embargo lift")
        st.page_link("views/mc1_leak.py", label="Explore the leak →")

with right:
    with st.container(border=True):
        st.markdown("#### MC2 · The anomalous post")
        st.caption("May 17, 2046 · 4:21 AM")
        st.write(
            "A post under employee John Windward's name appeared on the SaidIt forum in the middle of the "
            "night. It published the contents of a file, SwiftWren.txt, and the files were deleted one second later."
        )
        a, b, c = st.columns(3)
        a.metric("Events", f"{len(events):,}")
        b.metric("AI agents", events.loc[events["actor_kind"] == "agent", "actor"].nunique(),
                 help="Every one of the 49 employees has a personal AI agent")
        c.metric("Similar incidents", len(summary))
        st.page_link("views/mc2_post.py", label="Explore the post →")

st.divider()

q1, q2 = st.columns(2)
with q1:
    st.markdown("#### RQ1 · What happened?")
    st.write("What chains of decisions and system interactions led to the embargo leak and the anomalous post?")
with q2:
    st.markdown("#### RQ2 · What came before?")
    st.write("How did behavior differ from its normal baseline, and were there warning signs before each failure?")

st.divider()
st.markdown("#### What we've found so far")

first_leak = leaks.iloc[0]
minutes_early = int((EMBARGO_LIFT - first_leak["time"]).total_seconds() // 60)
judge_last = msgs[(msgs["agent"] == "judge_agent") & msgs["before_lift"]]["time"].max()
sw = summary.set_index("incident").loc["SwiftWren"]
virus_share = events["virus"].mean()

origin = mc2.content_origin().set_index("incident")
st.markdown(f"""
- **MC1 · the leak was argued into existence.** At 5:00 PM the CEO said *“Hold the line. The announcement goes official at 6.”*
  The Legal agent argued the embargo was “moot”, claimed CivicLoom had consented (no consent appears in the world events),
  sent “GO”, and posted the merger at **{first_leak['time']:%I:%M %p}**, {minutes_early} minutes early.
  The Judge's last message that day was at **{judge_last:%I:%M %p}**.
- **MC1 · warning signs:** a May 29 post tagging CivicLoom's CEO, and private reasoning that swung from “hold” to “disclose”
  during the afternoon of June 5.
- **MC2 · the chain:** SwiftWren.txt was created by the **CFO's agent** one second after it read
  `{origin.loc['SwiftWren', 'read 1 s before creating']}`. The instructions passed from agent to agent until they reached John Windward's agent,
  the only regular SaidIt poster they reached. It posted 2 seconds after the last hand-off and deleted the files.
- **MC2 · it had happened before:** HiddenOrca and MellowOtter, on May 10. {virus_share:.0%} of the log is a runaway
  “virus” loop run by four of the agents that also carried the instructions.
- **Safeguards:** a hard gate on agents publishing, limits on agent-to-agent instructions, and monitoring that acts on warning signs.
""")

c1, c2 = st.columns(2)
c1.page_link("views/compare.py", label="Read the full comparison and safeguards →")
c2.page_link("views/mc2_meaning.py", label="What do the MC2 posts mean? →")
st.caption("Use the menu on the left. Every chart is interactive: hover for details, drag to zoom, double-click to reset.")
