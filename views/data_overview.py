import pandas as pd
import plotly.express as px
import streamlit as st

from vastlib import anim, ui
from vastlib.charts import ACCENT, CHANNEL_COLORS, GREY, round_labels, style
from vastlib.load import load_mc1, load_mc2, load_org

ui.inject_css()

ui.page_header(
    "About",
    "The data behind it",
    "Both datasets are synthetic (made up for the VAST Challenge 2026), and both are read straight from the "
    "challenge's zip files. Here is what's in them and how we cleaned them.")

tab2, tab1, tab_stats = st.tabs(["The office log (MC2)", "The comms team's messages (MC1)", "Summary statistics"])


def feature_summary(df, columns):
    rows = []
    for col in columns:
        s = df[col]
        row = {"feature": col, "type": str(s.dtype), "non-missing": int(s.notna().sum()),
               "missing %": round(100 * s.isna().mean(), 1)}
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            row.update({"distinct": s.nunique(), "min": s.min(), "mean": round(s.mean(), 2), "max": s.max(),
                        "most common": ""})
        elif pd.api.types.is_datetime64_any_dtype(s):
            row.update({"distinct": s.nunique(), "min": s.min(), "mean": "", "max": s.max(), "most common": ""})
        else:
            s = s.dropna().astype(str)
            top = s.value_counts()
            row.update({"distinct": s.nunique(), "min": "", "mean": "", "max": "",
                        "most common": f"{top.index[0][:40]} ({top.iloc[0]:,})" if len(top) else ""})
        rows.append(row)
    out = pd.DataFrame(rows)
    for c in ["min", "mean", "max"]:
        out[c] = out[c].astype(str)
    return out


with tab2:
    ev = load_mc2()
    org = load_org()
    ui.cards([
        (ui.big(f"{len(ev):,}"), "logged actions", "emails, files, tasks, meetings and posts"),
        (ui.big(str(len(org))), "employees", f"in {org['department'].nunique()} departments, each with an AI agent"),
        (ui.big(f"{(ev['time'].max() - ev['time'].min()).days} days"), "of activity",
         f"{ev['time'].min():%b %d} to {ev['time'].max():%b %d}, 2046"),
    ])

    ui.section("Actions per day", "Red = the runaway virus loop. Grey = everything else.")
    per_day = ev.groupby(["date", "virus"]).size().reset_index(name="actions")
    per_day["kind"] = per_day["virus"].map({True: "virus loop", False: "normal activity"})
    fig = px.bar(per_day, x="date", y="actions", color="kind",
                 color_discrete_map={"virus loop": ACCENT, "normal activity": GREY}, labels={"date": "", "kind": ""})
    st.plotly_chart(style(fig, 340), key="per_day")

    left, right = st.columns(2)
    with left:
        st.markdown("**The most common actions** (virus loop removed)")
        top = ev.loc[~ev["virus"], "action"].value_counts().head(15).sort_values()
        top.index = top.index.str.replace("_", " ")
        fig = px.bar(top, orientation="h", labels={"value": "actions", "index": "", "action": ""})
        fig.update_traces(marker_color=GREY)
        st.plotly_chart(style(fig, 420, legend=False), key="top_actions")
    with right:
        st.markdown("**Employees per department**")
        fig = px.bar(org["department"].value_counts().sort_values(), orientation="h",
                     labels={"value": "people", "department": ""})
        fig.update_traces(marker_color=GREY)
        st.plotly_chart(style(fig, 420, legend=False), key="depts")

    ui.section("How we cleaned it")
    st.table(pd.DataFrame([
        ["The same action had two names", "saidit_post / post_saidit, flex_post / post_flex", "merged into one name"],
        ["People were written three ways", "‘Owen Hatch’, person:owen_hatch, Agent/person:owen_hatch",
         "all become owen_hatch, plus whether it was the person or their agent"],
        ["Times were in UTC", "the 4:21 AM post is logged at 11:21", "converted to local time (UTC − 7)"],
        ["Hand-off targets in three different fields", "target_agent, target, or the second party", "one ‘target’ column"],
        ["A runaway loop", "75k actions tagged virus = true", "kept, but marked so it can be hidden"],
    ], columns=["Problem", "Example", "What we did"]).set_index("Problem"))

    with st.expander("Browse the cleaned log"):
        actions = st.multiselect("Show these actions", sorted(ev["action"].unique()), default=["post_saidit"])
        view = ev[ev["action"].isin(actions)] if actions else ev
        st.dataframe(view[["time", "actor", "actor_kind", "action", "target", "file", "virus", "details_text"]].head(2000),
                     hide_index=True)
        st.caption(f"{len(view):,} matching actions (showing up to 2,000).")

with tab1:
    msgs, rounds, parts = load_mc1()
    ui.cards([
        (ui.big(f"{len(msgs):,}"), "messages", f"from {msgs['agent'].nunique()} AI agents"),
        (ui.big(str(len(rounds))), "rounds", "one a day, then hourly on June 5"),
        (ui.big(str(int(msgs["has_reasoning"].sum()))), "with private thoughts", "what the agent was thinking"),
    ])

    ui.section("Messages per round, by where they were sent")
    per_round = msgs.groupby(["round", "channel"]).size().reset_index(name="messages")
    per_round["round"], order = round_labels(per_round["round"])
    per_round["where"] = per_round["channel"].map(anim.CHANNEL_NAMES)
    fig = px.bar(per_round, x="round", y="messages", color="where",
                 color_discrete_map={anim.CHANNEL_NAMES[c]: v for c, v in CHANNEL_COLORS.items()},
                 category_orders={"round": order}, labels={"round": "", "where": ""})
    fig.update_xaxes(type="category")
    st.plotly_chart(style(fig, 380), key="per_round")

    left, right = st.columns(2)
    with left:
        st.markdown("**Who talks where**")
        mat = pd.crosstab(msgs["agent_label"], msgs["channel"].map(anim.CHANNEL_NAMES))
        fig = px.imshow(mat, text_auto=True, aspect="auto", color_continuous_scale=["#fbf9f5", ACCENT],
                        labels=dict(x="", y="", color="messages"))
        st.plotly_chart(style(fig, 360, legend=False), key="who_where")
    with right:
        st.markdown("**The share price, round by round**")
        r = rounds.copy()
        r["label"] = r["round"].dt.strftime("%b %d %H:%M")
        r["status"] = r["price_suspicious"].map({True: "suspicious value", False: "ok"})
        fig = px.scatter(r.dropna(subset=["stock_price"]), x="label", y="stock_price", color="status",
                         color_discrete_map={"suspicious value": ACCENT, "ok": GREY},
                         labels={"label": "", "stock_price": "$", "status": ""})
        fig.update_traces(marker_size=10)
        fig.update_xaxes(type="category")
        st.plotly_chart(style(fig, 360), key="price")

    ui.section("Quirks we found")
    st.table(pd.DataFrame([
        ["Agent names differ from the README", "social_media_agent and judge_agent in the data; social_manager_agent and judge_eval_agent in the README"],
        ["Recipients are roles, not names", "e.g. ‘platform_trust’ means the quality agent"],
        ["Messages to ‘pr’ addressed to ‘@pr-intern’", "Legal's ‘GO’ orders on June 5 went to the PR channel"],
        ["Private thoughts are rare", f"only {int(msgs['has_reasoning'].sum())} of {len(msgs)} messages have them"],
        ["Odd share prices", "missing values, a ‘$180’ (almost certainly a typo), and a sudden drop to ‘$18.0’"],
    ], columns=["Quirk", "Detail"]).set_index("Quirk"))

with tab_stats:
    ui.section("Every feature we use, summarised",
               "Text columns show their most common value; numbers and dates show their range.")
    ev = load_mc2()
    st.markdown("**Office log (one row per action)**")
    st.dataframe(feature_summary(ev, ["time", "date", "hour", "action", "actor", "actor_kind", "target",
                                      "file", "virus", "content_source"]), hide_index=True)
    st.markdown("**Employees (from the org chart)**")
    st.dataframe(feature_summary(load_org(), ["person", "title", "team", "department"]), hide_index=True)
    msgs, rounds, parts = load_mc1()
    st.markdown("**Comms messages (one row per message)**")
    st.dataframe(feature_summary(msgs, ["time", "round", "agent", "channel", "message_type", "content",
                                        "has_reasoning", "mentions_merger", "is_public", "before_lift"]), hide_index=True)
    st.markdown("**Rounds (one row per round)**")
    st.dataframe(feature_summary(rounds, ["round", "headline", "stock_price", "market_sentiment", "price_suspicious"]),
                 hide_index=True)
    left, right = st.columns(2)
    with left:
        st.caption("Actions per agent per day")
        st.dataframe(ev[ev["actor_kind"] == "agent"].groupby(["actor", "date"]).size().describe().round(1)
                     .to_frame("actions per agent-day"))
    with right:
        st.caption("Message length (characters)")
        st.dataframe(msgs["content"].str.len().describe().round(1).to_frame("characters"))
