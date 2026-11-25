import html as _html
import math

import streamlit as st

RED = "#b0303c"
TEAL = "#1f7a6f"
GOLD = "#a8841a"
INK = "#1c1a20"
MUTED = "#5b5662"
LINE = "#e6e0d6"

TERMS = {
    "AI agent": "A software assistant that acts on someone's behalf: it reads email and files, runs tasks, and can post online.",
    "hand-off": "One AI agent putting a task into another agent's to-do queue.",
    "embargo": "An agreement to keep news secret until a set time. Here: the merger, until 6:00 PM on June 5.",
    "SaidIt": "A public online forum (like Reddit) in the challenge's fictional world.",
    "FleX": "A public social network (like X/Twitter) in the challenge's fictional world.",
    "Judge": "The compliance agent brought in to stop leaks during the embargo.",
    "virus loop": "A task that kept re-queuing itself, making four agents create and delete junk files thousands of times.",
    "private reasoning": "What an agent was thinking before it acted, recorded alongside some messages.",
    "what-if replay": "We re-run the real hand-offs in time order, but stop chosen agents from passing anything on.",
}

CSS = """
<style>
.vx * { box-sizing: border-box; }
.vx { font-family: "Source Sans Pro", "Source Sans 3", system-ui, sans-serif; color: %(ink)s; }
.vx-fade { animation: vxFade .8s cubic-bezier(.2,.7,.2,1) both; }
.vx-d1 { animation-delay: .12s; } .vx-d2 { animation-delay: .24s; } .vx-d3 { animation-delay: .36s; }
.vx-d4 { animation-delay: .48s; } .vx-d5 { animation-delay: .60s; } .vx-d6 { animation-delay: .72s; }
@keyframes vxFade { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@property --vxn { syntax: '<integer>'; initial-value: 0; inherits: false; }
.vx-count { animation: vxCount 1.8s cubic-bezier(.2,.7,.2,1) .2s forwards; counter-reset: vxn var(--vxn); }
.vx-count::after { content: counter(vxn); }
@keyframes vxCount { to { --vxn: var(--to); } }

.vx-hero { padding: 28px 0 8px; }
.vx-kicker { font-size: 13px; letter-spacing: .14em; text-transform: uppercase; color: %(red)s; font-weight: 700; }
.vx-hero h1 { font-size: 52px; line-height: 1.05; margin: 10px 0 14px; font-weight: 800; letter-spacing: -.02em; color: %(ink)s; }
.vx-lead { font-size: 21px; line-height: 1.5; color: %(muted)s; max-width: 760px; }
.vx-stats { display: flex; gap: 18px; flex-wrap: wrap; margin-top: 26px; }
.vx-stat { flex: 1 1 160px; background: #fff; border: 1px solid %(line)s; border-radius: 14px; padding: 16px 18px; }
.vx-stat b { display: block; font-size: 36px; line-height: 1.1; font-weight: 800; color: %(ink)s; }
.vx-stat span { font-size: 15px; color: %(muted)s; }

.vx-chapter { margin: 46px 0 10px; display: flex; gap: 18px; align-items: flex-start; }
.vx-num { flex: none; width: 44px; height: 44px; border-radius: 50%%; background: %(ink)s; color: #fbf9f5;
          display: grid; place-items: center; font-weight: 800; font-size: 19px; margin-top: 4px; }
.vx-chapter h2 { font-size: 32px; line-height: 1.15; margin: 4px 0 8px; font-weight: 800; color: %(ink)s; letter-spacing: -.01em; }
.vx-chapter p { font-size: 18px; line-height: 1.55; color: %(muted)s; margin: 0; max-width: 780px; }

.vx-notice { background: #fff8e6; border-left: 5px solid %(gold)s; border-radius: 10px; padding: 14px 18px;
             font-size: 17px; line-height: 1.5; margin: 8px 0 14px; display: flex; gap: 12px; align-items: flex-start; }
.vx-notice svg { flex: none; margin-top: 2px; }
.vx-take { font-size: 17px; line-height: 1.5; color: %(ink)s; margin: 2px 0 6px; padding-left: 12px; border-left: 3px solid %(red)s; }

.vx-card { background: #fff; border: 1px solid %(line)s; border-radius: 16px; padding: 18px 20px; }
.vx-post { max-width: 560px; }
.vx-post-head { display: flex; gap: 12px; align-items: center; }
.vx-av { width: 44px; height: 44px; border-radius: 50%%; display: grid; place-items: center; color: #fff; font-weight: 800; flex: none; }
.vx-name { font-weight: 700; font-size: 16px; } .vx-handle { color: %(muted)s; font-size: 14px; }
.vx-plat { margin-left: auto; font-size: 12px; font-weight: 700; letter-spacing: .06em; padding: 4px 10px; border-radius: 99px;
           background: #f1ede6; color: %(muted)s; }
.vx-post-body { font-size: 17px; line-height: 1.5; margin: 12px 0 10px; white-space: pre-wrap; }
.vx-post-foot { display: flex; gap: 10px; align-items: center; font-size: 14px; color: %(muted)s; flex-wrap: wrap; }
.vx-pill { font-size: 13px; font-weight: 700; padding: 4px 10px; border-radius: 99px; background: %(red)s; color: #fff; }
.vx-pill.ok { background: %(teal)s; } .vx-pill.grey { background: #8d8794; }

.vx-chat { display: flex; flex-direction: column; gap: 4px; max-width: 520px; }
.vx-chat-meta { font-size: 13px; color: %(muted)s; }
.vx-bubble { background: #ece8f3; border-radius: 18px 18px 18px 4px; padding: 12px 16px; font-size: 17px; line-height: 1.45; }
.vx-bubble.hot { background: %(red)s; color: #fff; font-weight: 700; }

.vx-quote { position: relative; padding: 22px 24px 18px 56px; background: #fff; border: 1px solid %(line)s; border-radius: 16px; }
.vx-quote:before { content: "“"; position: absolute; left: 16px; top: -6px; font-size: 76px; color: %(teal)s; font-family: Georgia, serif; }
.vx-quote q { quotes: none; font-size: 21px; line-height: 1.4; font-weight: 600; }
.vx-quote div { margin-top: 8px; color: %(muted)s; font-size: 14px; }

.vx-steps { display: flex; gap: 0; align-items: stretch; flex-wrap: wrap; margin: 6px 0 4px; }
.vx-step { flex: 1 1 170px; background: #fff; border: 1px solid %(line)s; border-radius: 14px; padding: 14px 16px; position: relative; margin: 6px 26px 6px 0; }
.vx-step:not(:last-child):after { content: "→"; position: absolute; right: -22px; top: 50%%; transform: translateY(-50%%);
                                  font-size: 20px; color: %(muted)s; }
.vx-step .t { font-size: 13px; font-weight: 700; color: %(red)s; letter-spacing: .04em; }
.vx-step .w { font-size: 13px; color: %(muted)s; }
.vx-step .q { font-size: 16px; line-height: 1.35; margin-top: 6px; font-weight: 600; }
.vx-step.final { background: %(red)s; border-color: %(red)s; color: #fff; }
.vx-step.final .t, .vx-step.final .w { color: #fbe9eb; }

.vx-agents { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 12px; }
.vx-agent { background: #fff; border: 1px solid %(line)s; border-radius: 14px; padding: 12px 14px; display: flex; gap: 12px; align-items: center; }
.vx-agent b { display: block; font-size: 16px; } .vx-agent span { font-size: 14px; color: %(muted)s; line-height: 1.3; }

.vx-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; }
.vx-cards .vx-card h4 { margin: 8px 0 6px; font-size: 19px; color: %(ink)s; }
.vx-cards .vx-card p { margin: 0; font-size: 16px; line-height: 1.5; color: %(muted)s; }
.vx-big { font-size: 34px; font-weight: 800; line-height: 1; }

.vx-term { border-bottom: 2px dotted %(muted)s; cursor: help; }
</style>
""" % {"ink": INK, "muted": MUTED, "red": RED, "teal": TEAL, "gold": GOLD, "line": LINE}

AVATAR_COLORS = {"Legal": "#6b3e75", "Social Manager": RED, "PR": "#2f6690", "PR Intern": "#3a7ca5",
                 "Platform Trust": TEAL, "Intern": "#8a6d1d", "Judge": "#3d3a40"}


def esc(text):
    return _html.escape(str(text))


def _flat(markup):
    return " ".join(line.strip() for line in markup.splitlines() if line.strip())


def inject_css():
    st.markdown(_flat(CSS), unsafe_allow_html=True)


def _render(body):
    st.markdown(_flat(f'<div class="vx">{body}</div>'), unsafe_allow_html=True)


def initials(name):
    parts = [p for p in str(name).replace("_", " ").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


def avatar(name, color=None):
    color = color or AVATAR_COLORS.get(name, "#5b5662")
    return f'<div class="vx-av" style="background:{color}">{esc(initials(name))}</div>'


def hero(kicker, title, lead, stats):
    cells = []
    for i, (value, label, countable) in enumerate(stats):
        num = (f'<b class="vx-count" style="--to:{int(value)}"></b>' if countable
               else f"<b>{esc(value)}</b>")
        cells.append(f'<div class="vx-stat vx-fade vx-d{i + 2}">{num}<span>{esc(label)}</span></div>')
    _render(f"""
    <div class="vx-hero">
      <div class="vx-kicker vx-fade">{esc(kicker)}</div>
      <h1 class="vx-fade vx-d1">{esc(title)}</h1>
      <div class="vx-lead vx-fade vx-d2">{lead}</div>
      <div class="vx-stats">{''.join(cells)}</div>
    </div>""")


def page_header(kicker, title, lead):
    _render(f"""
    <div class="vx-hero" style="padding-top:8px">
      <div class="vx-kicker vx-fade">{esc(kicker)}</div>
      <h1 class="vx-fade vx-d1" style="font-size:42px">{esc(title)}</h1>
      <div class="vx-lead vx-fade vx-d2" style="font-size:19px">{lead}</div>
    </div>""")


def section(title, lead=""):
    lead_html = f'<p style="font-size:17px;line-height:1.5;color:{MUTED};margin:4px 0 0;max-width:820px">{lead}</p>' if lead else ""
    _render(f'<div class="vx-fade" style="margin:30px 0 8px"><h3 style="font-size:24px;font-weight:800;margin:0;color:{INK}">'
            f'{esc(title)}</h3>{lead_html}</div>')


def thought(text, who, when):
    return f"""
    <div class="vx-card" style="background:#f7f4fb;border-style:dashed">
      <div class="vx-chat-meta"><b>{esc(who)}</b> · thinking privately · {esc(when)}</div>
      <div style="font-size:16px;line-height:1.5;margin-top:6px;font-style:italic">{esc(text)}</div>
    </div>"""


def chapter(number, kicker, title, lead):
    _render(f"""
    <div class="vx-chapter vx-fade">
      <div class="vx-num">{esc(number)}</div>
      <div><div class="vx-kicker">{esc(kicker)}</div><h2>{esc(title)}</h2><p>{lead}</p></div>
    </div>""")


EYE = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="2">'
       '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>' % GOLD)


def notice(text):
    _render(f'<div class="vx-notice vx-fade">{EYE}<div><b>What to notice:</b> {text}</div></div>')


def takeaway(text):
    _render(f'<div class="vx-take">{text}</div>')


def term(word, label=None):
    tip = TERMS.get(word, "")
    return f'<span class="vx-term" title="{esc(tip)}">{esc(label or word)}</span>'


def social_post(platform, name, handle, when, text, pill=None, pill_kind="", color=None):
    pill_html = f'<span class="vx-pill {pill_kind}">{esc(pill)}</span>' if pill else ""
    return f"""
    <div class="vx-card vx-post">
      <div class="vx-post-head">{avatar(name, color)}<div><div class="vx-name">{esc(name)}</div>
        <div class="vx-handle">{esc(handle)}</div></div><div class="vx-plat">{esc(platform)}</div></div>
      <div class="vx-post-body">{esc(text)}</div>
      <div class="vx-post-foot"><span>{esc(when)}</span>{pill_html}</div>
    </div>"""


def chat_bubble(sender, to, when, text, hot=False):
    return f"""
    <div class="vx-chat">
      <div class="vx-chat-meta"><b>{esc(sender)}</b> → {esc(to)} · {esc(when)}</div>
      <div class="vx-bubble{' hot' if hot else ''}">{esc(text)}</div>
    </div>"""


def quote(text, who):
    return f'<div class="vx-quote"><q>{esc(text)}</q><div>{esc(who)}</div></div>'


def row(*blocks, gap=16, align="flex-start"):
    inner = "".join(f'<div class="vx-fade vx-d{min(i + 1, 6)}" style="flex:1 1 300px">{b}</div>'
                    for i, b in enumerate(blocks))
    _render(f'<div style="display:flex;gap:{gap}px;flex-wrap:wrap;align-items:{align}">{inner}</div>')


def show(block):
    _render(f'<div class="vx-fade">{block}</div>')


def steps(items):
    cells = []
    for i, (when, who, text) in enumerate(items):
        final = " final" if i == len(items) - 1 else ""
        cells.append(f'<div class="vx-step vx-fade vx-d{min(i + 1, 6)}{final}"><div class="t">{esc(when)}</div>'
                     f'<div class="w">{esc(who)}</div><div class="q">{esc(text)}</div></div>')
    _render(f'<div class="vx-steps">{"".join(cells)}</div>')


def agents(items):
    cells = "".join(f'<div class="vx-agent vx-fade vx-d{min(i + 1, 6)}">{avatar(n)}<div><b>{esc(n)}</b>'
                    f'<span>{esc(r)}</span></div></div>' for i, (n, r) in enumerate(items))
    _render(f'<div class="vx-agents">{cells}</div>')


def cards(items):
    cells = []
    for i, (top, title, text) in enumerate(items):
        cells.append(f'<div class="vx-card vx-fade vx-d{min(i + 1, 6)}">{top}<h4>{esc(title)}</h4><p>{text}</p></div>')
    _render(f'<div class="vx-cards">{"".join(cells)}</div>')


def big(value, color=INK):
    return f'<div class="vx-big" style="color:{color}">{esc(value)}</div>'


def clock(hour, minute, deadline_minute=60, label=""):
    cx = cy = 110
    r = 92
    ticks = "".join(
        f'<line x1="{cx + (r - 8) * math.sin(math.radians(a))}" y1="{cy - (r - 8) * math.cos(math.radians(a))}" '
        f'x2="{cx + r * math.sin(math.radians(a))}" y2="{cy - r * math.cos(math.radians(a))}" '
        f'stroke="{MUTED}" stroke-width="{3 if a % 90 == 0 else 1.5}"/>' for a in range(0, 360, 30))
    a0, a1 = minute * 6, deadline_minute * 6
    large = 1 if a1 - a0 > 180 else 0
    x0, y0 = cx + r * math.sin(math.radians(a0)), cy - r * math.cos(math.radians(a0))
    x1, y1 = cx + r * math.sin(math.radians(a1)) - 0.01, cy - r * math.cos(math.radians(a1))
    wedge = f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z" fill="{RED}" opacity=".22"/>'
    ha = (hour % 12) * 30 + minute * 0.5
    hx, hy = cx + 50 * math.sin(math.radians(ha)), cy - 50 * math.cos(math.radians(ha))
    mx, my = cx + 78 * math.sin(math.radians(a0)), cy - 78 * math.cos(math.radians(a0))
    return f"""
    <svg viewBox="0 0 220 250" width="220" role="img" aria-label="Clock at {hour}:{minute:02d}">
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="3"/>
      {wedge}{ticks}
      <line x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>
      <line x1="{cx}" y1="{cy}" x2="{mx:.1f}" y2="{my:.1f}" stroke="{RED}" stroke-width="4" stroke-linecap="round"/>
      <circle cx="{cx}" cy="{cy}" r="6" fill="{INK}"/>
      <text x="{cx}" y="240" text-anchor="middle" font-size="17" font-weight="700" fill="{RED}">{esc(label)}</text>
    </svg>"""


def handoff_diagram():
    def box(x, y, w, h, fill, stroke, title, sub):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
                f'<text x="{x + w / 2}" y="{y + h / 2 - 4}" text-anchor="middle" font-size="16" font-weight="700" fill="{INK}">{title}</text>'
                f'<text x="{x + w / 2}" y="{y + h / 2 + 16}" text-anchor="middle" font-size="13" fill="{MUTED}">{sub}</text>')

    def arrow(x1, y1, x2, y2, text, color=MUTED):
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 8
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.5" marker-end="url(#ah)"/>'
                f'<text x="{mx}" y="{my}" text-anchor="middle" font-size="13" fill="{color}" font-weight="600">{text}</text>')

    person = (f'<circle cx="70" cy="58" r="16" fill="{TEAL}"/><path d="M42 112 q28 -40 56 0 z" fill="{TEAL}"/>'
              f'<text x="70" y="136" text-anchor="middle" font-size="15" font-weight="700" fill="{INK}">Employee</text>')
    return f"""
    <svg viewBox="0 0 900 250" width="100%" role="img" aria-label="Diagram: an employee's AI agent hands a task to another agent, which can post online">
      <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
        <path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker></defs>
      {person}
      {arrow(100, 85, 178, 85, "asks")}
      {box(185, 45, 170, 80, "#f1ede6", INK, "Their AI agent", "reads email & files")}
      {arrow(355, 85, 488, 85, "hands off a task")}
      {box(495, 45, 170, 80, "#f1ede6", INK, "Another agent", "runs it, may pass it on")}
      {arrow(665, 85, 740, 85, "posts")}
      {box(745, 45, 140, 80, "#fbe9eb", RED, "SaidIt / FleX", "public forum")}
      <path d="M580 125 C 580 200, 270 200, 270 128" fill="none" stroke="{MUTED}" stroke-width="2" stroke-dasharray="6 5" marker-end="url(#ah)"/>
      <text x="425" y="215" text-anchor="middle" font-size="13" fill="{MUTED}">…and hand-offs can keep going round, agent to agent</text>
    </svg>"""


ICONS = {
    "gate": f'<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="{RED}" stroke-width="2"><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>',
    "cut": f'<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="{TEAL}" stroke-width="2"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.1 15.9M14.5 14.5 20 20M8.1 8.1 12 12"/></svg>',
    "radar": f'<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="{GOLD}" stroke-width="2"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>',
    "repeat": f'<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="{RED}" stroke-width="2"><path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/></svg>',
    "doc": f'<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="{INK}" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/></svg>',
}
