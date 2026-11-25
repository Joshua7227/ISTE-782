import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from vastlib import mc2
from vastlib.charts import CHANNEL_COLORS, style
from vastlib.load import CHANNEL_NAMES, EMBARGO_LIFT, load_mc1, load_org

RED, TEAL, INK, MUTED, FAINT = "#b0303c", "#1f7a6f", "#1c1a20", "#5b5662", "#e3ddd3"
AGENT_ORDER = ["Judge", "Platform Trust", "PR", "Intern", "PR Intern", "Social Manager", "Legal"]


def _play_controls(frame_names, labels, duration=350, transition=250):
    return dict(
        updatemenus=[dict(
            type="buttons", direction="left", x=0, y=-0.1, xanchor="left", yanchor="top",
            pad=dict(r=8, t=0), showactive=False, bgcolor="#f1ede6", bordercolor="#d8d1c5",
            font=dict(size=14),
            buttons=[
                dict(label="▶  Play", method="animate",
                     args=[frame_names, dict(frame=dict(duration=duration, redraw=True), fromcurrent=False,
                                             mode="immediate",
                                             transition=dict(duration=transition, easing="cubic-in-out"))]),
                dict(label="❚❚  Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate",
                                        transition=dict(duration=0))]),
            ])],
        sliders=[dict(
            x=0.22, len=0.78, y=-0.06, yanchor="top", pad=dict(t=0, b=0), active=len(frame_names) - 1,
            currentvalue=dict(visible=False), font=dict(size=11),
            transition=dict(duration=transition),
            steps=[dict(label=l, method="animate",
                        args=[[n], dict(frame=dict(duration=0, redraw=True), mode="immediate",
                                        transition=dict(duration=transition))])
                   for n, l in zip(frame_names, labels)])])


def _wrap(text, width=70, limit=320):
    text = text if len(text) <= limit else text[:limit] + "…"
    words, lines, line = text.split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    lines.append(line)
    return "<br>".join(lines)


@st.cache_data(show_spinner=False)
def june5_replay(step_minutes=10, height=520):
    msgs, _, _ = load_mc1()
    start, end = pd.Timestamp("2046-06-05 09:00"), pd.Timestamp("2046-06-05 18:30")
    day = msgs[(msgs["time"] >= start) & (msgs["time"] <= end)].copy()
    day["hover"] = day["content"].apply(_wrap)
    day["symbol"] = day["mentions_merger"].map({True: "star", False: "circle"})
    day["size"] = day["mentions_merger"].map({True: 17, False: 10})
    channels = list(CHANNEL_COLORS)

    def traces_until(t):
        out = []
        for ch in channels:
            d = day[(day["channel"] == ch) & (day["time"] <= t)]
            out.append(go.Scatter(
                x=d["time"], y=d["agent_label"], mode="markers", name=CHANNEL_NAMES[ch], showlegend=False,
                marker=dict(color=CHANNEL_COLORS[ch], symbol=d["symbol"].tolist(), size=d["size"].tolist(),
                            line=dict(width=0.6, color="white")),
                customdata=d[["hover"]].values,
                hovertemplate="<b>%{y}</b> · %{x|%I:%M %p}<br>%{customdata[0]}<extra></extra>"))
        return out

    def frame_layout(t):
        mins = int((EMBARGO_LIFT - t).total_seconds() // 60)
        status = f"{mins} min until the embargo lifts" if mins > 0 else "embargo lifted"
        public = int((day["is_public"] & day["mentions_merger"] & (day["time"] <= t) & day["before_lift"]).sum())
        color = RED if public else INK
        return dict(
            shapes=[dict(type="line", x0=t, x1=t, y0=0, y1=1, yref="paper", line=dict(color=INK, width=1.5)),
                    dict(type="line", x0=EMBARGO_LIFT, x1=EMBARGO_LIFT, y0=0, y1=1, yref="paper",
                         line=dict(color=RED, width=2, dash="dash"))],
            annotations=[
                dict(x=0.01, y=1.13, xref="paper", yref="paper", xanchor="left", showarrow=False, align="left",
                     text=f"<b style='font-size:22px'>{t:%I:%M %p}</b>   {status}", font=dict(size=15, color=INK)),
                dict(x=0.99, y=1.13, xref="paper", yref="paper", xanchor="right", showarrow=False,
                     text=f"<b>{public}</b> public posts naming the merger before 6 PM",
                     font=dict(size=15, color=color)),
                dict(x=EMBARGO_LIFT, y=1.0, yref="paper", xanchor="left", yanchor="bottom", showarrow=False,
                     text=" embargo lifts", font=dict(color=RED, size=12))])

    times = list(pd.date_range(start, end, freq=f"{step_minutes}min"))
    names = [t.strftime("%H:%M") for t in times]
    frames = [go.Frame(data=traces_until(t), name=n, layout=frame_layout(t)) for t, n in zip(times, names)]
    fig = go.Figure(data=traces_until(times[-1]), frames=frames)
    for ch in channels:
        fig.add_trace(go.Scatter(x=[start - pd.Timedelta(hours=5)], y=[AGENT_ORDER[0]], mode="markers",
                                 name=CHANNEL_NAMES[ch], hoverinfo="skip",
                                 marker=dict(color=CHANNEL_COLORS[ch], size=10)))
    fig.add_trace(go.Scatter(x=[start - pd.Timedelta(hours=5)], y=[AGENT_ORDER[0]], mode="markers",
                             name="★ names the merger", hoverinfo="skip",
                             marker=dict(color="#8d8794", size=13, symbol="star")))
    fig.update_layout(**frame_layout(times[-1]))
    fig.update_layout(**_play_controls(names, [t.strftime("%I:%M %p") for t in times], duration=260, transition=200))
    fig.update_xaxes(range=[start - pd.Timedelta(minutes=10), end], tickformat="%I %p", title="")
    fig.update_yaxes(categoryorder="array", categoryarray=AGENT_ORDER, range=[-0.6, len(AGENT_ORDER) - 0.4], title="")
    style(fig, height)
    fig.update_layout(margin=dict(t=80, b=120), legend=dict(orientation="h", y=-0.32, x=0, yanchor="top"))
    return fig


def _display_names():
    org = load_org().set_index("person")
    return lambda p: org.loc[p, "name"] if p in org.index else p


@st.cache_data(show_spinner=False)
def _tree_layout(name):
    full = mc2.reach_times(name)
    T = nx.DiGraph()
    for a, f in zip(full["agent"], full["from"]):
        T.add_node(a)
        if isinstance(f, str):
            T.add_edge(f, a)
    pos = nx.kamada_kawai_layout(T.to_undirected())
    return {n: (float(x), float(y)) for n, (x, y) in pos.items()}


@st.cache_data(show_spinner=False)
def spread_replay(name, blocked=(), n_frames=40, height=560):
    blocked = tuple(sorted(blocked))
    s = mc2.incident_summary().set_index("incident").loc[name]
    poster, posted_at = s["posted_by"], s["posted_at"]
    full = mc2.reach_times(name)
    scen = mc2.reach_times(name, blocked)
    pos = _tree_layout(name)
    nodes = full["agent"].tolist()
    origin = mc2.origin_of(name)
    label = _display_names()
    start = full["time"].min()
    times = list(pd.date_range(start, posted_at, periods=n_frames))
    reach_at = dict(zip(scen["agent"], scen["time"]))
    parent = dict(zip(scen["agent"], scen["from"]))
    posted = poster in reach_at

    def state(t, final=False):
        ex, ey = [], []
        for a, tt in reach_at.items():
            p = parent.get(a)
            if isinstance(p, str) and tt <= t and a in pos and p in pos:
                ex += [pos[p][0], pos[a][0], None]
                ey += [pos[p][1], pos[a][1], None]
        colors, sizes, symbols, lines = [], [], [], []
        for n in nodes:
            on = n in reach_at and reach_at[n] <= t
            if n in blocked:
                colors.append("#2b2830"); symbols.append("x"); sizes.append(26); lines.append("#2b2830")
            elif n == poster and final and posted:
                colors.append(RED); symbols.append("star"); sizes.append(40); lines.append(RED)
            elif n == origin and on:
                colors.append(TEAL); symbols.append("circle"); sizes.append(28); lines.append("white")
            elif on:
                colors.append(MUTED); symbols.append("circle"); sizes.append(24); lines.append("white")
            else:
                colors.append(FAINT); symbols.append("circle"); sizes.append(20); lines.append(FAINT)
        edges = go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="rgba(92,86,98,0.55)", width=2), hoverinfo="skip")
        dots = go.Scatter(
            x=[pos[n][0] for n in nodes], y=[pos[n][1] for n in nodes], mode="markers+text",
            text=[label(n) for n in nodes], textposition="top center", textfont=dict(size=12, color=INK),
            marker=dict(color=colors, size=sizes, symbol=symbols, line=dict(width=1.5, color=lines)),
            hovertext=[f"{label(n)}<br>{'reached ' + reach_at[n].strftime('%b %d %I:%M %p') if n in reach_at else ('blocked' if n in blocked else 'never reached')}"
                       for n in nodes], hoverinfo="text")
        reached_now = sum(1 for n in nodes if n in reach_at and reach_at[n] <= t)
        if final:
            head = (f"<b style='color:{RED}'>{posted_at:%b %d, %I:%M %p} · {label(poster)}'s agent posts the file</b>"
                    if posted else f"<b style='color:{TEAL}'>Post prevented · the instructions never reached {label(poster)}</b>")
        else:
            head = f"<b style='font-size:20px'>{t:%b %d, %I:%M %p}</b>   {reached_now} agents reached"
        lay = dict(annotations=[dict(x=0.0, y=1.08, xref="paper", yref="paper", xanchor="left", showarrow=False,
                                     text=head, font=dict(size=15, color=INK))])
        return [edges, dots], lay

    frames, names, labels_ = [], [], []
    for i, t in enumerate(times):
        data, lay = state(t)
        frames.append(go.Frame(data=data, name=str(i), layout=lay))
        names.append(str(i)); labels_.append(t.strftime("%b %d %I %p"))
    data, lay = state(posted_at, final=True)
    frames.append(go.Frame(data=data, name="post", layout=lay))
    names.append("post"); labels_.append("the post")

    first, lay0 = state(posted_at, final=True)
    fig = go.Figure(data=first, frames=frames)
    fig.update_layout(**lay0)
    fig.update_layout(**_play_controls(names, labels_, duration=230, transition=180))
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    fig.update_xaxes(visible=False, range=[min(xs) - 0.25, max(xs) + 0.25])
    fig.update_yaxes(visible=False, range=[min(ys) - 0.2, max(ys) + 0.25])
    style(fig, height, legend=False)
    fig.update_layout(margin=dict(t=60, b=90))
    return fig


def whatif_bars(blocked, height=360):
    summ = mc2.incident_summary().set_index("incident")
    names = summ.index.tolist()
    before = [len(mc2.replay(n)) for n in names]
    after = [len(mc2.replay(n, blocked)) for n in names]
    posted = [summ.loc[n, "posted_by"] in mc2.replay(n, blocked) for n in names]
    who = " + ".join(_display_names()(b) for b in blocked)

    def bars(values, colors, texts):
        return [go.Bar(x=names, y=values, marker_color=colors, text=texts, textposition="outside",
                       textfont=dict(size=15), width=0.55)]

    as_is = bars(before, ["#8d8794"] * 3, [f"{v} agents · posted" for v in before])
    blocked_view = bars(after, [RED if p else TEAL for p in posted],
                        [f"{v} agents · {'still posted' if p else 'STOPPED'}" for v, p in zip(after, posted)])
    frames = [go.Frame(data=as_is, name="before"), go.Frame(data=blocked_view, name="after")]
    fig = go.Figure(data=as_is, frames=frames)
    anim = dict(frame=dict(duration=900, redraw=True), mode="immediate",
                transition=dict(duration=900, easing="cubic-in-out"))
    fig.update_layout(updatemenus=[dict(
        type="buttons", direction="left", x=0, y=1.18, xanchor="left", showactive=True,
        bgcolor="#f1ede6", bordercolor="#d8d1c5", font=dict(size=14),
        buttons=[dict(label="As it happened", method="animate", args=[["before"], anim]),
                 dict(label=f"▶  Block {who}", method="animate", args=[["after"], anim])])])
    fig.update_yaxes(range=[0, max(before) * 1.3], title="agents the instructions reached")
    style(fig, height, legend=False)
    fig.update_layout(margin=dict(t=70))
    return fig
