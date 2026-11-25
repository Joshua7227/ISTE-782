import pandas as pd
import plotly.express as px
import streamlit as st

from vastlib import mc1, mc2, nlp, ui
from vastlib.charts import ACCENT, GREY, TEAL, style
from vastlib.load import load_mc1, load_mc2, load_org

ui.inject_css()
msgs, rounds, _ = load_mc1()
ev = load_mc2()
org = load_org().set_index("person")
leaks = mc1.public_leaks()
summary = mc2.incident_summary().set_index("incident")
sw = summary.loc["SwiftWren"]
judge = msgs[(msgs["agent"] == "judge_agent") & msgs["before_lift"]]
labels = nlp.stance_labels()
pairs = mc2.best_pairs(exclude=tuple(summary["posted_by"].unique()))
best = pairs[pairs["posts stopped"] == pairs["posts stopped"].max()]


def name_of(p):
    return org.loc[p, "name"] if p in org.index else p


ui.page_header(
    "Explore · How to stop it",
    "Both failures, side by side",
    "Two very different situations, one shared lesson: the agents could publish on their own, and nothing "
    "checked them at the last step.")

ui.section("At a glance")
rows = [
    ("What went wrong", "A secret merger was posted publicly before 6 PM",
     "Company files were posted to a public forum at 4:21 AM"),
    ("Who posted", f"The {leaks['agent_label'].iloc[0]} and Social Manager agents, from personal and anonymous accounts",
     f"{name_of(sw['posted_by'])}'s personal agent"),
    ("How many posts", f"{len(leaks)} before the embargo lifted", f"{len(summary)} file posts"),
    ("How it built up", "The Legal agent argued itself into it: ‘modifiable’ → ‘moot’ → ‘consent’ → ‘GO’",
     f"Instructions passed from agent to agent: {int(sw['hand_offs'])} hand-offs, {int(sw['agents_reached'])} agents"),
    ("First sign → failure", f"{(leaks['time'].iloc[0] - msgs[msgs['mentions_merger']]['time'].min()).days} days",
     f"{sw['hours_to_post'] / 24:.0f} days"),
    ("Earlier warnings", "A May 29 post hinting at ‘big things’ and tagging CivicLoom's CEO; the Intern repeating ‘CivicLoom’",
     "Two identical incidents a week earlier; a runaway virus loop on May 10–12"),
    ("Who was watching", f"A compliance agent (the Judge), silent after {judge['time'].max():%I:%M %p}",
     "No monitoring visible in the log"),
    ("Hiding it", "Anonymous accounts for some posts", "Files deleted within 2 seconds"),
    ("Instruction ignored", "CEO at 5 PM: “Hold the line.”", "None; no human was in the loop"),
]
st.table(pd.DataFrame(rows, columns=["", "Failure 1 · the merger leak", "Failure 2 · the 4:21 AM post"]).set_index(""))

ui.section("The warning signs, counted back from each failure",
           "Read right to left: the further right, the earlier the sign appeared.")
mc1_fail, mc2_fail = leaks["time"].iloc[0], sw["posted_at"]
vb = mc2.virus_by_agent()
signs = [
    ("Merger leak", msgs[msgs["mentions_merger"]]["time"].min(), "merger first named in a private chat"),
    ("Merger leak", pd.Timestamp("2046-05-29 09:00"), "‘big things coming’ post tags CivicLoom's CEO"),
    ("Merger leak", labels[labels["note"].str.contains("kitchen")]["time"].min(), "Intern repeats ‘CivicLoom’"),
    ("Merger leak", judge["time"].max(), "the Judge's last message"),
    ("Merger leak", labels[labels["stance"] == "disclose the deal"]["time"].min(), "first private push to announce"),
    ("Merger leak", mc1_fail, "FAILURE: first public merger post"),
    ("4:21 AM post", summary.loc["HiddenOrca", "first_seen"], "HiddenOrca instructions start moving"),
    ("4:21 AM post", summary.loc["HiddenOrca", "posted_at"], "HiddenOrca posted"),
    ("4:21 AM post", vb["start"].min(), "virus loop starts"),
    ("4:21 AM post", summary.loc["MellowOtter", "posted_at"], "MellowOtter posted"),
    ("4:21 AM post", vb["end"].max(), "virus loop ends"),
    ("4:21 AM post", mc2_fail, "FAILURE: SwiftWren posted"),
]
s = pd.DataFrame(signs, columns=["case", "time", "sign"]).dropna()
s["days before"] = [((mc1_fail if c == "Merger leak" else mc2_fail) - t).total_seconds() / 86400
                    for c, t in zip(s["case"], s["time"])]
s["kind"] = s["sign"].str.startswith("FAILURE").map({True: "failure", False: "warning sign"})
s["label"] = s["case"] + " · " + s["sign"]
s["when"] = pd.to_datetime(s["time"]).dt.strftime("%b %d, %I:%M %p")
s = s.sort_values(["case", "days before"], ascending=[True, False])
fig = px.scatter(s, x="days before", y="label", color="kind", facet_row="case",
                 color_discrete_map={"failure": ACCENT, "warning sign": TEAL},
                 hover_data={"when": True, "label": False, "case": False},
                 labels={"label": "", "days before": "days before the failure", "kind": "", "when": "time"},
                 category_orders={"label": s["label"].tolist()})
fig.update_traces(marker_size=14, hovertemplate="<b>%{y}</b><br>%{customdata[0]} · %{x:.1f} days before<extra></extra>")
fig.update_xaxes(autorange="reversed")
fig.update_yaxes(matches=None, showticklabels=True)
fig.for_each_annotation(lambda a: a.update(text=""))
st.plotly_chart(style(fig, 520), key="signs")
ui.notice("both failures gave signs more than a week ahead, and in the 4:21 AM case the exact same thing had "
          "already happened twice.")

ui.section("What we recommend")
ui.cards([
    (ui.ICONS["gate"], "1 · A gate on publishing",
     f"Agents posted publicly with no human sign-off in both failures. Require approval for any agent post, and "
     f"block posting during an embargo. <br><br><i>Evidence: {len(leaks)} early merger posts; {len(summary)} file posts, "
     "each 2 seconds after a hand-off.</i>"),
    (ui.ICONS["cut"], "2 · Limit agent-to-agent tasks",
     "Don't let an agent run a ‘read this and pass it on’ task from another agent's queue. Cap hand-offs, and flag a "
     f"file being passed around. <br><br><i>Evidence: blocking just {name_of('evelyn_dock')} and "
     f"{name_of('gabriel_sonar')} stops all {len(summary)} posts in the replay.</i>"),
    (ui.ICONS["radar"], "3 · Act on warning signs",
     "Alert when the compliance monitor goes quiet, when an agent's activity jumps far above its normal, and on any "
     "repeat incident. <br><br><i>Evidence: the Judge's silence, the virus loop, and two earlier incidents raised no response.</i>"),
])
st.page_link("views/what_if.py", label="Try your own safeguard in the what-if simulator →")

st.divider()
ui.section("Bonus: are the two datasets connected?")
link = ev[ev["details_text"].str.contains("CivicLoom|HarborCrest", case=False)].copy()
link["kind"] = link["action"].isin(["post_saidit", "post_flex"]).map({True: "public post (SaidIt / FleX)",
                                                                       False: "internal (tasks, meetings, contacts)"})
names = link["details_text"].str.extract(r"(HarborCrest ResidentEdge|CivicLoom Realty Partners)", expand=False).value_counts()
ui.takeaway(f"The merger's names from Failure 1 also appear in the Failure 2 office log: <b>{len(link)} times</b> "
            f"({', '.join(f'“{n}” {c}×' for n, c in names.items())}), including "
            f"<b>{(link['kind'].str.startswith('public')).sum()} public posts</b>, from {link['time'].min():%B %d}, "
            "nearly a month before the embargo day.")
weekly = link.groupby([pd.Grouper(key="time", freq="W"), "kind"]).size().reset_index(name="events")
fig = px.bar(weekly, x="time", y="events", color="kind",
             color_discrete_map={"public post (SaidIt / FleX)": ACCENT, "internal (tasks, meetings, contacts)": GREY},
             labels={"time": "week", "kind": ""})
st.plotly_chart(style(fig, 300), key="link")
st.caption("A caution: in the office log these read like an ordinary client or product name (e.g. “SLA Tracking "
           "Dashboard for CivicLoom Realty Partners”), and the VAST challenge warns that its datasets should not be "
           "assumed to be connected. We mention it as a curiosity, not as evidence.")
