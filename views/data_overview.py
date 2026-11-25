"""The data: what's in each dataset, and how we cleaned it."""
import pandas as pd
import plotly.express as px
import streamlit as st

from vastlib.charts import ACCENT, CHANNEL_COLORS, GREY, round_labels, style
from vastlib.load import load_mc1, load_mc2, load_org

st.title("The data")
st.caption("Both datasets are synthetic, from the VAST Challenge 2026. They are read straight from the zip files in data/.")

tab2, tab1, tab_stats = st.tabs(["MC2 · Event log", "MC1 · Agent messages", "Summary statistics"])


def feature_summary(df, columns):
    """One row per feature: type, missing values, distinct values, and range or most common value."""
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

# ---------------------------------------------------------------------------
with tab2:
    ev = load_mc2()
    org = load_org()

    c = st.columns(5)
    c[0].metric("Events", f"{len(ev):,}")
    c[1].metric("People", len(org))
    c[2].metric("Departments", org["department"].nunique())
    c[3].metric("Action types (raw → clean)", f"{ev['action_raw'].nunique()} → {ev['action'].nunique()}")
    c[4].metric("Days covered", (ev["time"].max() - ev["time"].min()).days)

    st.markdown("##### Events per day")
    per_day = ev.groupby(["date", "virus"]).size().reset_index(name="events")
    per_day["kind"] = per_day["virus"].map({True: "virus loop", False: "normal activity"})
    fig = px.bar(per_day, x="date", y="events", color="kind",
                 color_discrete_map={"virus loop": ACCENT, "normal activity": GREY})
    st.plotly_chart(style(fig, 360))
    st.caption("The spike on May 10–12 is almost entirely the self-repeating 'virus' loop (see Baselines & warning signs).")

    left, right = st.columns(2)
    with left:
        st.markdown("##### Most common actions (virus loop removed)")
        top = ev.loc[~ev["virus"], "action"].value_counts().head(15).sort_values()
        fig = px.bar(top, orientation="h", labels={"value": "events", "index": ""})
        fig.update_traces(marker_color=GREY)
        st.plotly_chart(style(fig, 420, legend=False))
    with right:
        st.markdown("##### People per department")
        fig = px.bar(org["department"].value_counts().sort_values(), orientation="h")
        fig.update_traces(marker_color=GREY)
        st.plotly_chart(style(fig, 420, legend=False))

    st.markdown("##### How we cleaned it")
    st.dataframe(pd.DataFrame([
        ["Same action, two names", "saidit_post vs post_saidit, flex_post vs post_flex", "Merged into one name"],
        ["Three name formats", "'Owen Hatch', person:owen_hatch, Agent/person:owen_hatch", "All become owen_hatch, plus an actor_kind column (agent / person / system)"],
        ["UTC timestamps", "The 4:21 AM post is logged at 11:21", "Converted to local time (UTC − 7)"],
        ["Hand-off target in 3 different fields", "target_agent, target, or the 2nd party", "One 'target' column"],
        ["Virus loop", "75k events (41%) tagged virus=True", "Kept, but flagged so baselines can exclude it"],
    ], columns=["Problem", "Example", "Fix"]), hide_index=True)

    with st.expander("Browse the cleaned events"):
        actions = st.multiselect("Actions", sorted(ev["action"].unique()), default=["post_saidit"])
        view = ev[ev["action"].isin(actions)] if actions else ev
        st.dataframe(view[["time", "actor", "actor_kind", "action", "target", "file", "virus", "details_text"]].head(2000),
                     hide_index=True)
        st.caption(f"{len(view):,} matching events (showing up to 2,000).")

# ---------------------------------------------------------------------------
with tab1:
    msgs, rounds, parts = load_mc1()

    c = st.columns(5)
    c[0].metric("Messages", f"{len(msgs):,}")
    c[1].metric("Rounds", len(rounds))
    c[2].metric("Agents", msgs["agent"].nunique())
    c[3].metric("Channels", msgs["channel"].nunique())
    c[4].metric("With private reasoning", int(msgs["has_reasoning"].sum()))

    st.markdown("##### Messages per round, by channel")
    per_round = msgs.groupby(["round", "channel"]).size().reset_index(name="messages")
    per_round["round"], order = round_labels(per_round["round"])
    fig = px.bar(per_round, x="round", y="messages", color="channel", color_discrete_map=CHANNEL_COLORS,
                 category_orders={"round": order}, labels={"round": ""})
    fig.update_xaxes(type="category")
    st.plotly_chart(style(fig, 380))
    st.caption("Most rounds are one per day at 9 AM. June 5 (the crisis day) is logged hour by hour from 9 AM to 6 PM.")

    left, right = st.columns(2)
    with left:
        st.markdown("##### Who talks on which channel")
        mat = pd.crosstab(msgs["agent_label"], msgs["channel"])
        fig = px.imshow(mat, text_auto=True, aspect="auto", color_continuous_scale=["#fbf9f5", ACCENT])
        st.plotly_chart(style(fig, 360, legend=False))
    with right:
        st.markdown("##### Stock price by round")
        r = rounds.copy()
        r["label"] = r["round"].dt.strftime("%b %d %H:%M")
        r["status"] = r["price_suspicious"].map({True: "suspicious value", False: "ok"})
        fig = px.scatter(r.dropna(subset=["stock_price"]), x="label", y="stock_price", color="status",
                         color_discrete_map={"suspicious value": ACCENT, "ok": GREY})
        fig.update_traces(marker_size=9)
        fig.update_xaxes(type="category")
        st.plotly_chart(style(fig, 360))

    st.markdown("##### Data quirks we found")
    st.dataframe(pd.DataFrame([
        ["Agent IDs differ from the README", "social_media_agent and judge_agent in the data vs social_manager_agent and judge_eval_agent in the README"],
        ["Recipients are roles, not IDs", "e.g. 'platform_trust' means quality_agent; mapped in load.py"],
        ["Messages to 'pr' addressed to '@pr-intern'", "Legal's 'GO' orders on June 5 went to the PR channel, not PR-Intern"],
        ["Private reasoning is rare", f"Only {int(msgs['has_reasoning'].sum())} of {len(msgs)} messages have it"],
        ["Odd stock prices", "Missing values, a '$180' (almost certainly a typo), and a sudden drop to '$18.0'"],
    ], columns=["Quirk", "Detail"]), hide_index=True)

# ---------------------------------------------------------------------------
with tab_stats:
    st.markdown("##### Every feature we use, summarised")
    st.caption("Computed on the cleaned data. Text columns show their most common value; numbers and dates show their range.")

    ev = load_mc2()
    st.markdown("**MC2 · events** (one row per event)")
    st.dataframe(feature_summary(ev, ["time", "date", "hour", "action", "actor", "actor_kind", "target",
                                      "file", "virus", "content_source"]), hide_index=True)

    st.markdown("**MC2 · people** (from the org chart)")
    st.dataframe(feature_summary(load_org(), ["person", "title", "team", "department"]), hide_index=True)

    msgs, rounds, parts = load_mc1()
    st.markdown("**MC1 · messages** (one row per message)")
    st.dataframe(feature_summary(msgs, ["time", "round", "agent", "channel", "message_type", "content",
                                        "has_reasoning", "mentions_merger", "is_public", "before_lift"]), hide_index=True)

    st.markdown("**MC1 · rounds** (one row per round)")
    st.dataframe(feature_summary(rounds, ["round", "headline", "stock_price", "market_sentiment", "price_suspicious"]),
                 hide_index=True)

    st.markdown("**Numeric summaries**")
    left, right = st.columns(2)
    with left:
        per_agent = ev[ev["actor_kind"] == "agent"].groupby(["actor", "date"]).size()
        st.caption("MC2 · events per agent per day")
        st.dataframe(per_agent.describe().round(1).to_frame("events per agent-day"))
    with right:
        st.caption("MC1 · message length (characters)")
        st.dataframe(msgs["content"].str.len().describe().round(1).to_frame("characters"))
