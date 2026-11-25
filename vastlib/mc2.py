import networkx as nx
import pandas as pd
import streamlit as st

from vastlib.load import load_mc2


@st.cache_data
def incidents():
    ev = load_mc2()
    posts = ev[ev["content_source"].notna()].copy()
    posts["incident"] = posts["content_source"].str.replace(".txt", "", regex=False)
    return posts[["incident", "time", "actor", "content_source", "id"]].reset_index(drop=True)


@st.cache_data
def incident_events(name):
    ev = load_mc2()
    return ev[ev["details_text"].str.contains(name, regex=False)].copy()


@st.cache_data
def handoffs(name):
    ev = incident_events(name)
    h = ev[(ev["action"] == "queue_subordinate_task") & ev["target"].notna()]
    h = h[h["actor"] != h["target"]]
    return h[["time", "actor", "target"]].rename(columns={"actor": "from", "target": "to"}).reset_index(drop=True)


@st.cache_data
def incident_summary():
    rows = []
    for _, inc in incidents().iterrows():
        name = inc["incident"]
        ev = incident_events(name)
        h = handoffs(name)
        created = ev[ev["action"] == "create_file"]
        deleted = ev[ev["action"] == "delete_file"]
        first = ev["time"].min()
        rows.append({
            "incident": name,
            "created_by": created["actor"].iloc[0] if len(created) else None,
            "first_seen": first,
            "posted_by": inc["actor"],
            "posted_at": inc["time"],
            "hours_to_post": round((inc["time"] - first).total_seconds() / 3600, 1),
            "hand_offs": len(h),
            "agents_reached": len(set(h["from"]) | set(h["to"])),
            "files_deleted_after": len(deleted),
        })
    return pd.DataFrame(rows)


def origin_of(name):
    s = incident_summary().set_index("incident").loc[name]
    if pd.notna(s["created_by"]):
        return s["created_by"]
    return handoffs(name)["from"].iloc[0]


@st.cache_data
def first_reach(name):
    h = handoffs(name)
    origin = origin_of(name)
    first = h.drop_duplicates("to")
    return first[first["to"] != origin].reset_index(drop=True)


def path_to_poster(name):
    first = first_reach(name)
    T = nx.DiGraph()
    T.add_edges_from(zip(first["from"], first["to"]))
    poster = incident_summary().set_index("incident").loc[name, "posted_by"]
    try:
        return nx.shortest_path(T, origin_of(name), poster)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return [origin_of(name), poster]


def trigger_chain(name, max_steps=8):
    h = handoffs(name)
    s = incident_summary().set_index("incident").loc[name]
    origin = origin_of(name)
    who, t, steps = s["posted_by"], s["posted_at"], []
    while who != origin and len(steps) < max_steps:
        prev = h[(h["to"] == who) & (h["time"] < t)]
        if prev.empty:
            break
        r = prev.iloc[-1]
        steps.append(r)
        who, t = r["from"], r["time"]
    return pd.DataFrame(steps[::-1]).reset_index(drop=True)


@st.cache_data
def chain_steps(name):
    ev = incident_events(name)
    path = path_to_poster(name)
    first = first_reach(name)
    rows = []

    for _, r in ev[ev["action"] == "create_file"].iterrows():
        rows.append({"time": r["time"], "who": r["actor"], "phase": "origin", "step": f"creates {r['file']}"})
    first_path = first[first["to"].isin(path[1:])]
    for _, r in first_path.iterrows():
        phase = "origin" if r["from"] == origin_of(name) else "first arrival"
        rows.append({"time": r["time"], "who": r["from"], "phase": phase,
                     "step": f"hands the instructions to {r['to']}"})

    trig = trigger_chain(name)
    first_arrival_time = first_path["time"].max() if len(first_path) else None
    for _, r in trig.iterrows():
        if first_arrival_time is not None and r["time"] <= first_arrival_time:
            continue
        rows.append({"time": r["time"], "who": r["from"], "phase": "trigger",
                     "step": f"hands the instructions to {r['to']}"})

    post = ev[ev["content_source"].notna()].head(1)
    for _, r in post.iterrows():
        rows.append({"time": r["time"], "who": r["actor"], "phase": "post", "step": "POSTS the file to SaidIt"})
    for _, r in ev[ev["action"] == "delete_file"].iterrows():
        rows.append({"time": r["time"], "who": r["actor"], "phase": "post", "step": f"deletes {r['file']}"})
    return pd.DataFrame(rows).sort_values("time").reset_index(drop=True)


def poster_receipts(name):
    h = handoffs(name)
    s = incident_summary().set_index("incident").loc[name]
    got = h[h["to"] == s["posted_by"]].copy()
    got["seconds_before_post"] = (s["posted_at"] - got["time"]).dt.total_seconds()
    return got.reset_index(drop=True)


@st.cache_data
def content_origin():
    ev = load_mc2()
    rows = []
    for _, s in incident_summary().iterrows():
        name = s["incident"]
        inc = incident_events(name)
        created = inc[inc["action"] == "create_file"]
        source_doc, doc_reads, size = None, None, None
        if len(created):
            c = created.iloc[0]
            size = c["size_hint"] if pd.notna(c["size_hint"]) else None
            before = ev[(ev["actor"] == c["actor"]) & (ev["action"] == "read_file")
                        & (ev["time"] < c["time"]) & (ev["time"] >= c["time"] - pd.Timedelta(seconds=5))]
            if len(before):
                source_doc = before.iloc[-1]["file"]
                doc_reads = int((ev["file"] == source_doc).sum())
        receipts = poster_receipts(name)
        rows.append({
            "incident": name,
            "created by": s["created_by"] if pd.notna(s["created_by"]) else "(before the log starts)",
            "read 1 s before creating": source_doc or "—",
            "times that document is read in the whole log": doc_reads if doc_reads is not None else "—",
            "file size hint": f"{int(size):,}" if size else "—",
            "times the poster received it": len(receipts),
            "seconds from last hand-off to post": int(receipts["seconds_before_post"].min()),
            "files deleted within 3 s": int((inc[inc["action"] == "delete_file"]["time"] - s["posted_at"]
                                             ).dt.total_seconds().between(0, 3).sum()),
        })
    return pd.DataFrame(rows)


@st.cache_data
def saidit_posters():
    ev = load_mc2()
    normal = ev[(ev["action"] == "post_saidit") & ev["content_source"].isna() & ev["actor"].notna()]
    counts = normal.groupby("actor").size().rename("normal SaidIt posts").reset_index()
    reached = set()
    for n in incident_summary()["incident"]:
        h = handoffs(n)
        reached |= set(h["from"]) | set(h["to"])
    counts["reached by an incident chain"] = counts["actor"].isin(reached)
    return counts.sort_values("normal SaidIt posts", ascending=False).reset_index(drop=True)


@st.cache_data
def virus_spread():
    ev = load_mc2()
    v = ev[ev["virus"] & (ev["action"] == "queue_subordinate_task") & ev["target"].notna()]
    v = v[v["actor"] != v["target"]]
    return v[["time", "actor", "target"]].rename(columns={"actor": "from", "target": "to"}).reset_index(drop=True)


@st.cache_data
def virus_by_agent():
    ev = load_mc2()
    v = ev[ev["virus"]]
    return (v.groupby("actor")
             .agg(events=("id", "size"), start=("time", "min"), end=("time", "max"))
             .sort_values("start").reset_index())


@st.cache_data
def reach_times(name, blocked_agents=()):
    blocked = set(blocked_agents)
    origin = origin_of(name)
    start = incident_events(name)["time"].min()
    reached = {} if origin in blocked else {origin: (start, None)}
    for t, f, to in zip(handoffs(name)["time"], handoffs(name)["from"], handoffs(name)["to"]):
        if f in reached and to not in blocked and to not in reached:
            reached[to] = (t, f)
    rows = [{"agent": a, "time": t, "from": f} for a, (t, f) in reached.items()]
    return pd.DataFrame(rows, columns=["agent", "time", "from"]).sort_values("time").reset_index(drop=True)


def replay(name, blocked_agents=()):
    return set(reach_times(name, tuple(sorted(blocked_agents)))["agent"])


@st.cache_data
def single_block_table():
    summ = incident_summary()
    names = summ["incident"].tolist()
    agents = sorted(set().union(*[set(handoffs(n)["from"]) | set(handoffs(n)["to"]) for n in names]))
    rows = []
    for a in agents:
        row = {"agent": a}
        stopped = 0
        for n in names:
            reached = replay(n, blocked_agents=[a])
            poster = summ.set_index("incident").loc[n, "posted_by"]
            row[f"{n} reach"] = len(reached)
            row[f"{n} posted?"] = "yes" if poster in reached else "STOPPED"
            stopped += poster not in reached
        row["posts stopped"] = stopped
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["posts stopped", "agent"], ascending=[False, True]).reset_index(drop=True)


@st.cache_data
def best_pairs(exclude=()):
    summ = incident_summary().set_index("incident")
    names = summ.index.tolist()
    agents = sorted(set().union(*[set(handoffs(n)["from"]) | set(handoffs(n)["to"]) for n in names]) - set(exclude))
    rows = []
    for i, a in enumerate(agents):
        for b in agents[i + 1:]:
            stopped, reach = 0, 0
            for n in names:
                reached = replay(n, blocked_agents=[a, b])
                stopped += summ.loc[n, "posted_by"] not in reached
                reach += len(reached)
            rows.append({"block": f"{a} + {b}", "posts stopped": stopped, "total agents reached": reach})
    return (pd.DataFrame(rows).sort_values(["posts stopped", "total agents reached"], ascending=[False, True])
              .reset_index(drop=True))
