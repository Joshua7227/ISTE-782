"""
Loading and cleaning for both datasets.

Every page calls these functions. @st.cache_data means the JSON is read
and cleaned only once, then reused, so pages switch instantly.

The data is read straight from the two VAST zip files in the data/ folder,
so nobody has to unzip anything.
"""
import json
import re
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MC1_ZIP = DATA_DIR / "VAST_Challenge_2026_MC1.zip"
MC2_ZIP = DATA_DIR / "VAST_Challenge_2026_MC2.zip"

# MC2 timestamps are UTC. The challenge says the post was at 4:21 AM local,
# and the log shows 11:21 UTC, so local time = UTC - 7 hours.
LOCAL_OFFSET = pd.Timedelta(hours=7)

# Words that reveal the embargoed merger (MC1)
MERGER_PATTERN = r"CivicLoom|HarborCrest"
EMBARGO_LIFT = pd.Timestamp("2046-06-05 18:00")


def _read_json_from_zip(zip_path, ends_with):
    with zipfile.ZipFile(zip_path) as z:
        name = next(n for n in z.namelist() if n.endswith(ends_with) and "__MACOSX" not in n)
        return json.loads(z.read(name))


# ---------------------------------------------------------------------------
# MC2: event log + org chart
# ---------------------------------------------------------------------------

def clean_name(p):
    """'Agent/person:owen_hatch', 'person:owen_hatch', 'Owen Hatch' -> 'owen_hatch'."""
    if p is None:
        return None
    p = str(p)
    if ":" in p:
        return p.split(":")[-1]
    return p.strip().lower().replace(" ", "_")


def actor_kind(p):
    p = str(p)
    if p.startswith("Agent/"):
        return "agent"
    if p.startswith("person:") or (":" not in p and " " in p):
        return "person"
    if p.startswith("agent"):
        return "agent"
    return "system"


def _target_of(details, parties):
    """Who a task was handed to. The log uses three different field names."""
    if isinstance(details, dict):
        for key in ("target_agent", "target"):
            val = details.get(key)
            if isinstance(val, str) and ("person" in val or "Agent" in val):
                return clean_name(val)
    if len(parties) > 1 and "person" in str(parties[1]):
        return clean_name(parties[1])
    return None


# The same action is logged under two names
SAME_ACTION = {"saidit_post": "post_saidit", "flex_post": "post_flex"}


@st.cache_data(show_spinner="Loading the MC2 event log…")
def load_mc2():
    raw = _read_json_from_zip(MC2_ZIP, "MC2 data.json")
    df = pd.DataFrame(raw["events"])

    df["time"] = pd.to_datetime(df["when"], unit="s") - LOCAL_OFFSET
    df["date"] = df["time"].dt.date
    df["hour"] = df["time"].dt.hour
    df["action_raw"] = df["short_name"]
    df["action"] = df["short_name"].replace(SAME_ACTION)

    first_party = df["parties"].apply(lambda ps: ps[0] if ps else None)
    df["actor"] = first_party.apply(clean_name)
    df["actor_kind"] = first_party.apply(actor_kind)
    df["target"] = [
        _target_of(d, ps) if a == "queue_subordinate_task" else None
        for d, ps, a in zip(df["details"], df["parties"], df["action"])
    ]
    df["virus"] = df["details"].apply(lambda d: bool(isinstance(d, dict) and d.get("virus")))
    df["file"] = df["details"].apply(
        lambda d: (d.get("target") if isinstance(d, dict) and isinstance(d.get("target"), str)
                   and d.get("action") in ("create_file", "read_file", "delete_file") else None))
    df["content_source"] = df["details"].apply(
        lambda d: d.get("content_source") if isinstance(d, dict) else None)
    # A text version of details, so pages can search it quickly
    df["details_text"] = df["details"].apply(lambda d: json.dumps(d, ensure_ascii=False))

    df = df.sort_values("time").reset_index(drop=True)
    return df.drop(columns=["when", "short_name"])


@st.cache_data
def load_org():
    """One row per person: name, title, team, department."""
    raw = _read_json_from_zip(MC2_ZIP, "org_chart.json")
    nodes = {n["id"]: n for n in raw["nodes"]}
    parent = {e["target"]: e["source"] for e in raw["edges"] if e["relation"] == "contains"}
    # department leads are linked with 'led_by' (department -> person), not 'contains'
    for e in raw["edges"]:
        if e["relation"] == "led_by":
            parent.setdefault(e["target"], e["source"])

    rows = []
    for nid, n in nodes.items():
        if n["type"] != "person":
            continue
        team = parent.get(nid)
        dept = parent.get(team) if team else None
        # some people sit directly under a department
        if team and nodes[team]["type"] == "department":
            dept, team = team, None
        rows.append({
            "person": clean_name(nid),
            "name": n.get("label"),
            "title": n.get("title"),
            "team": nodes[team]["label"] if team else "(no team)",
            "department": nodes[dept]["label"] if dept else "(none)",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# MC1: rounds of agent messages
# ---------------------------------------------------------------------------

# Recipients are written as roles; map them to agent ids
ROLE_TO_AGENT = {
    "legal": "legal_agent",
    "platform_trust": "quality_agent",
    "social_manager": "social_media_agent",
    "pr": "pr_agent",
    "pr_intern": "pr_intern_agent",
    "intern": "intern_agent",
    "judge": "judge_agent",
}
AGENT_LABEL = {
    "legal_agent": "Legal",
    "quality_agent": "Platform Trust",
    "social_media_agent": "Social Manager",
    "pr_agent": "PR",
    "pr_intern_agent": "PR Intern",
    "intern_agent": "Intern",
    "judge_agent": "Judge",
}
PUBLIC_CHANNELS = ["official_post", "personal_post", "anonymous_post"]


def _price(x):
    try:
        return float(str(x).replace("$", ""))
    except ValueError:
        return None


@st.cache_data(show_spinner="Loading the MC1 messages…")
def load_mc1():
    """Returns (messages, rounds, participants) DataFrames."""
    raw = _read_json_from_zip(MC1_ZIP, ".json")["rounds"]

    msgs, rounds, parts = [], [], []
    for r in raw:
        env = r["environment_context"]
        snap = env.get("market_snapshot") or {}
        rounds.append({
            "round": pd.Timestamp(r["hour"]),
            "headline": env.get("event_headline"),
            "narrative": env.get("event_narrative"),
            "stock_price_raw": snap.get("stock_price"),
            "stock_price": _price(snap.get("stock_price")),
            "market_sentiment": snap.get("sentiment"),
            "unavailable": ", ".join(env.get("agents_unavailable") or []),
        })
        for p in r.get("participants", []):
            meta = p.get("agent_round_metadata") or {}
            parts.append({
                "round": pd.Timestamp(r["hour"]),
                "agent": p["agent_id"],
                "declared_action": p.get("declared_action"),
                "sentiment": meta.get("sentiment_at_turn"),
                "action_class": meta.get("action_classification"),
            })
        for m in r["communications"]:
            state = m.get("internal_state") or {}
            msgs.append({
                "message_id": m["message_id"],
                "round": pd.Timestamp(r["hour"]),
                "time": pd.Timestamp(m["timestamp"]),
                "agent": m["agent_id"],
                "channel": m["channel"],
                "message_type": m["message_type"],
                "recipients": m["recipients"],
                "responding_to": m.get("responding_to"),
                "content": str(m.get("content") or ""),
                "reacting": state.get("reacting"),
                "rationalizing": state.get("rationalizing"),
                "deliberating": state.get("deliberating"),
            })

    df = pd.DataFrame(msgs).sort_values("time").reset_index(drop=True)
    df["agent_label"] = df["agent"].map(AGENT_LABEL).fillna(df["agent"])
    df["has_reasoning"] = df[["reacting", "rationalizing", "deliberating"]].notna().any(axis=1)
    df["mentions_merger"] = df["content"].str.contains(MERGER_PATTERN, case=False, regex=True)
    df["is_public"] = df["channel"].isin(PUBLIC_CHANNELS)
    df["before_lift"] = df["time"] < EMBARGO_LIFT
    df["recipient_agents"] = df["recipients"].apply(
        lambda rs: ["ALL"] if "ALL" in rs else [ROLE_TO_AGENT.get(x, x) for x in rs])

    rounds = pd.DataFrame(rounds)
    rounds["price_suspicious"] = rounds["stock_price"] > 100  # "$180" is a typo
    return df, rounds, pd.DataFrame(parts)
