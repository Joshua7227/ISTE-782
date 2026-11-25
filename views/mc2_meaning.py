import plotly.express as px
import streamlit as st

from vastlib import mc2, ui
from vastlib.charts import ACCENT, GREY, style
from vastlib.load import load_mc2, load_org

ui.inject_css()
origin = mc2.content_origin().set_index("incident")
org = load_org().set_index("person")
ev = load_mc2()
posters = mc2.saidit_posters()
reached = set().union(*[set(mc2.handoffs(n)["from"]) | set(mc2.handoffs(n)["to"]) for n in origin.index])
hit = posters.loc[posters["reached by an incident chain"], "actor"].tolist()


def name_of(p):
    return org.loc[p, "name"] if p in org.index else p


ui.page_header(
    "Explore · Failure 2",
    "What did the posts contain?",
    "The log never records the text of the posted files. But the actions around them tell a clear story.")

ui.cards([
    (ui.ICONS["doc"], "It came from executive documents",
     f"One second before creating each file, the creator's agent opened an internal document: the "
     f"<b>CFO's</b> agent read <code>{origin.loc['SwiftWren', 'read 1 s before creating']}</code>, the "
     f"<b>COO's</b> read <code>{origin.loc['MellowOtter', 'read 1 s before creating']}</code>. "
     "Each is opened only once in the whole log."),
    (ui.ICONS["repeat"], "It looks automated, not human",
     "Both files were made to the same second-by-second rhythm, a day apart: open the document at 08:02:00, "
     "create the file at :01, read the instructions at :02, pass them on at :03."),
    (ui.ICONS["cut"], "It ended with the one regular poster",
     f"Only {len(posters)} people post on SaidIt in normal work. The instructions reached {len(reached)} agents, "
     f"and <b>{', '.join(name_of(h) for h in hit)}</b> was the only regular SaidIt poster among them."),
    (ui.ICONS["gate"], "Then it covered its tracks",
     "Every post came 2 seconds after a hand-off, and both files were deleted within 2 seconds of posting."),
])

ui.section("Our reading")
ui.notice("the posts most likely publish the contents of confidential executive documents (meeting notes, "
          "strategic directions) to a public forum, probably transformed or encoded on the way, which would explain "
          "why they looked like gibberish. <i>This is our inference: the log shows the documents and the timing, "
          "not the text itself.</i>")

ui.section("A normal post vs. an anomalous one", "Same account, very different posts.")
john = hit[0] if hit else "john_windward"
normal = ev[(ev["actor"] == john) & (ev["action"] == "post_saidit") & ev["post_content"].notna()]
ex = normal.iloc[0]
inc = mc2.incident_summary().set_index("incident").loc["SwiftWren"]
ui.row(
    ui.social_post("SaidIt", name_of(john), f"{ex['forum']} forum", f"{ex['time']:%b %d · %I:%M %p}",
                   ex["post_content"], pill="normal post", pill_kind="grey", color="#2f6690"),
    ui.social_post("SaidIt", name_of(john), "posted by his AI agent", f"{inc['posted_at']:%b %d · %I:%M %p}",
                   f"[the full contents of SwiftWren.txt; the log records its size as {origin.loc['SwiftWren', 'file size hint']}]",
                   pill="deleted 2 seconds later", color=ui.RED),
)

ui.section("Who normally posts on SaidIt", "Red = reached by the incident instructions.")
posters["name"] = posters["actor"].map(name_of)
posters["label"] = posters["reached by an incident chain"].map({True: "reached by the instructions", False: "not reached"})
fig = px.bar(posters, x="normal SaidIt posts", y="name", orientation="h", color="label",
             color_discrete_map={"reached by the instructions": ACCENT, "not reached": GREY}, labels={"name": "", "label": ""})
fig.update_yaxes(autorange="reversed")
st.plotly_chart(style(fig, 280), key="posters")

ui.section("What normal SaidIt posts look like")
samples = ev[(ev["action"] == "post_saidit") & ev["post_content"].notna()].drop_duplicates("actor").head(3)
ui.row(*[ui.social_post("SaidIt", name_of(r["actor"]), f"{r['forum']} forum", f"{r['time']:%b %d · %I:%M %p}",
                        r["post_content"], pill="normal post", pill_kind="grey", color="#2f6690")
         for _, r in samples.iterrows()])

with st.expander("The evidence table"):
    st.dataframe(origin.T.astype(str))
    st.caption("“File size hint” is the size field the log records for each created file.")
