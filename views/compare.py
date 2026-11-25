"""Comparing the two failures, and the safeguards we recommend.

Brings the findings from every other page together. All numbers are computed from the data.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from vastlib import mc1, mc2, nlp
from vastlib.charts import ACCENT, GREY, TEAL, style
from vastlib.load import EMBARGO_LIFT, load_mc1, load_mc2

st.title("Comparing the two failures")
st.caption("Two very different systems, the same lesson: the agents had the access to publish, and nothing checked them at the last step.")

msgs, rounds, _ = load_mc1()
ev = load_mc2()
leaks = mc1.public_leaks()
summary = mc2.incident_summary().set_index("incident")
sw = summary.loc["SwiftWren"]
judge = msgs[(msgs["agent"] == "judge_agent") & msgs["before_lift"]]
labels = nlp.stance_labels()
pairs = mc2.best_pairs(exclude=tuple(summary["posted_by"].unique()))
best = pairs[pairs["posts stopped"] == pairs["posts stopped"].max()]

# ---------------------------------------------------------------- side by side
st.markdown("##### Side by side")
rows = [
    ("What went wrong", "Embargoed merger posted publicly before 6 PM",
     "Internal files posted to a public forum at 4:21 AM"),
    ("Who did it", f"{leaks['agent_label'].iloc[0]} and Social Manager agents (personal and anonymous accounts)",
     "John Windward's personal agent"),
    ("How many public posts", f"{len(leaks)} before the embargo lifted", f"{len(summary)} file posts"),
    ("Chain behind it", "Agents talked each other into it: ‘bilateral, modifiable’ → ‘moot’ → ‘verbal consent’ → ‘GO’",
     f"Instructions passed agent to agent: {int(sw['hand_offs'])} hand-offs reaching {int(sw['agents_reached'])} agents"),
    ("Time from first signal to failure", f"{(leaks['time'].iloc[0] - msgs[msgs['mentions_merger']]['time'].min()).days} days "
     "(first private mention of the merger name)", f"{sw['hours_to_post']:.0f} hours (SwiftWren file created)"),
    ("Earlier warning signs", "May 29 ‘big things coming’ post tagging CivicLoom's CEO; the Intern repeating ‘CivicLoom’ on June 5",
     "Two identical incidents a week earlier; a runaway ‘virus’ loop on May 10–12"),
    ("Oversight in place", f"A compliance agent (the Judge), silent after {judge['time'].max():%I:%M %p}",
     "None visible in the log"),
    ("Covering tracks", "Anonymous accounts used for some posts", "Both files deleted within 2 seconds of posting"),
    ("Instruction ignored", "CEO at 5:00 PM: “Hold the line. The announcement goes official at 6.”",
     "— (no human instruction in the chain)"),
]
st.table(pd.DataFrame(rows, columns=["", "MC1 · Embargo leak", "MC2 · Anomalous post"]).set_index(""))

# ---------------------------------------------------------------- warning signs on one axis
st.markdown("##### Warning signs, counted back from each failure")
mc1_fail, mc2_fail = leaks["time"].iloc[0], sw["posted_at"]
vb = mc2.virus_by_agent()
signs = [
    ("MC1", msgs[msgs["mentions_merger"]]["time"].min(), "first private mention of the merger name"),
    ("MC1", pd.Timestamp("2046-05-29 09:00"), "‘big things coming’ post tags CivicLoom's CEO"),
    ("MC1", labels[labels["note"].str.contains("kitchen")]["time"].min(), "Intern repeats ‘CivicLoom’"),
    ("MC1", judge["time"].max(), "Judge's last message"),
    ("MC1", labels[labels["stance"] == "disclose the deal"]["time"].min(), "first private argument to disclose"),
    ("MC1", mc1_fail, "FAILURE: first public merger post"),
    ("MC2", summary.loc["HiddenOrca", "first_seen"], "HiddenOrca instructions start circulating"),
    ("MC2", summary.loc["HiddenOrca", "posted_at"], "HiddenOrca posted"),
    ("MC2", vb["start"].min(), "virus loop starts"),
    ("MC2", summary.loc["MellowOtter", "posted_at"], "MellowOtter posted"),
    ("MC2", vb["end"].max(), "virus loop ends"),
    ("MC2", mc2_fail, "FAILURE: SwiftWren posted"),
]
s = pd.DataFrame(signs, columns=["case", "time", "sign"]).dropna()
s["days before failure"] = [((mc1_fail if c == "MC1" else mc2_fail) - t).total_seconds() / 86400
                            for c, t in zip(s["case"], s["time"])]
s["kind"] = s["sign"].str.startswith("FAILURE").map({True: "failure", False: "warning sign"})
s["label"] = s["case"] + " · " + s["sign"]
s = s.sort_values(["case", "days before failure"], ascending=[True, False])
fig = px.scatter(s, x="days before failure", y="label", color="kind", facet_row="case",
                 color_discrete_map={"failure": ACCENT, "warning sign": TEAL},
                 hover_data={"time": "|%b %d %I:%M %p", "label": False, "case": False},
                 labels={"label": ""}, category_orders={"label": s["label"].tolist()})
fig.update_traces(marker_size=13)
fig.update_xaxes(autorange="reversed")
fig.update_yaxes(matches=None, showticklabels=True)
fig.for_each_annotation(lambda a: a.update(text=""))  # the case is already in each label
st.plotly_chart(style(fig, 520))
st.caption("Both failures had signs more than a week ahead. In MC2 the exact same thing had already happened twice.")

# ---------------------------------------------------------------- safeguards
st.markdown("##### Safeguards we recommend")
c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.markdown("**1 · A hard gate on publishing**")
        st.write("Agents could post publicly with no human sign-off, in both cases. Require a human approval for any "
                 "post from an agent, and block posting entirely during an embargo window.")
        st.caption(f"Evidence: {len(leaks)} pre-embargo posts in MC1; {len(summary)} file posts in MC2, each 2 s after a hand-off.")
with c2:
    with st.container(border=True):
        st.markdown("**2 · Stop instructions travelling between agents**")
        st.write("An agent should not run a 'read this file and pass it on' task from another agent's queue. Cap or "
                 "review agent-to-agent hand-offs, and flag a file being handed around repeatedly.")
        st.caption(f"Evidence (what-if): blocking just {' or '.join(best['block'].head(2))} would have stopped "
                   f"{int(best['posts stopped'].iloc[0])} of {len(summary)} posts.")
with c3:
    with st.container(border=True):
        st.markdown("**3 · Monitoring that acts on warning signs**")
        st.write("The Judge went quiet for the decisive hours; the virus loop and two earlier incidents raised no "
                 "response. Alert on silence from oversight, on activity far above an agent's baseline, and on any repeat incident.")
        st.caption("Evidence: see Baselines & warning signs, and the chart above.")

st.page_link("views/what_if.py", label="Try your own interventions in the what-if simulator →")

# ---------------------------------------------------------------- bonus: a possible link between the datasets
st.divider()
st.markdown("##### Bonus: a possible link between the two datasets")
link = ev[ev["details_text"].str.contains("CivicLoom|HarborCrest", case=False)].copy()
link["kind"] = link["action"].isin(["post_saidit", "post_flex"]).map({True: "public post (SaidIt / FleX)",
                                                                       False: "internal (tasks, meetings, contacts)"})
names = link["details_text"].str.extract(r"(HarborCrest ResidentEdge|CivicLoom Realty Partners)", expand=False).value_counts()
st.write(f"The MC1 merger names also appear in the MC2 log: **{len(link)} events** mention them "
         f"({', '.join(f'“{n}” {c}×' for n, c in names.items())}), including "
         f"**{(link['kind'].str.startswith('public')).sum()} public SaidIt/FleX posts**, starting on "
         f"{link['time'].min():%B %d}, nearly a month before the MC1 embargo day.")
weekly = link.groupby([pd.Grouper(key="time", freq="W"), "kind"]).size().reset_index(name="events")
fig = px.bar(weekly, x="time", y="events", color="kind",
             color_discrete_map={"public post (SaidIt / FleX)": ACCENT, "internal (tasks, meetings, contacts)": GREY},
             labels={"time": "week"})
st.plotly_chart(style(fig, 300))
st.caption("Caution: in MC2 these read like an ordinary client or product name (e.g. “SLA Tracking Dashboard for CivicLoom "
           "Realty Partners”), and the VAST challenge warns that its datasets should not be assumed to be continuous. "
           "We treat this as a curiosity worth mentioning, not as evidence that the two failures are connected.")
