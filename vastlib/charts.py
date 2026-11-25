import math

import networkx as nx
import plotly.graph_objects as go

ACCENT = "#b0303c"
TEAL = "#1f7a6f"
GREY = "#9a96a0"
INK = "#1c1a20"

CHANNEL_COLORS = {
    "comms_huddle": "#9a96a0",
    "side_huddle": "#6b5b7a",
    "one_on_one_chat": "#c9a227",
    "official_post": "#1f7a6f",
    "personal_post": "#b0303c",
    "anonymous_post": "#e07a5f",
}

INCIDENT_COLORS = {"HiddenOrca": "#6b5b7a", "MellowOtter": "#c9a227", "SwiftWren": ACCENT}


def style(fig, height=420, legend=True):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans Pro, Arial, sans-serif", size=13),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hoverlabel=dict(bgcolor="white", font_size=13),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    return fig


def vline(fig, x, text, color=ACCENT, y=1.0, xanchor="left"):
    fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1, yref="paper",
                  line=dict(color=color, dash="dash", width=1.5))
    fig.add_annotation(x=x, y=y, yref="paper", text=text, showarrow=False, bgcolor="rgba(251,249,245,0.85)",
                       xanchor=xanchor, yanchor="bottom", font=dict(color=color, size=12))
    return fig


def incident_lines(fig, summary, as_date_string=False):
    for i, (day, g) in enumerate(summary.groupby(summary["posted_at"].dt.date)):
        x = str(day) if as_date_string else g["posted_at"].min()
        vline(fig, x, f"{day:%b %d}: " + ", ".join(g["incident"]), color=TEAL, y=1.0 + 0.035 * i)
    fig.update_layout(margin=dict(t=70))
    return fig


ROUND_FORMAT = "%b %d %H:%M"


def round_labels(rounds):
    order = [t.strftime(ROUND_FORMAT) for t in sorted(rounds.unique())]
    return rounds.dt.strftime(ROUND_FORMAT), order


def network_figure(edges, weight_col=None, highlight_nodes=(), highlight_edges=(),
                   origin=None, layout="spring", pos=None, height=520):
    G = nx.DiGraph()
    for _, r in edges.iterrows():
        w = r[weight_col] if weight_col else 1
        if G.has_edge(r["from"], r["to"]):
            G[r["from"]][r["to"]]["w"] += w
        else:
            G.add_edge(r["from"], r["to"], w=w)
    if G.number_of_nodes() == 0:
        return style(go.Figure(), height)

    if pos is None:
        if layout == "circle":
            pos = nx.circular_layout(G)
        else:
            pos = nx.spring_layout(G, seed=7, k=1.2 / math.sqrt(G.number_of_nodes()))

    highlight_nodes, highlight_edges = set(highlight_nodes), set(highlight_edges)
    max_w = max(d["w"] for _, _, d in G.edges(data=True))
    fig = go.Figure()

    for u, v, d in G.edges(data=True):
        on = (u, v) in highlight_edges
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode="lines", hoverinfo="skip", showlegend=False,
            line=dict(width=(4 if on else 1 + 5 * d["w"] / max_w), color=ACCENT if on else "rgba(120,120,130,0.45)")))
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=1,
                           arrowcolor=ACCENT if on else "rgba(120,120,130,0.6)", standoff=10, text="")

    nodes = list(G.nodes)
    colors = [TEAL if n == origin else ACCENT if n in highlight_nodes else GREY for n in nodes]
    degree = dict(G.degree(weight="w"))
    fig.add_trace(go.Scatter(
        x=[pos[n][0] for n in nodes], y=[pos[n][1] for n in nodes], mode="markers+text",
        text=nodes, textposition="top center", showlegend=False,
        marker=dict(size=[14 + 18 * degree[n] / max(degree.values()) for n in nodes], color=colors,
                    line=dict(width=1, color="white")),
        hovertext=[f"{n}<br>sent: {G.out_degree(n, weight='w')}<br>received: {G.in_degree(n, weight='w')}" for n in nodes],
        hoverinfo="text"))
    fig.update_xaxes(visible=False, range=[min(p[0] for p in pos.values()) - 0.3, max(p[0] for p in pos.values()) + 0.3])
    fig.update_yaxes(visible=False, range=[min(p[1] for p in pos.values()) - 0.25, max(p[1] for p in pos.values()) + 0.3])
    return style(fig, height, legend=False)
