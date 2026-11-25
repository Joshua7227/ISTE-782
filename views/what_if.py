import streamlit as st

from vastlib import anim, mc2, ui
from vastlib.load import load_org

ui.inject_css()
summary = mc2.incident_summary().set_index("incident")
org = load_org().set_index("person")
all_agents = sorted(set().union(*[set(mc2.handoffs(n)["from"]) | set(mc2.handoffs(n)["to"]) for n in summary.index]))


def name_of(p):
    return org.loc[p, "name"] if p in org.index else p


ui.page_header(
    "Explore · How to stop it",
    "Could we have stopped it?",
    f"Choose agents to block. We then run a {ui.term('what-if replay')}: the real hand-offs, in the real order, "
    "except your blocked agents can't receive or pass anything on. Would the posts still have happened?")


@st.fragment
def simulator():
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        blocked = c1.multiselect("Agents to block", all_agents, default=["evelyn_dock", "gabriel_sonar"],
                                 format_func=name_of)
        name = c2.selectbox("Incident to replay", summary.index.tolist(), index=2)

    cols = st.columns(len(summary))
    for col, (inc, s) in zip(cols, summary.iterrows()):
        before, after = mc2.replay(inc), mc2.replay(inc, blocked)
        posted = s["posted_by"] in after
        status = ('<span class="vx-pill">still posted</span>' if posted
                  else '<span class="vx-pill ok">post prevented</span>')
        with col:
            ui.show(f'<div class="vx-card"><div style="font-weight:700;font-size:17px">{inc}</div>'
                    f'{ui.big(f"{len(after)} / {len(before)}", ui.RED if posted else ui.TEAL)}'
                    f'<div style="color:#5b5662;margin:6px 0 10px">agents reached, with your block</div>{status}</div>')

    ui.section("Before and after", "Press the ▶ Block button to animate the change.")
    if blocked:
        st.plotly_chart(anim.whatif_bars(tuple(blocked)), key="whatif_bars")
    else:
        ui.takeaway("Pick at least one agent to block.")
    ui.section(f"Replay {name} with your block",
               "Press ▶ Play. ✕ = a blocked agent. Faded dots are agents the instructions never reach.")
    st.plotly_chart(anim.spread_replay(name, tuple(blocked)), key=f"whatif_spread_{name}")


simulator()

ui.section("Which blocks work best?", "We tried every agent, and every pair of agents.")
left, right = st.columns(2)
with left:
    st.markdown("**Blocking one agent**")
    single = mc2.single_block_table()
    single.insert(0, "name", single["agent"].map(name_of))
    st.dataframe(single.drop(columns=["agent"]), hide_index=True, height=420)
with right:
    st.markdown("**Blocking two agents (not counting the poster)**")
    pairs = mc2.best_pairs(exclude=tuple(summary["posted_by"].unique()))
    pairs["block"] = pairs["block"].apply(lambda b: " + ".join(name_of(x) for x in b.split(" + ")))
    st.dataframe(pairs.head(15), hide_index=True, height=420)

best = pairs[pairs["posts stopped"] == pairs["posts stopped"].max()]
ui.notice(f"blocking John Windward's agent (the poster) stops everything, but that's the last step. Earlier in the "
          f"chain, {len(best)} pairs stop all {len(summary)} posts: " + "; ".join(f"<b>{b}</b>" for b in best["block"]) +
          ". Evelyn Dock and Gabriel Sonar neither created a file nor posted, and both also ran the virus loop.")
