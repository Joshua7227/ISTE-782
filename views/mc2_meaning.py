"""MC2 · What do the posts mean? Where did their content come from? (MC2 question 2)

The log never contains the text of the posted files, so this page builds the case
from the actions around them.
"""
import plotly.express as px
import streamlit as st

from vastlib import mc2
from vastlib.charts import ACCENT, GREY, style
from vastlib.load import load_mc2, load_org

st.title("MC2 · What do the posts mean?")
st.caption("The log never contains the text of the posted files. This page builds the case from the actions around them.")

origin = mc2.content_origin()
org = load_org().set_index("person")

st.markdown("##### The evidence, incident by incident")
st.dataframe(origin.set_index("incident").T.astype(str))

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.markdown("**1 · The content came from executive documents**")
        st.write("One second before creating each file, the creator's agent read an internal document: "
                 "the **CFO's** agent read `meeting_notes.doc` before creating SwiftWren.txt, and the **COO's** agent "
                 "read `strategic_directions.doc` before creating MellowOtter.txt. Each document is read **only once** "
                 "in the entire 185,000-event log.")
    with st.container(border=True):
        st.markdown("**2 · It was scripted, not human**")
        st.write("Both files were made with the same machine-like rhythm, a day apart: read the document at 08:02:00, "
                 "create the file at :01, read the instructions at :02, hand them on at :03. Each post came exactly "
                 "**2 seconds** after a hand-off, and both files were **deleted within 2 seconds** of posting.")
with right:
    with st.container(border=True):
        st.markdown("**3 · The instructions travelled until they found a SaidIt poster**")
        posters = mc2.saidit_posters()
        reached = set().union(*[set(mc2.handoffs(n)["from"]) | set(mc2.handoffs(n)["to"]) for n in origin["incident"]])
        hit = posters.loc[posters["reached by an incident chain"], "actor"].tolist()
        st.write(f"Only {len(posters)} people post on SaidIt in normal work. The chains reached {len(reached)} different "
                 f"agents, but **{', '.join(hit)} {'is the only regular SaidIt poster' if len(hit) == 1 else 'are the only regular SaidIt posters'} "
                 f"any chain reached**, and every anomalous post came from there.")
    with st.container(border=True):
        st.markdown("**Our reading of the meaning**")
        st.write("The posts most likely publish the contents of confidential executive documents to a public forum. "
                 "They look like gibberish probably because the text was transformed or encoded on the way, which "
                 "is a data-exfiltration channel that hides in plain sight. *This is our inference: the log shows the "
                 "documents and the timing, not the text itself.*")

st.markdown("##### Who normally posts on SaidIt")
posters["label"] = posters["reached by an incident chain"].map({True: "reached by an incident chain", False: "not reached"})
fig = px.bar(posters, x="normal SaidIt posts", y="actor", orientation="h", color="label",
             color_discrete_map={"reached by an incident chain": ACCENT, "not reached": GREY})
fig.update_yaxes(autorange="reversed", title="")
st.plotly_chart(style(fig, 280))

st.markdown("##### What a normal SaidIt post looks like")
ev = load_mc2()
normal = ev[(ev["action"] == "post_saidit") & ev["content_source"].isna()].copy()
normal["content"] = normal["details"].apply(lambda d: d.get("content") if isinstance(d, dict) else None)
normal["forum"] = normal["details"].apply(lambda d: d.get("forum") if isinstance(d, dict) else None)
sample = normal.dropna(subset=["content"])
st.dataframe(sample[["time", "actor", "forum", "content"]].head(12), hide_index=True)
sizes = [str(x) for x in origin["file size hint"] if x != "—"]
st.caption(f"Normal posts are short work-topic titles (e.g. “{sample['content'].iloc[0]}”). The anomalous posts instead "
           f"published whole files (size hints {' and '.join(sizes)}).")
